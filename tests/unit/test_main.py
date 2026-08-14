import pytest

from noema.main import main


def test_main_displays_bootstrap_status(capsys: pytest.CaptureFixture[str]) -> None:
    main()

    assert capsys.readouterr().out == "Noema Cognitive Runtime\nStatus: bootstrap\n"
