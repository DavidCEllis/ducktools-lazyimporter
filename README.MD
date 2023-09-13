# Lazy importer #

A lazy importer that plays nice with type checkers and linters.

```python
# my_module.py
from lazy_importer import lazy_importer

from inexpensive_module import func1  # Not lazily imported

with lazy_importer():
   from expensive_module import func2, func3  # lazily imported


# __init__.py

from lazy_importer.hook import lazy_hook

with lazy_hook():
    import my_module

```


## How it works ##


