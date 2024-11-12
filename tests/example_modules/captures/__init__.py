from ducktools.lazyimporter import LazyImporter
from ducktools.lazyimporter.capture import capture_imports

from .func_submod import import_in_function

laz = LazyImporter()

with capture_imports(laz):
    import functools
    from . import import_target
    import_in_function()
