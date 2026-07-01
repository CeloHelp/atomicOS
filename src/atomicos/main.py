"""Application entry point."""

from atomicos.diagnostics import configure_logging, get_logger
from atomicos.config import load_config
from atomicos.ui import launch_app


logger = get_logger("main")


def main() -> None:
    configure_logging()
    try:
        config = load_config()
    except Exception:
        logger.exception("Application configuration failed during startup")
        raise

    try:
        launch_app(config)
    except Exception:
        logger.exception("Application failed during startup")
        raise


if __name__ == "__main__":
    main()
