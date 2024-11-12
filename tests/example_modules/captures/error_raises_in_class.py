from ducktools.lazyimporter import LazyImporter
from ducktools.lazyimporter.capture import capture_imports


class X:
    laz = LazyImporter()
    with capture_imports(laz, auto_export=False):
        pass
