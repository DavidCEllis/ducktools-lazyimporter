from ducktools.lazyimporter import LazyImporter
from ducktools.lazyimporter.capture import capture_imports


def __dir__():
    return []


laz = LazyImporter()


with capture_imports(laz, auto_export=True):
    pass

