import noema


def test_main_package_is_importable() -> None:
    assert noema.__version__ == "0.1.0"
