import os


def get_src_dir() -> str:
    """Return the absolute path to the `src/` directory of the project.

    This file lives in `src/aedificator/`, so climbing two levels returns `src/`.
    """
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_data_dir() -> str:
    """Return the `src/data` directory, creating it if necessary."""
    p = os.path.join(get_src_dir(), "data")
    os.makedirs(p, exist_ok=True)
    return p


def get_logs_dir() -> str:
    """Return the `src/data/logs` directory, creating it if necessary."""
    p = os.path.join(get_data_dir(), "logs")
    os.makedirs(p, exist_ok=True)
    return p


def get_db_path() -> str:
    """Return the full path to the Aedificator sqlite DB file."""
    return os.path.join(get_data_dir(), "aedificator.db")


def get_backup_file() -> str:
    """Return the full path to the default backup file in `src/data`."""
    return os.path.join(get_data_dir(), "backup.backup")
