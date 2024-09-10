import abc
from typing import (
    Any,
    TypedDict,
    overload,
    type_check_only,
)
import types

__version__: str
__all__: list[str] = [
    "LazyImporter",
    "ModuleImport",
    "FromImport",
    "MultiFromImport",
    "TryExceptImport",
    "TryExceptFromImport",
    "TryFallbackImport",
    "ImportBase",
    "get_importer_state",
    "get_module_funcs",
    "force_imports",
]

EAGER_PROCESS: bool
EAGER_IMPORT: bool

class ImportBase(metaclass=abc.ABCMeta):
    module_name: str

    @property
    def module_name_noprefix(self) -> str: ...
    @property
    def import_level(self) -> int: ...
    @property
    def module_basename(self) -> str: ...
    @property
    def submodule_names(self) -> list[str]: ...
    @abc.abstractmethod
    def import_objects(
        self, globs: dict[str, Any] | None = ...
    ) -> dict[str, types.ModuleType | Any]: ...

class ModuleImport(ImportBase):
    module_name: str
    asname: str

    def __init__(self, module_name: str, asname: str | None = ...) -> None: ...
    def __repr__(self) -> str: ...
    def __eq__(self, other) -> bool: ...
    def import_objects(
        self, globs: dict[str, Any] | None = ...
    ) -> dict[str, types.ModuleType]: ...

class FromImport(ImportBase):
    module_name: str
    attrib_name: str
    asname: str

    def __init__(
        self, module_name: str, attrib_name: str, asname: str | None = ...
    ) -> None: ...
    def __repr__(self) -> str: ...
    def __eq__(self, other) -> bool: ...
    def import_objects(self, globs: dict[str, Any] | None = ...) -> dict[str, Any]: ...

class MultiFromImport(ImportBase):
    module_name: str
    attrib_names: list[str | tuple[str, str]]

    def __init__(
        self, module_name: str, attrib_names: list[str | tuple[str, str]]
    ) -> None: ...
    def __repr__(self) -> str: ...
    def __eq__(self, other) -> bool: ...
    @property
    def asnames(self): ...
    def import_objects(self, globs: dict[str, Any] | None = ...) -> dict[str, Any]: ...

class _TryExceptImportMixin(metaclass=abc.ABCMeta):
    except_module: str
    @property
    def except_import_level(self) -> int: ...
    @property
    def except_module_noprefix(self) -> str: ...
    @property
    def except_module_basename(self) -> str: ...
    @property
    def except_module_names(self) -> list[str]: ...

class TryExceptImport(_TryExceptImportMixin, ImportBase):
    module_name: str
    except_module: str
    asname: str

    def __init__(self, module_name: str, except_module: str, asname: str) -> None: ...
    def __repr__(self) -> str: ...
    def __eq__(self, other) -> bool: ...
    def import_objects(self, globs: dict[str, Any] | None = ...) -> dict[str, Any]: ...

class TryExceptFromImport(_TryExceptImportMixin, ImportBase):
    module_name: str
    attribute_name: str
    except_module: str
    except_attribute: str
    asname: str
    def __init__(
        self,
        module_name: str,
        attribute_name: str,
        except_module: str,
        except_attribute: str,
        asname: str,
    ) -> None: ...
    def __repr__(self) -> str: ...
    def __eq__(self, other) -> bool: ...
    def import_objects(self, globs: dict[str, Any] | None = ...) -> dict[str, Any]: ...

class TryFallbackImport(ImportBase):
        module_name: str
        fallback: Any
        asname: str

        def __init__(
                self,
                module_name: str,
                fallback: Any,
                asname: str | None = None,
        ) -> None: ...
        def __repr__(self) -> str: ...
        def __eq__(self, other) -> bool: ...
        def import_objects(self, globs: dict[str, Any] | None = ...) -> dict[str, Any]: ...

class _ImporterGrouper:
    def __init__(self) -> None: ...
    def __set_name__(self, owner, name) -> None: ...
    @overload
    def __get__(
        self, inst: None, cls: type[LazyImporter] | None = ...
    ) -> _ImporterGrouper: ...
    @overload
    def __get__(
        self, inst: LazyImporter, cls: type[LazyImporter] | None = ...
    ) -> list[ImportBase]: ...
    @staticmethod
    def group_importers(inst: LazyImporter) -> list[ImportBase]: ...

class LazyImporter:
    def __init__(
        self,
        imports: list[ImportBase],
        *,
        globs: dict[str, Any] | None = ...,
        eager_process: bool | None = ...,
        eager_import: bool | None = ...,
    ) -> None: ...
    def __getattr__(self, name: str) -> types.ModuleType | Any: ...
    def __dir__(self): ...

@type_check_only
class _ImporterState(TypedDict):
    imported_attributes: dict[str, Any]
    lazy_attributes: list[str]

def get_importer_state(
    importer: LazyImporter,
) -> _ImporterState: ...
def get_module_funcs(
    importer: LazyImporter,
    module_name: str | None = ...,
) -> tuple[types.FunctionType, types.FunctionType]: ...
def force_imports(importer: LazyImporter) -> None: ...
