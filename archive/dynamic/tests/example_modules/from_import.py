from lazy_importer import lazy_from_import


__all__ = ["function_module"]

# noinspection PyUnreachableCode
if False:
    from function_module import null_func

lazy_from_import(__name__, "function_module", "null_func")
