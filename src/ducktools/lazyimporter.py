# MIT License
# Copyright (c) 2023 David C Ellis
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

"""
Tools to make a lazy importer object that can be set up to import
when first accessed.
"""
import abc
import sys

__version__ = "v0.2.2"
__all__ = [
    "LazyImporter",
    "ModuleImport",
    "FromImport",
    "MultiFromImport",
    "TryExceptImport",
    "TryExceptFromImport",
    "ImportBase",
    "get_importer_state",
    "get_module_funcs",
]


class ImportBase(abc.ABC):
    module_name: str

    @property
    def module_name_noprefix(self):
        return self.module_name.lstrip(".")

    @property
    def import_level(self):
        level = 0
        for char in self.module_name:
            if char != ".":
                break
            level += 1
        return level

    @property
    def module_basename(self):
        """
        Get the first part of a module import name.
        eg: 'importlib' from 'importlib.util'

        :return: name of base module
        :rtype: str
        """
        return self.module_name_noprefix.split(".")[0]

    @property
    def submodule_names(self):
        """
        Get a list of all submodule names in order.
        eg: ['util'] from 'importlib.util'
        :return: List of submodule names.
        :rtype: list[str]
        """
        return self.module_name_noprefix.split(".")[1:]

    @abc.abstractmethod
    def do_import(self, globs=None):
        """
        Perform the imports defined and return a dictionary.

        :return: dict of {name: imported_object, ...} for all names
        :rtype: dict[str, typing.Any]
        """


class ModuleImport(ImportBase):
    module_name: str
    asname: "None | str"

    def __init__(self, module_name, asname=None):
        """
        Equivalent to `import <module_name> [as <asname>]`
        when provided to a LazyImporter.

        :param module_name: Name of the module to import eg: "dataclasses"
        :type module_name: str
        :param asname: Optional name to use as the attribute name for the module
        :type asname: str
        """
        self.module_name = module_name
        self.asname = asname

        if self.import_level > 0 and asname is None:
            raise ValueError(
                "Relative imports are not allowed without an assigned name."
            )

        if self.asname is not None and not asname.isidentifier():
            raise ValueError(f"{self.asname!r} is not a valid Python identifier.")

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"module_name={self.module_name!r}, "
            f"asname={self.asname!r}"
            f")"
        )

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            return (self.module_name, self.asname) == (other.module_name, other.asname)
        return NotImplemented

    def do_import(self, globs=None):
        mod = __import__(
            self.module_name_noprefix,
            globals=globs,
            level=self.import_level,
        )

        if self.asname:  # return the submodule
            submod_used = [self.module_basename]
            for submod in self.submodule_names:
                submod_used.append(submod)
                mod = getattr(mod, submod)

        if self.asname:
            return {self.asname: mod}
        else:  # pragma: no cover
            return {self.module_basename: mod}


class FromImport(ImportBase):
    module_name: str
    attrib_name: str
    asname: str

    def __init__(self, module_name, attrib_name, asname=None):
        """
        Equivalent to `from <module_name> import <attrib_name> [as <asname>]`
        when provided to a LazyImporter

        :param module_name: name of the module containing the objects to import
        :type module_name: str
        :param attrib_name: name of the attribute to import
        :type attrib_name: str
        :param asname: name to use as the name of the attribute on the lazy importer
        :type asname: str | None
        """
        self.module_name = module_name
        self.attrib_name = attrib_name
        self.asname = asname if asname is not None else attrib_name

        if not self.asname.isidentifier():
            raise ValueError(f"{self.asname!r} is not a valid Python identifier.")

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"module_name={self.module_name!r}, "
            f"attrib_name={self.attrib_name!r}, "
            f"asname={self.asname!r}"
            f")"
        )

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            return (self.module_name, self.attrib_name, self.asname) == (
                other.module_name,
                self.attrib_name,
                other.asname,
            )
        return NotImplemented

    def do_import(self, globs=None):
        # Perform the import
        mod = __import__(
            self.module_name_noprefix,
            globals=globs,
            fromlist=[self.attrib_name],
            level=self.import_level,
        )

        return {self.asname: getattr(mod, self.attrib_name)}


