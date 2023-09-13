"""
Hook into the import mechanism and sneakily translate our modules before
python gets there.

Copied mostly from prefab_classes_hook but slightly more relaxed
on import performance
"""
import sys

from importlib.machinery import PathFinder, SourceFileLoader

from . import LAZY_IMPORT_MAGIC_BYTES

__all__ = ["lazy_hook", "insert_lazy_hook", "remove_lazy_hook"]

# For bootstrapping reasons we need to ignore stdlib modules and
# modules from the lazy importer itself.
IGNORE_MODULES = frozenset(sys.stdlib_module_names) | {"lazy_importer"}

LAZY_IMPORT_COUNTER = 0


class LazyImportError(ImportError):
    pass


# noinspection PyMethodOverriding,PyArgumentList
class LazyHackLoader(SourceFileLoader):
    def source_to_code(self, data, path, *, _optimize=-1):
        from .ast_hack import hack_ast
        from importlib.util import decode_source
        src = decode_source(data)
        prefab_src = hack_ast(src)

        code = super().source_to_code(prefab_src, path, _optimize=_optimize)

        return code

    @staticmethod
    def make_pyc_hash(source_bytes):
        # Modify the data given to the hash with extra data
        hash_input_bytes = b"".join([LAZY_IMPORT_MAGIC_BYTES, source_bytes])
        try:
            # Using internals
            from _imp import source_hash
            from importlib._bootstrap_external import _RAW_MAGIC_NUMBER  # noqa

            return source_hash(_RAW_MAGIC_NUMBER, hash_input_bytes)
        except ImportError:
            # Using public methods
            from importlib.util import source_hash

            return source_hash(hash_input_bytes)

    # noinspection PyUnresolvedReferences,PyProtectedMember
    def get_code(self, fullname):
        """
        Modified from SourceLoader.get_code method in _bootstrap_external
        Need the whole function in order to modify the invalidation method.

        For compilation to work correctly this Loader must invalidate .pyc files
        compiled by python's own loader and vice versa. Updates to python and
        updates to the generator must also invalidate .pyc files.

        This works by adding LAZY_IMPORT_MAGIC_BYTES to the data before the hash is
        generated.

        Concrete implementation of InspectLoader.get_code.
        Reading of bytecode requires path_stats to be implemented. To write
        bytecode, set_data must also be implemented.
        """
        # These imports are all needed just for this function.
        # Unlike most of the other imports I don't know if there's a "right" place
        # to get these from.
        from importlib._bootstrap_external import (
            cache_from_source,
            _classify_pyc,
            _validate_hash_pyc,
            _compile_bytecode,
            _code_to_hash_pyc,
        )

        source_path = self.get_filename(fullname)
        source_bytes = None
        source_hash_data = None
        check_source = True
        try:
            bytecode_path = cache_from_source(source_path)
        except NotImplementedError:
            bytecode_path = None
        else:
            try:
                data = self.get_data(bytecode_path)
            except OSError:
                pass
            else:
                exc_details = {
                    "name": fullname,
                    "path": bytecode_path,
                }
                try:
                    flags = _classify_pyc(data, fullname, exc_details)
                    bytes_data = memoryview(data)[16:]
                    used_hash = flags & 0b1 != 0
                    if used_hash:
                        source_bytes = self.get_data(source_path)
                        source_hash_data = self.make_pyc_hash(source_bytes)
                        _validate_hash_pyc(
                            data, source_hash_data, fullname, exc_details
                        )
                    else:
                        raise ImportError(
                            "Timestamp based .pyc validation is invalid for this loader"
                        )
                except (ImportError, EOFError):
                    pass
                else:
                    return _compile_bytecode(
                        bytes_data,
                        name=fullname,
                        bytecode_path=bytecode_path,
                        source_path=source_path,
                    )

        if source_bytes is None:
            source_bytes = self.get_data(source_path)
        code_object = self.source_to_code(source_bytes, source_path)
        # _bootstrap._verbose_message('code object from {}', source_path)
        if not sys.dont_write_bytecode and bytecode_path is not None:

            if source_hash_data is None:
                source_hash_data = self.make_pyc_hash(source_bytes)

            data = _code_to_hash_pyc(code_object, source_hash_data, check_source)

            try:
                self._cache_bytecode(source_path, bytecode_path, data)
            except NotImplementedError:
                pass
        return code_object


class LazyFinder(PathFinder):
    @classmethod
    def find_spec(cls, fullname, path=None, target=None):
        spec = PathFinder.find_spec(fullname, path, target)

        # Don't attempt to handle modules without spec
        if not spec:
            return None
        elif spec.name.partition(".")[0] in IGNORE_MODULES:
            return None

        origin = getattr(spec, "origin", None)
        if origin:
            new_loader = LazyHackLoader(spec.loader.name, spec.loader.path)
            spec.loader = new_loader
            return spec
        return None


def insert_lazy_hook():
    """
    Add the lazy importer hook to sys.meta_path
    """
    global LAZY_IMPORT_COUNTER
    if LAZY_IMPORT_COUNTER is None:
        raise LazyImportError("Cannot insert or remove hook while suspended.")

    LAZY_IMPORT_COUNTER += 1
    # Don't insert the prefab finder if it is already in the list
    if LazyFinder in sys.meta_path:
        return

    index = 0
    for i, finder in enumerate(sys.meta_path):
        finder = finder if type(finder) is type else type(finder)
        if issubclass(finder, PathFinder):
            index = i
            break

    # Make PrefabFinder the first importer before other PathFinders
    sys.meta_path.insert(index, LazyFinder)


def remove_lazy_hook():
    """
    Remove the lazy importer import hook from sys.meta_path
    """
    global LAZY_IMPORT_COUNTER
    if LAZY_IMPORT_COUNTER is None:
        raise LazyImportError("Cannot insert or remove hook while it is suspended.")

    LAZY_IMPORT_COUNTER -= 1
    if LAZY_IMPORT_COUNTER <= 0:
        try:
            sys.meta_path.remove(LazyFinder)
        except ValueError:  # PrefabFinder not in the list
            pass


class _suspend_lazy_hook:
    """
    Tool to temporarily suspend the hook
    """
    def __init__(self):
        self.old_meta_path = []
        self.lazy_counter = None

    def __enter__(self):
        global LAZY_IMPORT_COUNTER

        # Set the counter to None to prevent the importer
        # from being inserted while suspended
        self.lazy_counter = LAZY_IMPORT_COUNTER
        LAZY_IMPORT_COUNTER = None

        # Copy meta path to restore later
        self.old_meta_path = sys.meta_path.copy()
        try:
            sys.meta_path.remove(LazyFinder)
        except ValueError:
            pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore meta path with import hook
        sys.meta_path = self.old_meta_path

        # Restore import counter
        global LAZY_IMPORT_COUNTER
        LAZY_IMPORT_COUNTER = self.lazy_counter


class lazy_hook:
    """
    Context manager to insert and clean up the prefab compilation import hook.

    This function should be used before importing any modules with lazy imports
    you wish to be compiled. These modules will then be converted to .pyc files
    with a special identifier so they will only be re-converted if a change is
    made to the .py file, if there is a new version of lazy_importer or if
    there is a new python magic number.

    usage::
        with lazy_hook():
            import my_lazy_module
    """

    def __enter__(self):
        insert_lazy_hook()

    def __exit__(self, exc_type, exc_val, exc_tb):
        remove_lazy_hook()
