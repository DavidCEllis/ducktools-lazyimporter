# Capturing import statements #

There is now an experimental method to capture import statements. This works by replacing the 
`__import__` function within the block and restoring it afterwards. Currently this is in a 
separate submodule.

```python
from ducktools.lazyimporter import LazyImporter, get_importer_state
from ducktools.lazyimporter.capture import capture_imports

laz = LazyImporter()

with capture_imports(laz):
    # Inside this block, imports are captured and converted to lazy imports on laz
    import functools
    from collections import namedtuple as nt

print(get_importer_state(laz))

# Note that the captured imports are *not* available in the module namespace
try:
    functools
except NameError:
    print("functools is not here")
```

The replaced `__import__` function wraps the original `builtins.__import__` function outside
of the module it is being executed in. If you call a functiion inside the capturing block
that performs an import in another module that **should** work as expected.