class MultiFromImport(ImportBase):
    module_name: str
    attrib_names: "list[str | tuple[str, str]]"

    def __init__(self, module_name, attrib_names):
        """
        Equivalent to `from <module_name> import <attrib_names[0]>, <attrib_names[1]>, ...`
        when provided to a LazyImporter

        Optional 'asname' for attributes if given as a tuple.

        :param module_name: Name of the module to import from
        :type module_name: str
        :param attrib_names: List of attributes or (attribute, asname) pairs.
        :type attrib_names: list[str | tuple[str, str]]
        """
        self.module_name = module_name
        self.attrib_names = attrib_names

        for name in self.asnames:
            if not name.isidentifier():
                raise ValueError(f"{name!r} is not a valid Python identifier.")

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"module_name={self.module_name!r}, "
            f"attrib_names={self.attrib_names!r})"
        )

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            return (self.module_name, self.attrib_names) == (
                other.module_name,
                other.attrib_names,
            )
        return NotImplemented

    @property
    def asnames(self):
        """
        Get a list of all the names that will be assigned by this importer

        :return: list of 'asname' names to give as 'dir' for LazyImporter bindings
        :rtype: list[str]
        """
        names = []
        for item in self.attrib_names:
            if isinstance(item, str):
                names.append(item)
            else:
                names.append(item[1])

        return names

    def do_import(self, globs=None):
        from_imports = {}

        # Perform the import
        mod = __import__(
            self.module_name_noprefix,
            globals=globs,
            fromlist=self.asnames,
            level=self.import_level,
        )

        for name in self.attrib_names:
            if isinstance(name, str):
                from_imports[name] = getattr(mod, name)
            else:
                from_imports[name[1]] = getattr(mod, name[0])

        return from_imports


class TryExceptImport(ImportBase):
    module_name: str
    except_module: str
    asname: str

    def __init__(self, module_name, except_module, asname):
        """
        Equivalent to:

        .. code-block:: python

            try:
                import <module_name> as <asname>
            except ImportError:
                import <except_module> as <asname>

        Inside a LazyImporter

        :param module_name: Name of the 'try' module
        :type module_name: str
        :param except_module: Name of the module to import in the case
                              that the 'try' module fails
        :type except_module: str
        :param asname: Name to use for either on successful import
        :type asname: str
        """
        self.module_name = module_name
        self.except_module = except_module
        self.asname = asname

        if not self.asname.isidentifier():
            raise ValueError(f"{self.asname!r} is not a valid Python identifier.")

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"module_name={self.module_name!r}, "
            f"except_module={self.except_module!r}, "
            f"asname={self.asname!r}"
            f")"
        )

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            return (self.module_name, self.except_module, self.asname) == (
                other.module_name,
                other.except_module,
                other.asname,
            )
        return NotImplemented

    @property
    def except_import_level(self):
        level = 0
        for char in self.except_module:
            if char != ".":
                break
            level += 1
        return level

    @property
    def except_module_noprefix(self):
        """
        Remove any leading '.' characters from the except_module name.
        :return:
        """
        return self.except_module.lstrip(".")

    @property
    def except_module_basename(self):
        """
        Get the first part of an except module import name.
        eg: 'importlib' from 'importlib.util'

        :return: name of base module
        :rtype: str
        """
        return self.except_module_noprefix.split(".")[0]

    @property
    def except_module_names(self):
        """
        Get a list of all except submodule names in order.
        eg: ['util'] from 'importlib.util'
        :return: List of submodule names.
        :rtype: list[str]
        """
        return self.except_module_noprefix.split(".")[1:]

    def do_import(self, globs=None):
        try:
            mod = __import__(
                self.module_name_noprefix,
                globals=globs,
                level=self.import_level,
            )
        except ImportError:
            mod = __import__(
                self.except_module_noprefix,
                globals=globs,
                level=self.except_import_level,
            )
            submod_used = [self.except_module_basename]
            submodule_names = self.except_module_names

        else:
            submod_used = [self.module_basename]
            submodule_names = self.submodule_names

        for submod in submodule_names:
            submod_used.append(submod)
            mod = getattr(mod, submod)

        return {self.asname: mod}


