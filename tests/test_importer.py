def test_basic_import():
    import function_module  # noqa
    import basic_import as f  # noqa

    assert "function_module" not in dir(f)

    assert "function_module" in f._LAZY_LOADERS
    assert function_module is f.function_module

    assert "function_module" in dir(f)


def test_from_import():
    import function_module  # noqa
    import from_import as f  # noqa

    assert "null_func" not in dir(f)
    assert "null_func" in f._LAZY_LOADERS

    assert function_module.null_func is f.null_func

    assert "null_func" in dir(f)
