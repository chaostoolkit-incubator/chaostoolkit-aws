import pytest

try:
    from chaoslib.log import configure_logger

    NEED_TO_CONFIGURE_LOGGER = True
except ImportError:
    NEED_TO_CONFIGURE_LOGGER = False


if NEED_TO_CONFIGURE_LOGGER:

    @pytest.fixture(scope="session", autouse=True)
    def setup_logger() -> None:
        configure_logger(verbose=True)
