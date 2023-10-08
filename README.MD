# lazy_importer.py #

Create an object that can be accessed to lazily
import modules/submodules.

## How to use ##

```python
from lazy_importer import LazyImporter, ModuleImport, FromImport

laz = LazyImporter([
    FromImport("collections", "namedtuple", asname="nt"),
    ModuleImport("inspect"),
])

def occasional_function():
    print(laz.inspect.signature(laz.nt))

# Imports only occur when the function is called 
# and the attributes are accessed
occasional_function()
```