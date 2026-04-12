"""File storage management utilities."""

import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


def get_data_directory(base_dir: str = "data") -> Path:
    """
    Create and return the data directory.

    Args:
        base_dir: Base directory for data storage (default is "data")

    Returns:
        Path to the data directory
    """
    data_dir = Path(base_dir)
    data_dir.mkdir(exist_ok=True)
    return data_dir


def list_downloaded_files(directory: str = "data/excel") -> List[Path]:
    """
    List all Excel files in the download directory.

    Args:
        directory: Directory to list files from (default is "data/excel")

    Returns:
        List of Paths to Excel files
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        return []
    return list(dir_path.glob("*.xlsx"))


def delete_file(file_path: Path) -> bool:
    """
    Delete a file.

    Args:
        file_path: Path to the file

    Returns:
        True if successful, False otherwise
    """
    try:
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted: {file_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting {file_path}: {e}")
        return False


def get_file_size(file_path: Path) -> int:
    """
    Get file size in bytes.

    Args:
        file_path: Path to the file

    Returns:
        File size in bytes, or 0 if error
    """
    try:
        return file_path.stat().st_size
    except Exception as e:
        logger.error(f"Error getting file size: {e}")
        return 0
