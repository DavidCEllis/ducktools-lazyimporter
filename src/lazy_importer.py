"""
Tools to make a lazy importer object that can be set up to import
when first accessed.
"""
__version__ = "0.0.2-dev0"
__all__ = ["ModuleImport", "FromImport", "lazy_importer", "LazyImporterMaker"]


class ModuleImport:
    module_name: str
    asname: None | str

    @property
    def module_basename(self):
        return self.module_name.split(".")[0]

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


class FromImport:
    module_name: str
    attrib_name: str
    asname: None | str

    @property
    def module_basename(self):
        return self.module_name.split(".")[0]

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


def lazy_importer(modules: list[ModuleImport | FromImport]):
    importer = LazyImporterMaker(modules)
    return importer.get_lazy_importer_object()


def _make_module_import(base_module: str, submodules: set[str]) -> str:
    submodule_imports = "\n        ".join(f"import {module}" for module in submodules)

    src = (
        f"    @cached_property\n"
        f"    def {base_module}(self):\n"
        f"        {submodule_imports}\n"
        f"        return {base_module}\n"
    )
    return src


def _make_module_import_asname(module_name: str, asname: str) -> str:
    src = (
        f"    @cached_property\n"
        f"    def {asname}(self):\n"
        f"        import {module_name}\n"
        f"        return {module_name}\n"
    )
    return src


def _make_from_import(module_name: str, attrib: str, asname: str) -> str:
    src = (
        f"    @cached_property\n"
        f"    def {asname}(self):\n"
        f"        from {module_name} import {attrib}\n"
        f"        return {attrib}\n"
    )
    return src


class _cached_property:  # noqa
    """Drastically simplified cached_property for this use case"""
    def __init__(self, func):
        self.func = func

    def __set_name__(self, owner, name):
        self.asname = name

    def __get__(self, instance, owner):
        result = self.func(instance)
        setattr(instance, self.asname, result)
        return result


class LazyImporterMaker:
    def __init__(self, imports):
        self.imports = imports

    def __repr__(self):
        return f"{self.__class__.__name__}(imports={self.imports!r})"

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            return self.imports == other.imports
        return NotImplemented

    def _sort_imports(self):
        plain_module_imports = {}
        asname_module_imports = []
        from_imports = []

        for imp in self.imports:
            if isinstance(imp, ModuleImport):
                if imp.asname:
                    asname_module_imports.append(imp)
                else:
                    if imp.module_basename not in plain_module_imports:
                        plain_module_imports[imp.module_basename] = {
                            imp.module_basename
                        }
                    plain_module_imports[imp.module_basename].add(imp.module_name)
            elif isinstance(imp, FromImport):
                from_imports.append(imp)
            else:
                raise TypeError(
                    f"{imp} is not an instance of ModuleImport or FromImport"
                )

        return plain_module_imports, asname_module_imports, from_imports

    @property
    def classname(self):
        return f"LazyImporter_{__name__}"

    def get_lazy_class_source(self):
        plain_module_imports, asname_module_imports, from_imports = self._sort_imports()

        plain_imports = [
            _make_module_import(base_module, submodules)
            for base_module, submodules in plain_module_imports.items()
        ]
        asname_imports = [
            _make_module_import_asname(imp.module_name, imp.asname)
            for imp in asname_module_imports
        ]
        attrib_imports = [
            _make_from_import(imp.module_name, imp.attrib_name, imp.asname)
            for imp in from_imports
        ]
        complete_imports = "\n".join([*plain_imports, *asname_imports, *attrib_imports])

        class_def = (
            f"class {self.classname}:\n"
            f"    IMPORT_DETAILS = {self.imports!r}\n"
            f"    def __dir__(self):\n"
            f"        return [\n"
            f"            item.asname if item.asname else item.module_basename\n"
            f"            for item in self.IMPORT_DETAILS\n"
            f"        ]\n"
            f"\n"
            f"{complete_imports}\n"
        )

        return class_def

    def get_lazy_importer_object(self):
        globs = {
            "ModuleImport": ModuleImport,
            "FromImport": FromImport,
            "cached_property": _cached_property
        }
        exec(self.get_lazy_class_source(), globs)
        return globs[self.classname]()
