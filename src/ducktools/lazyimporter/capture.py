import builtins
import importlib
import sys

from . import ModuleImport, MultiFromImport, extend_imports


class CaptureError(Exception):
    """
    Error for capture speciific details
    """


# A replaced __import__ will still populate module globals (but not sys.modules)
# After the fake imports are done, these will be used to remove the names from the module
class _ImportPlaceholder:
    __slots__ = ("attrib_name", "placeholder_parent")

    def __init__(self, attrib_name=None, parent=None):
        self.attrib_name = attrib_name
        self.placeholder_parent = parent

    def __repr__(self):
        return f"{type(self).__name__}(attrib_name={self.attrib_name!r}, parent={self.placeholder_parent!r})"

    def __getattr__(self, item):
        # 'as' imports will be created from attribute access
        # store the parent so we can work backwards to the original import
        return _ImportPlaceholder(attrib_name=item, parent=self)


# Temporary importers needed for tracking back to assigned names
class CapturedModuleImport:
    __slots__ = ("module_name", "placeholder")

    def __init__(self, module_name, placeholder):
        self.module_name = module_name
        self.placeholder = placeholder

    def __eq__(self, other):
        if type(self) is type(other):
            return (
                self.module_name == other.module_name
                and self.placeholder == other.placeholder
            )
        return NotImplemented

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"module_name={self.module_name!r}, "
            f"placeholder={self.placeholder!r}"
            f")"
        )

    @property
    def final_element(self):
        return self.module_name.split(".")[-1]


class CapturedFromImport:
    __slots__ = ("module_name", "attrib_name", "placeholder")

    def __init__(self, module_name, attrib_name, placeholder):
        self.module_name = module_name
        self.attrib_name = attrib_name
        self.placeholder = placeholder

    def __eq__(self, other):
        if type(self) is type(other):
            return (
                self.module_name == other.module_name
                and self.placeholder == other.placeholder
                and self.attrib_name == other.attrib_name
            )
        return NotImplemented

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"module_name={self.module_name!r}, "
            f"attrib_name={self.attrib_name!r}, "
            f"placeholder={self.placeholder!r}"
            f")"
        )


def make_capturing_import(captured_imports, globs, old_import):
    def _capturing_import(name, globals=None, locals=None, fromlist=(), level=0):
        # Something else tried to import - redirect to regular machinery
        if globals is not globs:
            return old_import(name, globals, locals, fromlist, level)

        if fromlist and "*" in fromlist:
            raise CaptureError("Lazy importers cannot capture '*' imports.")

        # Make a unique placeholder object
        placeholder = _ImportPlaceholder(attrib_name=name.split(".")[0])

        leading_dots = "." * level
        module_name = f"{leading_dots}{name}"

        if fromlist:
            captured_imports.extend(
                [
                    CapturedFromImport(
                        module_name=module_name,
                        attrib_name=obj_name,
                        placeholder=placeholder,
                    )
                    for obj_name in fromlist
                ]
            )
        else:
            captured_imports.append(
                CapturedModuleImport(
                    module_name=module_name,
                    placeholder=placeholder,
                )
            )

        return placeholder
    return _capturing_import


class capture_imports:
    def __init__(self, importer):
        try:
            sys._getframe  # noqa
        except AttributeError:
            raise CaptureError("Import capture requires sys._getframe")

        self.importer = importer

        self.captured_imports = []

        # Place to store current and previous __import__ functions
        self.import_func = None
        self.previous_import_func = None

        # Need the globals to check imports are for the appropriate module
        # and for relative imports
        self.globs = self.importer._globals
        if self.globs is None:
            raise CaptureError("Importer must have globals to capture import statements")

    def __enter__(self):
        if self.previous_import_func or self.import_func:
            raise CaptureError("_CaptureContext is not reusable")

        # Store the old import function, create the new one and replace it
        self.previous_import_func = builtins.__import__

        self.import_func = make_capturing_import(
            self.captured_imports,
            self.globs,
            self.previous_import_func,
        )

        builtins.__import__ = self.import_func

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore import state
        if builtins.__import__ is not self.import_func:
            # If the importer has been changed while in use restore to a default
            # importlib.__import__
            builtins.__import__ = importlib.__import__
            raise CaptureError(
                "Importer was replaced while in import block. "
                "Restored to 'importlib.__import__'."
            )

        builtins.__import__ = self.previous_import_func

        # Trace names that are now in globals back to the actual import
        placeholders = {}
        for importer in self.captured_imports:
            importer_placeholders = placeholders.get(importer.placeholder, {})
            if isinstance(importer, CapturedModuleImport):
                importer_placeholders[importer.final_element] = importer
            else:
                importer_placeholders[importer.attrib_name] = importer

            placeholders[importer.placeholder] = importer_placeholders

        final_imports = []  # List of ModuleImport and MultiFromImport
        from_imports = {}  # dict of module_name: [(attrib, asname), ..]

        # Imports within class/function bodies can appear in locals
        # Retrace and collect the importers
        locs = dict(sys._getframe(1).f_locals)

        # If imports are done at module level, globs and locs will be equal
        if locs != self.globs:
            spaces = [locs, self.globs]
        else:
            spaces = [self.globs]

        for ns in spaces:
            # Copy as the original may be mutated.
            for key, value in ns.copy().items():
                if isinstance(value, _ImportPlaceholder):
                    attrib_name = value.attrib_name
                    while parent := value.placeholder_parent:
                        value = parent

                    try:
                        importer_map = placeholders[value]
                    except KeyError:
                        continue
                    else:
                        if attrib_name:
                            capture = importer_map[attrib_name]
                            if isinstance(capture, CapturedModuleImport):
                                importer = ModuleImport(
                                    capture.module_name,
                                    asname=key,
                                )
                                final_imports.append(importer)
                            else:
                                try:
                                    pairs = from_imports[capture.module_name]
                                except KeyError:
                                    pairs = []
                                    from_imports[capture.module_name] = pairs

                                pairs.append((attrib_name, key))

                        try:
                            del ns[key]
                        except TypeError:
                            # Can't delete via local namespace proxy - set to None
                            ns[key] = None

        final_imports.extend([MultiFromImport(k, v) for k, v in from_imports.items()])

        # Add these imports to the importer
        extend_imports(self.importer, final_imports)
