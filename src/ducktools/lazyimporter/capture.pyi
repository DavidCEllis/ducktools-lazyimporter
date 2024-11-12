from collections.abc import Callable
from typing import Any
from typing_extensions import Self

from . import LazyImporter

class CaptureError(Exception):
    ...

class _ImportPlaceholder:
    capturer: capture_imports
    attrib_name: str
    placeholder_parent: _ImportPlaceholder

    def __init__(
        self,
        capturer: capture_imports,
        attrib_name: str | None = None,
        parent: _ImportPlaceholder | None = None
    ) -> None: ...
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

class capture_imports:
    importer: LazyImporter
    auto_export: bool

    captured_imports: list[CapturedModuleImport | CapturedFromImport]
    import_func: _import_signature | None
    previous_import_func: _import_signature | None
    globs: dict[str, Any] | None

    def __init__(self, importer: LazyImporter, auto_export: bool = True) -> None: ...

    def _make_capturing_import(self) -> _import_signature: ...

    def __enter__(self) -> Self: ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...
