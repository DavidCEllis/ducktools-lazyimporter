# MIT License
# Copyright (c) 2024-2025 David C Ellis
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import builtins
import sys

from . import ModuleImport, MultiFromImport, extend_imports, get_module_funcs


class CaptureError(Exception):
    """
    Error for capture specific details
    """


# A replaced __import__ will still populate module globals (but not sys.modules)
# After the fake imports are done, these will be used to remove the names from the module
# This intentionally does **not** define an '__eq__' or '__hash__'
# Two placeholders are only identical if they are the same object as otherwise it's
# not possible to trace imports back correctly.
class _ImportPlaceholder:
    __slots__ = ("attrib_name", "placeholder_parent", "capturer")

    def __init__(self, capturer, attrib_name=None, parent=None):
        self.capturer = capturer
        self.attrib_name = attrib_name
        self.placeholder_parent = parent

    def __repr__(self):  # pragma: nocover
        return (
            f"{self.__class__.__name__}("
            f"capturer={self.capturer!r}, "
            f"attrib_name={self.attrib_name!r}, "
            f"parent={self.placeholder_parent!r}"
            f")"
        )

    def __getattr__(self, item):
        # 'as' imports will be created from attribute access
        # store the parent so we can work backwards to the original import
        return _ImportPlaceholder(capturer=self.capturer, attrib_name=item, parent=self)


# Temporary importers needed for tracking back to assigned names
class CapturedModuleImport:
    __slots__ = ("module_name", "placeholder")

    def __init__(self, module_name, placeholder):
        self.module_name = module_name
        self.placeholder = placeholder

    def __repr__(self):  # pragma: nocover
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

    def __repr__(self):  # pragma: nocover
        return (
            f"{self.__class__.__name__}("
            f"module_name={self.module_name!r}, "
            f"attrib_name={self.attrib_name!r}, "
            f"placeholder={self.placeholder!r}"
            f")"
        )


