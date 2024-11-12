from ducktools.lazyimporter import LazyImporter
from ducktools.lazyimporter.capture import capture_imports


def import_check():
    import functools
    return functools


laz = LazyImporter()
with capture_imports(laz, auto_export=False):
    import collections
    inner_import = import_check()
    class InnerClass:
        import typing
