from ducktools.lazyimporter import LazyImporter
from ducktools.lazyimporter.capture import capture_imports


laz = LazyImporter()
with capture_imports(laz, auto_export=False):
    import importlib.util
    import importlib
