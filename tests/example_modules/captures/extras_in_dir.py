# This test file is used to test that values defined *after* the lazyimporter appear in dir

from ducktools.lazyimporter import LazyImporter
from ducktools.lazyimporter.capture import capture_imports


_laz = LazyImporter()


with capture_imports(_laz, auto_export=True):
    import functools
    from collections import namedtuple


# These functions are defined *after* dir is set
def extra_func():
    pass

LTUAE = 42
