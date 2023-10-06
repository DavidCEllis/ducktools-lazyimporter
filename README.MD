# lazy_importer.py #

Create an object that can be accessed to lazily
import modules/submodules.

## How to use ##

```python
from lazy_importer import lazy_importer, ModuleImport, FromImport

laz = lazy_importer([
    FromImport("collections", "namedtuple", asname="nt"),
    ModuleImport("inspect"),
])

def occasional_function():
    print(laz.inspect.signature(laz.nt))

# Imports only occur when the function is called.
occasional_function()
```