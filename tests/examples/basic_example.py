from lazy_importer import lazy_importer


with lazy_importer():
    import inspect
    from dataclasses import dataclass
    from typing import NamedTuple as namedtuple
    import functools as ft
