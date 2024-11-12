from ducktools.lazyimporter import LazyImporter
from ducktools.lazyimporter.capture import capture_imports


laz = LazyImporter()
cap = capture_imports(laz, auto_export=False)

with cap:
    pass

with cap:
    pass
