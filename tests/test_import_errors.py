import pytest

from ducktools.lazyimporter import (
    ModuleImport,
    FromImport,
    MultiFromImport,
    TryExceptImport,
    _SubmoduleImports,
    MultiFromImport,
    LazyImporter,
)


def test_missing_import():
    laz = LazyImporter([ModuleImport("importlib")])

    with pytest.raises(AttributeError):
        _ = laz.missing_attribute


def test_invalid_input():
    with pytest.raises(TypeError) as e:
        laz = LazyImporter(["importlib"], eager_process=True)

    assert e.match(
        "'importlib' is not an instance of "
        "ModuleImport, FromImport, MultiFromImport or TryExceptImport"
    )


def test_invalid_relative_import():
    with pytest.raises(ValueError) as e:
        _ = ModuleImport(".relative_module")

    assert e.match("Relative imports are not allowed without an assigned name.")


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


class TestNameClash:
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


class TestNoGlobals:
    def test_relative_module_noglobals(self):
        """
        ModuleImport relative without globals
        """
        with pytest.raises(ValueError) as e:
            laz = LazyImporter(
                [ModuleImport(".relative_module", asname="relative_module")],
                eager_process=True,
            )

        assert e.match(
            "Attempted to setup relative import without providing globals()."
        )

    def test_relative_from_noglobals(self):
        """
        FromImport relative without globals
        """
        with pytest.raises(ValueError) as e:
            laz = LazyImporter(
                [FromImport(".relative_module", "attribute")],
                eager_process=True,
            )

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
