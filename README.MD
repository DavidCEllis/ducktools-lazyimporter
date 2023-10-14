# lazy_importer.py #

Create an object that can be accessed to lazily
import modules/submodules.

## How to use ##

```python
from lazy_importer import (
    LazyImporter,
    ModuleImport,
    FromImport,
    MultiFromImport,
    get_importer_state,
)

# Setup attributes but don't perform any imports
laz = LazyImporter([
    MultiFromImport(
        "collections", [("namedtuple", "nt"), "OrderedDict"]
    ),
    FromImport("pprint", "pprint"),
    FromImport("functools", "partial"),
    ModuleImport("inspect"),
])

print("Possible attributes:")
laz.pprint(dir(laz))
print()

print("pprint imported:")
laz.pprint(get_importer_state(laz))
print()

_ = laz.nt
print("Collections elements imported:")
laz.pprint(get_importer_state(laz))
print()

_ = laz.partial
print("Functools elements imported:")
laz.pprint(get_importer_state(laz))
print()
```

Output:
```
Possible attributes:
['OrderedDict', 'inspect', 'nt', 'partial', 'pprint']

pprint imported:
{'imported_attributes': {'pprint': <function pprint at ...>},
 'lazy_attributes': ['OrderedDict', 'inspect', 'nt', 'partial']}

Collections elements imported:
{'imported_attributes': {'OrderedDict': <class 'collections.OrderedDict'>,
                         'nt': <function namedtuple at ...>,
                         'pprint': <function pprint at ...>},
 'lazy_attributes': ['inspect', 'partial']}

Functools elements imported:
{'imported_attributes': {'OrderedDict': <class 'collections.OrderedDict'>,
                         'nt': <function namedtuple at ...>,
                         'partial': <class 'functools.partial'>,
                         'pprint': <function pprint at ...},
 'lazy_attributes': ['inspect']}
```