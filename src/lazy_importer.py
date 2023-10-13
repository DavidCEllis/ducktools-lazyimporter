"""
Tools to make a lazy importer object that can be set up to import
when first accessed.
"""
import abc
import sys

__version__ = "0.0.3-dev0"
__all__ = ["LazyImporter", "ModuleImport", "FromImport", "MultiFromImport"]


class _ImportBase(abc.ABC):
    module_name: str

    @property
    def module_basename(self):
        return self.module_name.split(".")[0]

    @property
    def submodule_names(self):
        return self.module_name.split(".")[1:]

    @abc.abstractmethod
    def do_import(self):
        pass


class ModuleImport(_ImportBase):
    module_name: str
    asname: None | str

    def __init__(self, module_name, asname=None):
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

    def do_import(self):
        try:  # Already imported
            mod = sys.modules[self.module_name]
        except KeyError:
            mod = __import__(self.module_name)

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
    asname: None | str

    def __init__(self, module_name, attrib_name, asname=None):
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

    def do_import(self):
        try:
            # Module already imported
            mod = sys.modules[self.module_name]
        except KeyError:
            # Perform the import
            mod = __import__(self.module_name)

            submod_used = [self.module_basename]
            for submod in self.submodule_names:
                submod_used.append(submod)
                try:
                    mod = getattr(mod, submod)
                except AttributeError:
                    invalid_module = ".".join(submod_used)
                    raise ModuleNotFoundError(f"No module named {invalid_module!r}")

        return {self.asname: getattr(mod, self.attrib_name)}


class MultiFromImport(_ImportBase):
    """
    Convenience to import multiple names from one module.

    Must be converted into FromImport objects inside the lazyimporter
    """

    module_name: str
    attrib_names: list[str | tuple[str, str]]

    def __init__(self, module_name, attrib_names):
        self.module_name = module_name
        self.attrib_names = attrib_names

    def __repr__(self):
        return (f"{self.__class__.__name__}("
                f"module_name={self.module_name!r}, "
                f"attrib_names={self.attrib_names!r})")

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            return (self.module_name, self.attrib_names) == (
                other.module_name,
                self.attrib_names,
            )
        return NotImplemented

    def as_from_imports(self) -> list[FromImport]:
        from_imports = []
        for name in self.attrib_names:
            if isinstance(name, str):
                from_imports.append(FromImport(self.module_name, name))
            else:
                from_imports.append(FromImport(self.module_name, name[0], name[1]))
        return from_imports

    @property
    def asnames(self) -> list[str]:
        names = []
        for item in self.attrib_names:
            if isinstance(item, str):
                names.append(item)
            else:
                names.append(item[1])

        return names

    def do_import(self):
        from_imports = {}

        try:
            # Module already imported
            mod = sys.modules[self.module_name]
        except KeyError:
            # Perform the import
            mod = __import__(self.module_name)

            submod_used = [self.module_basename]
            for submod in self.submodule_names:
                submod_used.append(submod)
                try:
                    mod = getattr(mod, submod)
                except AttributeError:
                    invalid_module = ".".join(submod_used)
                    raise ModuleNotFoundError(f"No module named {invalid_module!r}")

        for name in self.attrib_names:
            if isinstance(name, str):
                from_imports[name] = getattr(mod, name)
            else:
                from_imports[name[1]] = getattr(mod, name[0])

        return from_imports


class _SubmoduleImports(_ImportBase):
    """
    Internal class to handle submodules
    """

    module_name: str
    submodules: set[str]

    def __init__(self, module_name, submodules=None):
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

    def do_import(self):
        for submod in self.submodules:  # Make sure any submodules are in place
            try:
                _ = sys.modules[submod]
            except KeyError:
                __import__(submod)
        try:
            mod = sys.modules[self.module_basename]
        except KeyError:
            mod = __import__(self.module_basename)
        return {self.module_name: mod}


class LazyImporter:
    _imports: list[ModuleImport | FromImport | MultiFromImport]
    _importers = dict[str, ModuleImport | FromImport | MultiFromImport | _SubmoduleImports]

    def __init__(self, imports: list[ModuleImport | FromImport | MultiFromImport]):
        # Keep original imports for __repr__
        self._imports = imports
        self._importers = {}

        for imp in self._imports:
            if asname := getattr(imp, "asname", None):  # import x.y as z OR from x import y
                if asname in self._importers:
                    raise ValueError(f"{asname!r} used for multiple imports.")
                self._importers[asname] = imp
            elif asnames := getattr(imp, "asnames", None):  # from x import y, z ...
                for asname in asnames:
                    if asname in self._importers:
                        raise ValueError(f"{asname!r} used for multiple imports.")
                    self._importers[asname] = imp
            elif isinstance(imp, ModuleImport):  # import x OR import x.y
                # Collecting all submodule imports under the main module import
                try:
                    importer = self._importers[imp.module_basename]
                except KeyError:
                    if imp.module_name == imp.module_basename:
                        importer = _SubmoduleImports(imp.module_basename)
                    else:
                        importer = _SubmoduleImports(
                            imp.module_basename, {imp.module_name}
                        )
                    self._importers[imp.module_basename] = importer
                else:
                    if isinstance(importer, _SubmoduleImports):
                        # Don't add the basename
                        if imp.module_name != imp.module_basename:
                            importer.submodules.add(imp.module_name)
                    else:
                        raise ValueError(
                            f"{imp.module_name!r} used for multiple imports."
                        )
            else:
                raise TypeError(
                    f"{imp} is not an instance of ModuleImport or FromImport"
                )

    def __getattr__(self, name):
        try:
            importer = self._importers[name]
        except KeyError:
            raise AttributeError(
                f"{self.__class__.__name__!r} object has no attribute {name!r}"
            )

        import_data = importer.do_import()
        for key, value in import_data.items():
            setattr(self, key, value)

        obj = import_data[name]

        return obj

    def __dir__(self):
        return sorted(self._importers.keys())

    def __repr__(self):
        return f"{self.__class__.__name__}(imports={self._imports!r})"
