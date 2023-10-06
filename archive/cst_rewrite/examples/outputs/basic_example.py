_LAZY_IMPORTS = {
    'inspect': ('inspect', 'inspect'), 
    'ft': ('functools', 'ft'), 
    'dataclass': ('dataclasses', 'dataclass', 'dataclass'), 
    'namedtuple': ('typing', 'NamedTuple', 'namedtuple')
}

def __getattr__(name):
    """
    Lazy importer __getattr__ function
    
    Imports lazy attributes and assigns them to the module for future access.
    """

    import sys
    
    try:
        lazy_import = _LAZY_IMPORTS[name]

        this_module = sys.modules[__name__]

        import importlib

        match lazy_import:
            case (module_name, alias):
                module = importlib.import_module(module_name)
                setattr(this_module, alias, module)
                return module
            case (module_name, from_name, alias):
                module = importlib.import_module(module_name, package=__name__)
                obj = getattr(module, from_name)
                setattr(this_module, alias, obj)
                return obj
            case _:
                raise TypeError(f"Received unrecognised object {lazy_import}")

    except (KeyError, AttributeError):
        raise AttributeError(
            f"Module {__name__} has no attribute {name!r}."
        )

def __dir__():
    import sys
    this_module = sys.modules[__name__]
    old_dir = this_module.__dict__.keys()
    new_items = ['inspect', 'ft', 'dataclass', 'namedtuple']
    return sorted({*old_dir, *new_items})
