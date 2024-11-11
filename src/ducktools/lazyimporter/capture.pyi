from collections.abc import Callable
from typing import Any
from typing_extensions import Self

from . import LazyImporter

class CaptureError(Exception):
    ...

class _ImportPlaceholder:
    attrib_name: str
    placeholder_parent: _ImportPlaceholder

    def __init__(self, attrib_name: str | None = None, parent: _ImportPlaceholder | None = None) -> None: ...
    def __repr__(self) -> str: ...
    def __getattr__(self, item: str) -> _ImportPlaceholder: ...


class CapturedModuleImport:
    module_name: str
    placeholder: _ImportPlaceholder

    def __init__(self, module_name: str, placeholder: _ImportPlaceholder) -> None: ...
    def __eq__(self, other) -> bool: ...
    def __repr__(self) -> str: ...
    @property
    def final_element(self) -> str: ...

class CapturedFromImport:
    module_name: str
    attrib_name: str
    placeholder: _ImportPlaceholder

    def __init__(self, module_name: str, attrib_name: str, placeholder: _ImportPlaceholder) -> None: ...
    def __eq__(self, other) -> bool: ...
    def __repr__(self) -> str: ...


_import_signature = Callable[
    [str, dict[str, Any] | None, dict[str, Any] | None, tuple[str, ...] | None, int],
    Any,
]

def make_capturing_import(
    captured_imports: list[CapturedModuleImport | CapturedFromImport],
    globs: dict[str, Any],
    old_import: _import_signature,
) -> _import_signature: ...

class capture_imports:
    def __init__(self, importer: LazyImporter) -> None: ...
    def __enter__(self) -> Self: ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...
