from ducktools.lazyimporter import LazyImporter
from ducktools.lazyimporter.capture import capture_imports


laz = LazyImporter()
with capture_imports(laz, auto_export=False):
    from functools import partial as p
    from collections import namedtuple as p
