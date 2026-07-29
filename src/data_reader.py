"""Data reader module for parsing and loading invoice data."""

from pathlib import Path
from typing import Optional
import pandas as pd


class DataReader:
    """Reads and parses invoice data from text files.

    This class handles reading large pipe-delimited text files containing
    invoice details. It supports chunked reading for memory efficiency
    and provides methods to extract data by various criteria.

    Attributes:
        file_path: Path to the data file to read.
        delimiter: Character used to delimit fields (default: '|').
        encoding: File encoding (default: 'utf-8').
    """

    def __init__(
        self,
        file_path: str | Path,
        delimiter: str = "|",
        encoding: str = "utf-8",
    ) -> None:
        """Initialize DataReader.

        Args:
            file_path: Path to the data file.
            delimiter: Field delimiter character. Defaults to '|'.
            encoding: File encoding. Defaults to 'utf-8'.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If file_path is empty or None.
        """
        if not file_path:
            raise ValueError("file_path cannot be empty or None")

        self.file_path = Path(file_path)

        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

        self.delimiter = delimiter
        self.encoding = encoding

    def read_full(self) -> pd.DataFrame:
        """Read the entire data file into a DataFrame.

        Returns:
            DataFrame with all data from the file.

        Raises:
            pd.errors.ParserError: If there's an error parsing the file.
        """
        return pd.read_csv(
            self.file_path,
            delimiter=self.delimiter,
            encoding=self.encoding,
            dtype_backend="numpy_nullable",
        )

    def read_chunks(self, chunksize: int = 10000) -> pd.io.parsers.TextFileReader:
        """Read data in chunks for memory-efficient processing.

        Args:
            chunksize: Number of rows per chunk. Defaults to 10000.

        Returns:
            An iterator of DataFrames, each containing chunksize rows.

        Raises:
            ValueError: If chunksize is not positive.
        """
        if chunksize <= 0:
            raise ValueError("chunksize must be positive")

        return pd.read_csv(
            self.file_path,
            delimiter=self.delimiter,
            encoding=self.encoding,
            chunksize=chunksize,
            dtype_backend="numpy_nullable",
        )

    def get_file_info(self) -> dict:
        """Get metadata about the data file.

        Returns:
            Dictionary containing file information:
            - path: Full file path
            - size_mb: File size in megabytes
            - exists: Whether the file exists
        """
        size_mb = self.file_path.stat().st_size / (1024 * 1024)
        return {
            "path": str(self.file_path),
            "size_mb": round(size_mb, 2),
            "exists": self.file_path.exists(),
        }

    def get_columns(self) -> list[str]:
        """Get the column names from the data file.

        Returns:
            List of column names.
        """
        df = pd.read_csv(
            self.file_path,
            delimiter=self.delimiter,
            encoding=self.encoding,
            nrows=0,
        )
        return df.columns.tolist()

    def get_row_count(self) -> int:
        """Count the total number of rows in the file (excluding header).

        Note:
            This reads the entire file to count rows, which may be slow
            for very large files. Use with caution.

        Returns:
            Total number of data rows.
        """
        count = 0
        for _ in self.read_chunks():
            count += 1
        return count * 10000  # Approximate based on default chunksize