class capture_imports:
    def __init__(self, importer, auto_export=True):
        """
        Capture import statements executed within a block using this as a context manager

        Any `import <module> as <name>` or `from <module> import <attribute> as <name>`
        calls will be intercepted and assigned as lazy imports to the importer provided.

        **This only works at module level!**

        :param importer: LazyImporter instance
        :param auto_export: generate __getattr__ and __dir__ functions and add them to globals
                            in order to make the attributes available to import on the module.
        """
        self.importer = importer
        self.auto_export = auto_export

        # Global and locals checks
        # This capture function only works at module level, so locals should be globals
        # And they should match the level of the lazy importer
        try:
            sys._getframe  # noqa
        except AttributeError:
            raise CaptureError("Import capture requires sys._getframe")

        self.globs = None
        self.captured_imports = []

        # Place to store current and previous __import__ functions
        self.import_func = None
        self.previous_import_func = None

    def _make_capturing_import(self):
        def _capturing_import(name, globals=None, locals=None, fromlist=(), level=0):
            # Something else tried to import - redirect to regular machinery
            if globals is not self.globs or globals != locals:
                return self.previous_import_func(name, globals, locals, fromlist, level)

            if fromlist and "*" in fromlist:
                raise CaptureError("Lazy importers cannot capture '*' imports.")

            # Make a unique placeholder object
            placeholder = _ImportPlaceholder(
                capturer=self,
                attrib_name=name.split(".")[0],
            )

            leading_dots = "." * level
            module_name = f"{leading_dots}{name}"

            captured_imports = self.captured_imports
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

    def __enter__(self):
        if self.previous_import_func or self.import_func:
            raise CaptureError("_CaptureContext is not reusable")

        # Only capture the frame when entering, this makes it possible to wrap
        # capture_imports.
        frame = sys._getframe(1)
        globs = frame.f_globals
        locs = frame.f_locals

        if globs is not locs:
            raise CaptureError("Import capture must be done at module level")

        if globs is not self.importer._globals:
            raise CaptureError("LazyImporter globals must match frame globals for capture_imports call")

        if self.auto_export and (globs.get("__getattr__") or globs.get("__dir__")):
            raise CaptureError(
                "auto_export is not supported if __getattr__ or __dir__ is already defined on the module."
            )

        self.globs = globs

        # Store the old import function, create the new one and replace it
        self.previous_import_func = builtins.__import__

        self.import_func = self._make_capturing_import()

        builtins.__import__ = self.import_func

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore import state
        if builtins.__import__ is not self.import_func:
            # If the importer has been changed while in use restore it anyway
            # But error out
            builtins.__import__ = self.previous_import_func
            raise CaptureError(
                "Importer was replaced while in import block. "
                "Restored to state when block entered."
            )

        builtins.__import__ = self.previous_import_func

        # Trace names that are now in globals back to the actual import

        # `captured_imports` contains a list of CapturedImport objects containing
        # the import module and attribute names alongside a placeholder that was returned
        # by the original import
        # The globals namespace now contains the final placeholders that were assigned.
        # These may not be the original placeholders returned as 'from' imports for example
        # will have accessed attributes from the placeholders.
        # The logic is to trace the placeholder back to the parent, and then match that
        # with the placeholders contained by the CapturedImports

        # First create a mapping from placeholder instances to attribute names, to importers
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

        # Create a set of imports - if there is an importer that is not used
        # After all are matched then raise an exception
        importer_set = set(self.captured_imports)

        # Copy as the original may be mutated.
        # `key` in this case will be the name the attribute was assigned
        for key, value in self.globs.copy().items():
            if isinstance(value, _ImportPlaceholder) and value.capturer is self:
                # Store the initial attribute name and seek upwards through
                # parent placeholders to try to find the original placeholder
                attrib_name = value.attrib_name
                while parent := value.placeholder_parent:
                    value = parent

                # Get the {attribute name: importer, ...} mappings
                importer_map = placeholders[value]

                if attrib_name:
                    # Retrieve the captured import statement from the mapping
                    try:
                        capture = importer_map[attrib_name]
                    except KeyError:
                        # Search the capture map to see if this is a submodule import
                        for cap_imp in importer_map.values():
                            if cap_imp.module_name.split(".")[0] == attrib_name:
                                asname = cap_imp.module_name.split(".")[-1]
                                raise CaptureError(
                                    f"Submodule import `import {cap_imp.module_name}` requires assigned name: "
                                    f"eg `import {cap_imp.module_name} as {asname}`"
                                )

                        # I don't know of a case where this can currently happen
                        # But this is still an error so raise here
                        raise  # pragma: nocover

                    # Remove used importers from the set
                    importer_set.discard(capture)

                    # Convert it to a regular ModuleImport or store it to make
                    # a MultiFromImport at the end.
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

                    del self.globs[key]

        # importer_set should be empty
        # If it was not then there were import statements that did not have
        # a matching name in globals.

        if importer_set:
            missing_module_imports = []
            missing_from_imports = []
            for imp in importer_set:
                if isinstance(imp, CapturedModuleImport):
                    missing_module_imports.append(repr(imp.module_name))
                else:
                    missing_from_imports.append(repr(imp.attrib_name))

            if missing_module_imports:
                err_list = ", ".join(missing_module_imports)
                raise CaptureError(
                    f"Unused module import(s) {err_list} not matched to a name in globals. "
                    f"Possible duplicates or unaliased submodule import before module import."
                )
            else:
                err_list = ", ".join(missing_from_imports)
                raise CaptureError(f"Imports for name(s) {err_list} found, but unused.")

        final_imports.extend([MultiFromImport(k, v) for k, v in from_imports.items()])

        # Add these imports to the importer
        extend_imports(self.importer, final_imports)

        # Export to globals
        if self.auto_export:
            module_name = self.globs["__name__"]
            getattr_func, dir_func = get_module_funcs(self.importer, module_name=module_name)
            self.globs["__getattr__"] = getattr_func
            self.globs["__dir__"] = dir_func
