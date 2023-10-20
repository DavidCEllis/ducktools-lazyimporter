"""
Tools to make a lazy importer object that can be set up to import
when first accessed.
"""
import abc
import sys

__version__ = "v0.1.0"
__all__ = [
    "LazyImporter",
    "ModuleImport",
    "FromImport",
    "MultiFromImport",
    "get_importer_state",
    "get_module_funcs",
]


class _ImportBase(abc.ABC):
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


class ModuleImport(_ImportBase):
    module_name: str
    asname: None | str

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
        try:  # Already imported
            mod = sys.modules[self.module_name_noprefix]
        except KeyError:
            mod = __import__(
                self.module_name_noprefix,
                globals=globs,
                level=self.import_level,
            )

            if self.asname:  # return the submodule
                submod_used = [self.module_basename]
                for submod in self.submodule_names:
                    submod_used.append(submod)
                    try:
                        mod = getattr(mod, submod)
                    except AttributeError:
                        invalid_module = ".".join(submod_used)
                        raise ModuleNotFoundError(f"No module named {invalid_module!r}")

        if self.asname:
            return {self.asname: mod}
        else:
            return {self.module_basename: mod}


class FromImport(_ImportBase):
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
        try:
            # Module already imported
            mod = sys.modules[self.module_name]
        except KeyError:
            # Perform the import
            mod = __import__(
                self.module_name_noprefix,
                globals=globs,
                fromlist=[self.attrib_name],
                level=self.import_level,
            )

        return {self.asname: getattr(mod, self.attrib_name)}


class MultiFromImport(_ImportBase):
    module_name: str
    attrib_names: list[str | tuple[str, str]]

    def __init__(self, module_name, attrib_names):
        """
        Equivalent to `from <module_name> import <attrib_names[0]>, <attrib_names[1]>, ...
        when provided to a LazyImporter

        Optional 'asname' for attributes if given as a tuple.

        :param module_name: Name of the module to import from
        :type module_name: str
        :param attrib_names: List of attributes or (attribute, asname) pairs.
        :type attrib_names: list[str | tuple[str, str]]
        """
        self.module_name = module_name
        self.attrib_names = attrib_names

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
                self.attrib_names,
            )
        return NotImplemented

    @property
    def asnames(self):
        """

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

        try:
            # Module already imported
            mod = sys.modules[self.module_name]
        except KeyError:
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


class _SubmoduleImports(_ImportBase):
    module_name: str
    submodules: set[str]

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
            try:
                _ = sys.modules[submod]
            except KeyError:
                __import__(
                    submod,
                    globals=globs,
                    level=self.import_level,
                )
        try:
            mod = sys.modules[self.module_basename]
        except KeyError:
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
        :rtype: dict[str, _ImportBase]
        """
        importers = {}

        for imp in inst._imports:  # noqa
            if imp.import_level > 0 and inst._globals is None:
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
                    f"{imp} is not an instance of ModuleImport or FromImport"
                )
        return importers


class LazyImporter:
    _imports: list[ModuleImport | FromImport | MultiFromImport]
    _globals: dict

    _importers = _ImporterGrouper()

    def __init__(self, imports, *, globs=None):
        """
        Create a LazyImporter to import modules and objects when they are accessed
        on this importer object.

        globals() must be provided to the importer if relative imports are used.

        :param imports: list of imports
        :type imports: list[ModuleImport | FromImport | MultiFromImport]
        :param globs: globals object for relative imports
        :type globs: dict[str, typing.Any]
        """
        # Keep original imports for __repr__
        self._imports = imports
        self._globals = globs

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
        return f"{self.__class__.__name__}(imports={self._imports!r})"


def get_importer_state(importer):
    """
    Get the importer state showing what has been imported and what attributes remain.

    :param importer: LazyImporter object to be examined
    :type importer: LazyImporter
    :return: Dict of imported_modules and lazy_modules
    :rtype: dict[str, dict[str, typing.Any] | list[str]]
    """
    imported_attributes = {
        k: v for k, v in importer.__dict__.items() if k in dir(importer)
    }
    lazy_attributes = [k for k in dir(importer) if k not in imported_attributes]

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
            attr = getattr(importer, name)
            setattr(mod, name, attr)
            return attr

    else:
        dir_data = dir(importer)

        def __getattr__(name):
            return getattr(importer, name)

    def __dir__():
        return dir_data

    return __getattr__, __dir__