class TryExceptFromImport(TryExceptImport):
    module_name: str
    attribute_name: str
    except_module: str
    except_attribute: str
    asname: str

    def __init__(self, module_name, attribute_name, except_module, except_attribute, asname):
        """
        Equivalent to:

        .. code-block:: python

            try:
                from <module_name> import <attribute_name> as <asname>
            except ImportError:
                from <except_module> import <except_attribute> as <asname>

        :param module_name: Name of module to 'try' to import from
        :type module_name: str
        :param attribute_name: Name of attribute to import from module_name
        :type attribute_name: str
        :param except_module: Name of module to import from if initial import fails
        :type except_module: str
        :param except_attribute: Name of attribute from the except_module
        :type except_attribute: str
        :param asname: Name to use to access this attribute on the LazyImporter
        :type asname: str
        """
        super().__init__(module_name, except_module, asname)
        self.attribute_name = attribute_name
        self.except_attribute = except_attribute

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"module_name={self.module_name!r}, "
            f"attribute_name={self.attribute_name!r}, "
            f"except_module={self.except_module!r}, "
            f"except_attribute={self.except_attribute!r}, "
            f"asname={self.asname!r}"
            f")"
        )

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            return (self.module_name, self.attribute_name, self.except_module, self.except_attribute, self.asname) == (
                other.module_name,
                other.attribute_name,
                other.except_module,
                other.except_attribute,
                other.asname,
            )
        return NotImplemented

    def do_import(self, globs=None):
        try:
            mod = __import__(
                self.module_name_noprefix,
                globals=globs,
                level=self.import_level,
            )
        except ImportError:
            mod = __import__(
                self.except_module_noprefix,
                globals=globs,
                level=self.except_import_level,
            )
            submod_used = [self.except_module_basename]
            submodule_names = self.except_module_names
            used_fallback = True
        else:
            submod_used = [self.module_basename]
            submodule_names = self.submodule_names
            used_fallback = False

        for submod in submodule_names:
            submod_used.append(submod)
            mod = getattr(mod, submod)

        if used_fallback:
            attrib = getattr(mod, self.except_attribute)
        else:
            attrib = getattr(mod, self.attribute_name)

        return {self.asname: attrib}


class _SubmoduleImports(ImportBase):
    module_name: str
    submodules: "set[str]"

    def __init__(self, module_name, submodules=None):
        """
        Private class to handle correctly importing submodules originally provided
        as ModuleImport classes without 'asname' provided

        :param module_name: name of the module
        :type module_name: str
        :param submodules: tuple of all submodules to import
        :type submodules: None | set[str]
        """
        self.module_name = module_name
        self.submodules = submodules if submodules is not None else set()

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"module_name={self.module_name!r}, "
            f"submodules={self.submodules!r}"
            f")"
        )

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            return (self.module_name, self.submodules) == (
                other.module_name,
                other.submodules,
            )
        return NotImplemented

    def do_import(self, globs=None):
        for submod in self.submodules:  # Make sure any submodules are in place
            __import__(
                submod,
                globals=globs,
                level=self.import_level,
            )

        mod = __import__(
            self.module_basename,
            globals=globs,
            level=self.import_level,
        )

        return {self.module_name: mod}


class _ImporterGrouper:
    def __init__(self):
        self._name = None

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, inst, cls=None):
        if inst:
            importers = self.group_importers(inst)
            setattr(inst, self._name, importers)
            return importers
        return self

    @staticmethod
    def group_importers(inst):
        """
        Take a LazyImporter and return the dictionary of names to _ImportBase subclasses
        needed to perform the lazy imports.

        ModuleImport instances with the same base module and no 'asname' are grouped in
        order to allow access to any of the submodules. As there is no way to know which
        submodule is being accessed all are imported when the base module is first
        accessed.

        This is kept outside of the LazyImporter class to keep the namespace of
        LazyImporter minimal. It should be called when the `_importers` attribute
        is first accessed on an instance.

        :param inst: LazyImporter instance
        :type inst: LazyImporter
        :return: lazy importers attribute dict mapping to the objects that
                 perform the imports
        :rtype: dict[str, ImportBase]
        """
        importers = {}

        for imp in inst._imports:  # noqa
            if getattr(imp, "import_level", 0) > 0 and inst._globals is None:  # noqa
                raise ValueError(
                    "Attempted to setup relative import without providing globals()."
                )

            # import x.y as z OR from x import y
            if asname := getattr(imp, "asname", None):
                if asname in importers:
                    raise ValueError(f"{asname!r} used for multiple imports.")
                importers[asname] = imp

            # from x import y, z ...
            elif asnames := getattr(imp, "asnames", None):
                for asname in asnames:
                    if asname in importers:
                        raise ValueError(f"{asname!r} used for multiple imports.")
                    importers[asname] = imp

            # import x OR import x.y
            elif isinstance(imp, ModuleImport):
                # Collecting all submodule imports under the main module import
                try:
                    importer = importers[imp.module_basename]
                except KeyError:
                    if imp.module_name == imp.module_basename:
                        importer = _SubmoduleImports(imp.module_basename)
                    else:
                        importer = _SubmoduleImports(
                            imp.module_basename, {imp.module_name_noprefix}
                        )
                    importers[imp.module_basename] = importer
                else:
                    if isinstance(importer, _SubmoduleImports):
                        # Don't add the basename
                        if imp.module_name_noprefix != imp.module_basename:
                            importer.submodules.add(imp.module_name_noprefix)
                    else:
                        raise ValueError(
                            f"{imp.module_name!r} used for multiple imports."
                        )
            else:
                raise TypeError(
                    f"{imp!r} is not an instance of "
                    f"ModuleImport, FromImport, MultiFromImport or TryExceptImport"
                )
        return importers


