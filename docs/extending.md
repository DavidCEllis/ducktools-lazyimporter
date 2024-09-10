# Extending by subclassing ImportBase #

Perhaps the included Import classes don't cover the import type you're looking 
for and you need an extension. These can be made by subclassing `ImportBase`.

Subclasses of `ImportBase` require 3 things:

`module_name` attribute must be the name of the default module to be imported.

`asname` or `asnames` must be either the identifier or a list of identifiers 
(respectively) to use to store attributes. This can be an attribute or a property.

`import_objects` must be a method that takes 2 arguments `(self, globs=None)`, performs
the import and returns a dictionary of the form `{asname: <object>, ...}` for all of
the names defined in `asname`/`asnames`.

For example say you want an importer that can do this kind of import:

```python
import sys
if sys.version_info >= (3, 12):
    import tomllib
else:
    import tomli as tomllib
```

You could write something like this:

```python
# NOTE: This is a simplified example using importlib.import_module
import importlib
from ducktools.lazyimporter import ImportBase, LazyImporter


class IfElseImporter(ImportBase):
    def __init__(self, condition, module_name, else_module_name, asname):
        self.condition = condition
        self.module_name = module_name
        self.else_module_name = else_module_name
        self.asname = asname
        
        if not self.asname.isidentifier():
            raise ValueError(f"{self.asname} is not a valid python identifier.")
        
    def import_objects(self, globs=None):
        if globs is not None:
            package = globs.get('__name__')
        else:
            package = None
            
        if self.condition:
            mod = importlib.import_module(self.module_name, package)
        else:
            mod = importlib.import_module(self.else_module_name, package)
            
        return {self.asname: mod}

```

And then use it with:

```python
import sys

laz = LazyImporter([
    IfElseImporter(
        condition=sys.version_info >= (3, 12),
        module_name="tomllib",
        else_module_name="tomli",
        asname="tomllib",
    )
])
```