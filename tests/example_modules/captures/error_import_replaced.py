import builtins
import importlib

from ducktools.lazyimporter import LazyImporter
from ducktools.lazyimporter.capture import capture_imports


laz = LazyImporter()

with capture_imports(laz, auto_export=False):
    builtins.__import__ = importlib.__import__
