# Test cases automatically generated by Pynguin (https://www.pynguin.eu).
# Please check them before you use them.
import pytest
import module_loading_typed as module_0


@pytest.mark.xfail(strict=True)
def test_case_0():
    str_0 = "\n    Simulate a dict for DjangoTranslation._catalog so as multiple catalogs\n    with different plural equations are kept separate.\n    "
    module_0.import_string(str_0)


def test_case_1():
    str_0 = "f@UgEl/ZN~iYOq\nbMf\t\t"
    bool_0 = module_0.module_has_submodule(str_0, str_0)
    assert bool_0 is False
    str_1 = ""
    with pytest.raises(ImportError):
        module_0.import_string(str_1)


@pytest.mark.xfail(strict=True)
def test_case_2():
    none_type_0 = None
    module_0.import_string(none_type_0)


def test_case_3():
    bool_0 = False
    bool_1 = module_0.module_has_submodule(bool_0, bool_0)
    assert bool_1 is False


def test_case_4():
    str_0 = "\n    Simulate a dict for DjangoTranslation._catalog so as multiple catalogs\n    with different plural equations are kept separate.\n    "
    with pytest.raises(ValueError):
        module_0.module_dir(str_0)


@pytest.mark.xfail(strict=True)
def test_case_5():
    module_0.autodiscover_modules()


@pytest.mark.xfail(strict=True)
def test_case_6():
    str_0 = "django"
    module_0.cached_import(str_0, str_0)


def test_case_7():
    str_0 = "re.0Ws&FhIJ"
    with pytest.raises(ImportError):
        module_0.import_string(str_0)
