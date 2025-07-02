import pytest

from ducktools.lazyimporter import (
    ModuleImport,
    FromImport,
    MultiFromImport,
    TryExceptImport,
    TryExceptFromImport,
    TryFallbackImport,
    LazyImporter,
)


def test_missing_import():
    laz = LazyImporter([ModuleImport("importlib")])

    with pytest.raises(AttributeError):
        _ = laz.missing_attribute


def test_missing_attribute():
    import ex_othermod

    assert ex_othermod.name == "ex_othermod"

    with pytest.raises(AttributeError) as e:
        _ = ex_othermod.invalid

    assert e.match("module 'ex_othermod' has no attribute 'invalid'")


def test_invalid_input():
    with pytest.raises(TypeError) as e:
        laz = LazyImporter(["importlib"], eager_process=True)

    assert e.match(
        "'importlib' is not an instance of "
        "ModuleImport, FromImport, MultiFromImport or TryExceptImport"
    )


class TestModuleImportErrors:
    def test_invalid_relative_import(self):
        with pytest.raises(ValueError) as e:
            _ = ModuleImport(".relative_module")

        assert e.match("Relative import '.relative_module' requires an assigned name.")


    def test_invalid_relative_try_fallback(self):
        with pytest.raises(ValueError) as e:
            _ = TryFallbackImport(".relative_module", None)

        assert e.match("Relative import '.relative_module' requires an assigned name.")

    def test_invalid_submodule_import(self):
        with pytest.raises(ValueError) as e:
            _ = ModuleImport("importlib.util")

        assert e.match("Submodule import 'importlib.util' requires an assigned name.")

    def test_invalid_submodule_try_fallback(self):
        with pytest.raises(ValueError) as e:
            _ = TryFallbackImport("importlib.util", None)

        assert e.match("Submodule import 'importlib.util' requires an assigned name.")


class TestInvalidIdentifiers:
    def test_modimport_invalid(self):
        with pytest.raises(ValueError) as e:
            _ = ModuleImport("modname", "##invalid_identifier##")

        assert e.match(f"'##invalid_identifier##' is not a valid Python identifier.")

    def test_fromimport_invalid(self):
        with pytest.raises(ValueError) as e:
            _ = FromImport("modname", "attribute", "##invalid_identifier##")

        assert e.match(f"'##invalid_identifier##' is not a valid Python identifier.")

    def test_multifromimport_invalid(self):
        with pytest.raises(ValueError) as e:
            _ = MultiFromImport("modname", [("attribute", "##invalid_identifier##")])

        assert e.match(f"'##invalid_identifier##' is not a valid Python identifier.")

    def test_tryexceptimport_invalid(self):
        with pytest.raises(ValueError) as e:
            _ = TryExceptImport("modname", "altmod", "##invalid_identifier##")

        assert e.match(f"'##invalid_identifier##' is not a valid Python identifier.")

    def test_tryexceptfromimport_invalid(self):
        with pytest.raises(ValueError) as e:
            _ = TryExceptFromImport(
                "modname",
                "attribname",
                "altmod",
                "altattribute",
                "##invalid_identifier##",
            )
        assert e.match(f"'##invalid_identifier##' is not a valid Python identifier.")

    def test_tryfallbackimport_invalid(self):
        with pytest.raises(ValueError) as e:
            _ = TryFallbackImport(
                "modname",
                None,
                "##invalid_identifier##",
            )

        assert e.match(f"'##invalid_identifier##' is not a valid Python identifier.")


class TestNameClash:
    def test_moduleimport_clash(self):
        with pytest.raises(ValueError) as e:
            importer = LazyImporter(
                [ModuleImport("collections"), ModuleImport("collections")],
                eager_process=True,
            )
        assert e.match("'collections' used for multiple imports.")

    def test_fromimport_clash(self):
        """
        Multiple FromImports with clashing 'asname' parameters
        """

        with pytest.raises(ValueError) as e:
            laz = LazyImporter(
                [
                    FromImport("collections", "namedtuple", "nt"),
                    FromImport("typing", "NamedTuple", "nt"),
                ],
                eager_process=True,
            )

        assert e.match("'nt' used for multiple imports.")

    def test_multifromimport_clash(self):
        """
        Multiple FromImports with clashing 'asname' parameters
        """

        with pytest.raises(ValueError) as e:
            laz = LazyImporter(
                [
                    MultiFromImport(
                        "collections", [("namedtuple", "nt"), ("defaultdict", "nt")]
                    ),
                ],
                eager_process=True,
            )

        assert e.match("'nt' used for multiple imports.")

    def test_mixedimport_clash(self):
        with pytest.raises(ValueError) as e:
            laz = LazyImporter(
                [
                    FromImport("mod1", "matching_mod_name"),
                    ModuleImport("matching_mod_name"),
                ],
                eager_process=True,
            )

        assert e.match("'matching_mod_name' used for multiple imports.")

    def test_reserved_name(self):
        # Single asname
        with pytest.raises(ValueError) as e:
            laz = LazyImporter(
                [
                    FromImport("mod1", "objname", "_importers"),
                ],
                eager_process=True,
            )

        assert e.match("'_importers' clashes with a LazyImporter internal name.")

        # Multiple asnames
        with pytest.raises(ValueError) as e:
            laz = LazyImporter(
                [
                    MultiFromImport("mod1", [("objname", "_importers")]),
                ],
                eager_process=True,
            )

        assert e.match("'_importers' clashes with a LazyImporter internal name.")

class TestNoGlobals:
    def test_relative_module_noglobals(self):
        """
        ModuleImport relative without globals where frame hacks are unavailable
        """
        laz = LazyImporter(
            [ModuleImport(".relative_module", asname="relative_module")],
            eager_process=False,
            eager_import=False,
        )

        laz._globals = None

        with pytest.raises(ValueError) as e:
            _ = laz._importers

        assert e.match(
            "Attempted to setup relative import without providing globals()."
        )

    def test_relative_from_noglobals(self):
        """
        FromImport relative without globals
        """
        laz = LazyImporter(
            [FromImport(".relative_module", "attribute")],
            eager_process=False,
            eager_import=False,
        )

        laz._globals = None

        with pytest.raises(ValueError) as e:
            _ = laz._importers

        assert e.match(
            "Attempted to setup relative import without providing globals()."
        )


class TestImportErrors:
    def test_module_import_nosubmod_asname(self):
        laz = LazyImporter(
            [
                ModuleImport("importlib.util.fakemod", asname="fakemod"),
            ]
        )

        with pytest.raises(ModuleNotFoundError) as e:
            _ = laz.fakemod

        assert e.match("No module named 'importlib.util.fakemod'")

    def test_tryexcept_import_nosubmod_asname(self):
        laz = LazyImporter(
            [
                TryExceptImport(
                    "importlib.util.fakemod1",
                    "importlib.util.fakemod",
                    asname="fakemod",
                ),
            ]
        )

        with pytest.raises(ModuleNotFoundError) as e:
            _ = laz.fakemod

        assert e.match("No module named 'importlib.util.fakemod'")
