from importlib import import_module as _import_module


__all__ = [
    "_make_getattr",
    "lazy_import",
    "lazy_from_import",
    "lazy_multi_from_import",
]

LOADER_ATTRIB_NAME = "_LAZY_LOADERS"


class ModuleLoader:
    module_name: str
    package_name: str
    attrib_name: str | None

    def __init__(self, module_name, package_name, attrib_name=None):
        self.module_name = module_name
        self.package_name = package_name
        self.attrib_name = attrib_name

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"module_name={self.module_name!r}, "
            f"package_name={self.package_name!r}, "
            f"attrib_name={self.attrib_name!r})"
        )

    def get_obj(self):
        module = _import_module(
            self.module_name,
            package=self.package_name
        )
        if self.attrib_name is None:
            return module
        else:
            return getattr(module, self.attrib_name)

    def get_basename(self):
        if not self.attrib_name:
            return self.module_name.split(".")[0]
        else:
            return self.attrib_name


def _make_getattr(module):
    def _getattr(name):
        # The loader attribute itself needs to be special cased
        # to avoid infinite recursion when access is attempted.
        if name == LOADER_ATTRIB_NAME:
            raise AttributeError(
                f"module {module.__name__!r} has no attribute {name!r}"
            )

        try:
            loader = getattr(module, LOADER_ATTRIB_NAME).pop(name)  # noqa

            # Import the object and assign it to the module
            obj = loader.get_obj()
            setattr(module, name, obj)
            return obj
        except (KeyError, AttributeError):
            raise AttributeError(
                f"module {module.__name__!r} has no attribute {name!r}"
            )

    _getattr.__name__ = "__getattr__"
    _getattr.__qualname__ = f"{module.__name__}.__getattr__"
    return _getattr


def lazy_import(
        caller_name: str,
        module_name: str,
        *,
        as_name: None | str = None,
) -> None:
    """
    Delayed/lazy import a python module. The import will happen when the object is
    accessed.

    **Submodules must be imported with a given as_name**

    eg:
    # caller_name.py
    import module_name [as as_name]

    :param caller_name: the __name__ where the function is being called
                        this should almost always be '__name__'. To avoid
                        potentially fragile inspection this must be provided
                        explicitly.
    :param module_name: name of the module to import.
    :param as_name: name to assign to imported value
    """
    if not module_name.isidentifier() and not as_name:
        raise ValueError(f"Module Name: {module_name} is not a valid identifier.")

    module = _import_module(caller_name)

    if not hasattr(module, "__getattr__"):
        module.__getattr__ = _make_getattr(module)

    try:
        lazy_loaders = getattr(module, LOADER_ATTRIB_NAME)
    except AttributeError:
        lazy_loaders = {}
        setattr(module, LOADER_ATTRIB_NAME, lazy_loaders)

    if as_name is None:
        as_name = module_name

    loader = ModuleLoader(
        module_name=module_name,
        package_name=caller_name,
    )

    lazy_loaders[as_name] = loader


def lazy_from_import(
        caller_name: str,
        module_name: str,
        attrib_name: str,
        *,
        as_name: None | str = None
) -> None:
    """
    Delayed/lazy import of an object from a python module. The import will only
    happen when the object is accessed.

    eg:
    # caller_name.py
    from module_name import object_name [as as_name]

    :param caller_name: the __name__ where the function is being called
                        this should almost always be '__name__'. To avoid
                        potentially fragile inspection this must be provided
                        explicitly.
    :param module_name: name of the module to import the object from.
    :param attrib_name: name of the object to be imported
    :param as_name: name to assign to the imported object
    """
    if not attrib_name.isidentifier():
        raise ValueError(f"Attribute Name: "
                         f"{attrib_name} is not a valid Python identifier.")

    module = _import_module(caller_name)
    if as_name is None:
        as_name = attrib_name

    if not hasattr(module, "__getattr__"):
        module.__getattr__ = _make_getattr(module)

    try:
        delayed_loaders = getattr(module, LOADER_ATTRIB_NAME)
    except AttributeError:
        delayed_loaders = {}
        setattr(module, LOADER_ATTRIB_NAME, delayed_loaders)

    if as_name is None:
        as_name = module_name

    loader = ModuleLoader(
        module_name=module_name,
        package_name=caller_name,
        attrib_name=attrib_name,
    )

    delayed_loaders[as_name] = loader


def lazy_multi_from_import(
        caller_name: str,
        module_name: str,
        object_names: list[str],
) -> None:
    """
        Delayed/lazy import of an object from a python module. The import will only
        happen when the object is accessed.

        eg:
        # caller_name.py
        from module_name import object_name [as as_name]

        :param caller_name: the __name__ where the function is being called
                            this should almost always be '__name__'. To avoid
                            potentially fragile inspection this must be provided
                            explicitly.
        :param module_name: name of the module to import the object from.
        :param object_names: names of the object to be imported
        """
    for name in object_names:
        lazy_from_import(
            caller_name=caller_name,
            module_name=module_name,
            attrib_name=name,
        )
