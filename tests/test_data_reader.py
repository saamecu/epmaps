"""Unit tests for the DataReader module."""

import pytest
import tempfile
from pathlib import Path
import pandas as pd

from src.data_reader import DataReader


class TestDataReaderInitialization:
    """Tests for DataReader initialization."""

    def test_init_with_valid_file(self, sample_data_file):
        """Test successful initialization with a valid file."""
        reader = DataReader(sample_data_file)
        assert reader.file_path == Path(sample_data_file)
        assert reader.delimiter == "|"
        assert reader.encoding == "utf-8"

    def test_init_with_custom_delimiter(self, sample_data_file):
        """Test initialization with custom delimiter."""
        reader = DataReader(sample_data_file, delimiter=",")
        assert reader.delimiter == ","

    def test_init_with_nonexistent_file(self):
        """Test initialization fails with nonexistent file."""
        with pytest.raises(FileNotFoundError):
            DataReader("/nonexistent/path/file.txt")

    def test_init_with_empty_path(self):
        """Test initialization fails with empty path."""
        with pytest.raises(ValueError, match="cannot be empty or None"):
            DataReader("")

    def test_init_with_none_path(self):
        """Test initialization fails with None path."""
        with pytest.raises(ValueError, match="cannot be empty or None"):
            DataReader(None)

    def test_init_with_path_object(self, sample_data_file):
        """Test initialization with Path object."""
        path_obj = Path(sample_data_file)
        reader = DataReader(path_obj)
        assert reader.file_path == path_obj


class TestDataReaderReadFull:
    """Tests for full file reading."""

    def test_read_full_returns_dataframe(self, sample_data_file):
        """Test that read_full returns a DataFrame."""
        reader = DataReader(sample_data_file)
        df = reader.read_full()
        assert isinstance(df, pd.DataFrame)

    def test_read_full_has_correct_columns(self, sample_data_file):
        """Test that read_full returns expected columns."""
        reader = DataReader(sample_data_file)
        df = reader.read_full()
        expected_cols = ["MANDT", "FACTURA", "RUBRO", "CANTIDAD"]
        assert all(col in df.columns for col in expected_cols)

    def test_read_full_not_empty(self, sample_data_file):
        """Test that read_full returns non-empty DataFrame."""
        reader = DataReader(sample_data_file)
        df = reader.read_full()
        assert len(df) > 0

    def test_read_full_with_custom_delimiter(self, csv_data_file):
        """Test read_full with comma delimiter."""
        reader = DataReader(csv_data_file, delimiter=",")
        df = reader.read_full()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0


class TestDataReaderReadChunks:
    """Tests for chunked reading."""

    def test_read_chunks_returns_iterator(self, sample_data_file):
        """Test that read_chunks returns an iterator."""
        reader = DataReader(sample_data_file)
        chunks = reader.read_chunks(chunksize=10)
        assert hasattr(chunks, "__iter__")

    def test_read_chunks_produces_dataframes(self, sample_data_file):
        """Test that chunks are DataFrames."""
        reader = DataReader(sample_data_file)
        chunks = reader.read_chunks(chunksize=5)
        for chunk in chunks:
            assert isinstance(chunk, pd.DataFrame)
            break

    def test_read_chunks_respects_chunksize(self, sample_data_file):
        """Test that chunks have at most chunksize rows."""
        reader = DataReader(sample_data_file)
        chunksize = 3
        chunks = reader.read_chunks(chunksize=chunksize)
        for chunk in chunks:
            assert len(chunk) <= chunksize

    def test_read_chunks_invalid_chunksize(self, sample_data_file):
        """Test that invalid chunksize raises ValueError."""
        reader = DataReader(sample_data_file)
        with pytest.raises(ValueError, match="must be positive"):
            reader.read_chunks(chunksize=0)

    def test_read_chunks_negative_chunksize(self, sample_data_file):
        """Test that negative chunksize raises ValueError."""
        reader = DataReader(sample_data_file)
        with pytest.raises(ValueError, match="must be positive"):
            reader.read_chunks(chunksize=-1)


class TestDataReaderFileInfo:
    """Tests for file information methods."""

    def test_get_file_info_returns_dict(self, sample_data_file):
        """Test that get_file_info returns a dictionary."""
        reader = DataReader(sample_data_file)
        info = reader.get_file_info()
        assert isinstance(info, dict)

    def test_get_file_info_has_required_keys(self, sample_data_file):
        """Test that file info contains required keys."""
        reader = DataReader(sample_data_file)
        info = reader.get_file_info()
        required_keys = ["path", "size_mb", "exists"]
        assert all(key in info for key in required_keys)

    def test_get_file_info_size_is_nonnegative(self, sample_data_file):
        """Test that file size is non-negative."""
        reader = DataReader(sample_data_file)
        info = reader.get_file_info()
        assert info["size_mb"] >= 0

    def test_get_file_info_exists_is_true(self, sample_data_file):
        """Test that exists flag is True for valid file."""
        reader = DataReader(sample_data_file)
        info = reader.get_file_info()
        assert info["exists"] is True

    def test_get_columns_returns_list(self, sample_data_file):
        """Test that get_columns returns a list."""
        reader = DataReader(sample_data_file)
        columns = reader.get_columns()
        assert isinstance(columns, list)
        assert len(columns) > 0

    def test_get_columns_contains_expected_headers(self, sample_data_file):
        """Test that columns include expected headers."""
        reader = DataReader(sample_data_file)
        columns = reader.get_columns()
        expected = ["MANDT", "FACTURA"]
        assert all(col in columns for col in expected)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_data_file():
    """Create a temporary sample data file with invoice data."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write("MANDT|FACTURA|RUBRO|CANTIDAD|PRECIO\n")
        f.write("300|001-012-057647312|AM01|1.000|2.10\n")
        f.write("300|001-012-057647313|AM01|1.000|2.10\n")
        f.write("300|001-012-057647314|AM01|1.000|2.10\n")
        f.write("300|001-012-057647320|AM01|1.000|2.10\n")
        f.write("300|001-012-057647321|AM01|1.000|2.10\n")
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink()


@pytest.fixture
def csv_data_file():
    """Create a temporary CSV data file."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, encoding="utf-8"
    ) as f:
        f.write("ID,NAME,VALUE\n")
        f.write("1,Test1,100\n")
        f.write("2,Test2,200\n")
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink()
