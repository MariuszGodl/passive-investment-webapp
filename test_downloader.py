"""Example script to test the Excel downloader."""

import asyncio
import logging

from services.api.app.data_retrieval.excel_downloader import ExcelDownloader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


async def main():
    """Test the Excel downloader."""

    downloader = ExcelDownloader(storage_dir="data/excel")

    test_url = "https://www.gov.pl/attachment/26c05556-a312-47be-aa8d-ec4790b12b83"
    
    print("\n" + "=" * 60)
    print("Testing Excel Downloader")
    print("=" * 60)

    df = await downloader.download_and_process(
        url=test_url,
        filename="test_file",
        extension="xls",
    )

    if df is not None:
        print("\nData downloaded:")
        print(df.head(10))
        print(f"\nShape: {df.shape[0]} rows, {df.shape[1]} columns")
    else:
        print("\nFailed to download or process the file")


if __name__ == "__main__":
    asyncio.run(main())

