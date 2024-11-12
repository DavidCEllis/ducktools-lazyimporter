from ducktools.lazyimporter import LazyImporter
from ducktools.lazyimporter.capture import capture_imports


def __getattr__(name):
    raise AttributeError()


laz = LazyImporter()


with capture_imports(laz, auto_export=True):
    pass

