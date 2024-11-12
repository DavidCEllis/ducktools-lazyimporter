from ducktools.lazyimporter import LazyImporter
from ducktools.lazyimporter.capture import capture_imports


laz = LazyImporter(globs={})

with capture_imports(laz):
    pass
