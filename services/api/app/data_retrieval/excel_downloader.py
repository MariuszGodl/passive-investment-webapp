"""Excel file downloader module."""

import asyncio
import logging
from pathlib import Path
from typing import Optional

import aiohttp
import pandas as pd
# xlrd is required for reading .xls files (older Excel format)
# It's imported here to ensure pandas can use it as an engine
import xlrd  # noqa: F401

logger = logging.getLogger(__name__)


class ExcelDownloader:
    """Download and validate Excel files from URLs."""

    def __init__(self, storage_dir: str = "data/excel"):
        """
        Initialize the downloader.
        
        :param: storage_dir str: Directory to store downloaded Excel files
        """

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Excel files will be stored in: {self.storage_dir}")

    async def download(
        self, url: str, filename: str, extension: str = "xlsx", timeout: int = 30
    ) -> Optional[Path]:
        """
        Download an Excel file from a URL.
        
        :param: url str: URL to the Excel file
        :param: filename str: Name to save the file as (without extension)
        :param: extension str: File extension (default is "xlsx")
        :param: timeout int: Download timeout in seconds
        
        :return: Path to downloaded file or None if failed
        """

        try:
            file_path = self.storage_dir / f"{filename}.{extension}"
            
            logger.info(f"Downloading from {url} to {file_path}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=timeout) as response:
                    if response.status == 200:
                        with open(file_path, "wb") as f:
                            f.write(await response.read())
                        logger.info(f"Downloaded: {file_path}")
                        return file_path
                    else:
                        logger.error(f"Failed to download: HTTP {response.status}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.error(f"Download timeout for {url}")
            return None
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            return None

    def read_excel(self, file_path: Path, sheet_name: int = 0) -> Optional[pd.DataFrame]:
        """
        Read an Excel file into a pandas DataFrame.

        :param: file_path Path: Path to the Excel file
        :param: sheet_name int: Sheet index or name to read

        :return: DataFrame or None if failed
        """

        try:
            # Determine engine based on file extension
            if file_path.suffix.lower() == '.xls':
                engine = 'xlrd'
            else:
                engine = None  # Let pandas auto-detect

            df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine)
            logger.info(f"Read {len(df)} rows from {file_path.name}")
            return df
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return None

    async def download_and_process(
        self, url: str, filename: str, extension: str = "xlsx", sheet_name: str | int = 0
    ) -> Optional[pd.DataFrame]:
        """
        Download an Excel file and return it as a DataFrame.

        :param: url str: URL to the Excel file
        :param: filename str: Name to save the file as
        :param: extension str: File extension (default is "xlsx")
        :param: sheet_name str | int: Sheet index or name to read

        :return: DataFrame or None if failed
        """

        file_path = await self.download(url, filename, extension)
        if file_path:
            return self.read_excel(file_path, sheet_name)
        return None