class LazyImporter:
    _imports: "list[ImportBase]"
    _globals: dict

    _importers = _ImporterGrouper()

    def __init__(self, imports, *, globs=None, eager_process=False):
        """
        Create a LazyImporter to import modules and objects when they are accessed
        on this importer object.

        globals() must be provided to the importer if relative imports are used.

        :param imports: list of imports
        :type imports: list[ImportBase]
        :param globs: globals object for relative imports
        :type globs: dict[str, typing.Any]
        :param eager_process: filter and check the imports eagerly
        :type eager_process: bool
        """
        # Keep original imports for __repr__
        self._imports = imports
        self._globals = globs

        if eager_process:
            _ = self._importers

    def __getattr__(self, name):
        # This performs the imports associated with the name of the attribute
        # and sets the result to that name.
        # If the name is linked to a MultiFromImport all of the attributes are
        # set when the first is accessed.
        try:
            importer = self._importers[name]
        except KeyError:
            raise AttributeError(
                f"{self.__class__.__name__!r} object has no attribute {name!r}"
            )

        import_data = importer.do_import(globs=self._globals)
        for key, value in import_data.items():
            setattr(self, key, value)

        obj = import_data[name]

        return obj

    def __dir__(self):
        return sorted(self._importers.keys())

    def __repr__(self):
        return (
            f"{self.__class__.__name__}"
            f"(imports={self._imports!r}, "
            f"globs={self._globals!r})"
        )


def get_importer_state(importer):
    """
    Get the importer state showing what has been imported and what attributes remain.

    :param importer: LazyImporter object to be examined
    :type importer: LazyImporter
    :return: Dict of imported_modules and lazy_modules
    :rtype: dict[str, dict[str, typing.Any] | list[str]]
    """
    # Get the dir *before* looking at __dict__
    # Calling 'dir' in the block would cause the __dict__ size to change
    # And fail iteration
    importer_dir = dir(importer)

    imported_attributes = {
        k: v for k, v in importer.__dict__.items() if k in importer_dir
    }

    lazy_attributes = [k for k in importer_dir if k not in imported_attributes]

    return {
        "imported_attributes": imported_attributes,
        "lazy_attributes": lazy_attributes,
    }


def get_module_funcs(importer, module_name=None):
    """
    Get simplified __getattr__ and __dir__ functions for a module that includes
    the imports from the importer as if they are part of the module.

    If a module name is provided, attributes from the module will appear in the
    __dir__ function and __getattr__ will set the attributes on the module when
    they are first accessed.

    If a module already has __dir__ and/or __getattr__ functions it is probably
    better to use the result of dir(importer) and getattr(importer, name) to
    extend those functions.

    :param importer: Lazy importer that provides additional objects to export
                     as part of a module
    :type importer: LazyImporter
    :param module_name: Name of the module that needs the __dir__ and
                        __getattr__ functions. Usually `__name__`.
    :type module_name: str
    :return: __getattr__ and __dir__ functions
    :rtype: tuple[types.FunctionType, types.FunctionType]
    """

    if module_name:
        mod = sys.modules[module_name]
        dir_data = sorted(list(mod.__dict__.keys()) + dir(importer))

        def __getattr__(name):
            try:
                attr = getattr(importer, name)
            except AttributeError:
                raise AttributeError(f"module {module_name!r} has no attribute {name!r}")
            setattr(mod, name, attr)
            return attr

    else:
        dir_data = dir(importer)

        def __getattr__(name):
            return getattr(importer, name)

    def __dir__():
        return dir_data

    return __getattr__, __dir__
