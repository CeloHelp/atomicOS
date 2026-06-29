"""Application entry point."""

from atomicos.config import load_config
from atomicos.ui import launch_app


def main() -> None:
    launch_app(load_config())


if __name__ == "__main__":
    main()
