"""Unit tests for the CLI module."""

import pytest
import tempfile
from pathlib import Path

from click.testing import CliRunner

from src.cli import cli


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def sample_data_file():
    """Create a temporary sample data file for CLI testing."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        # Note: MONTH values without leading zeros to avoid pandas auto-conversion
        f.write("MANDT|FACTURA|RUBRO|CANTIDAD|PRECIO_TOTAL|MONTH\n")
        f.write("300|001-001-057647312|AM01|1.0|10.00|1\n")
        f.write("300|001-001-057647313|AM01|1.0|10.00|1\n")
        f.write("300|001-002-057647314|OT01|1.0|20.00|1\n")
        f.write("300|001-003-057647320|AM01|1.0|15.00|2\n")
        f.write("300|001-003-057647321|OT01|1.0|25.00|2\n")
        temp_path = f.name

    yield temp_path
    Path(temp_path).unlink()


class TestCliInfo:
    """Tests for the info command."""

    def test_info_command_success(self, runner, sample_data_file):
        """Test info command with valid file."""
        result = runner.invoke(cli, ["info", sample_data_file])
        assert result.exit_code == 0
        assert "File Information" in result.output
        assert "Size:" in result.output
        assert "Columns:" in result.output

    def test_info_command_nonexistent_file(self, runner):
        """Test info command with nonexistent file."""
        result = runner.invoke(cli, ["info", "/nonexistent/file.txt"])
        assert result.exit_code != 0

    def test_info_displays_columns(self, runner, sample_data_file):
        """Test that info displays column names."""
        result = runner.invoke(cli, ["info", sample_data_file])
        assert "MANDT" in result.output
        assert "FACTURA" in result.output
        assert "RUBRO" in result.output


class TestCliStats:
    """Tests for the stats command."""

    def test_stats_command_success(self, runner, sample_data_file):
        """Test stats command with valid file."""
        result = runner.invoke(cli, ["stats", sample_data_file])
        assert result.exit_code == 0
        assert "Statistics" in result.output
        assert "COUNT" in result.output
        assert "SUM" in result.output
        assert "MEAN" in result.output

    def test_stats_with_custom_column(self, runner, sample_data_file):
        """Test stats with custom column option."""
        result = runner.invoke(cli, ["stats", sample_data_file, "-c", "CANTIDAD"])
        assert result.exit_code == 0
        assert "CANTIDAD" in result.output

    def test_stats_invalid_column(self, runner, sample_data_file):
        """Test stats with nonexistent column."""
        result = runner.invoke(cli, ["stats", sample_data_file, "-c", "NONEXISTENT"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()


class TestCliGroup:
    """Tests for the group command."""

    def test_group_command_success(self, runner, sample_data_file):
        """Test group command with valid parameters."""
        result = runner.invoke(cli, ["group", sample_data_file])
        assert result.exit_code == 0
        assert "Grouped by" in result.output or "GROUP" in result.output.upper()

    def test_group_by_rubro(self, runner, sample_data_file):
        """Test group by rubro."""
        result = runner.invoke(cli, ["group", sample_data_file, "-g", "RUBRO"])
        assert result.exit_code == 0
        assert "RUBRO" in result.output or "AM01" in result.output or "OT01" in result.output

    def test_group_with_different_aggregations(self, runner, sample_data_file):
        """Test group with different aggregation methods."""
        for agg in ["sum", "mean", "count", "min", "max"]:
            result = runner.invoke(
                cli, ["group", sample_data_file, "-a", agg]
            )
            assert result.exit_code == 0

    def test_group_invalid_aggregation(self, runner, sample_data_file):
        """Test group with invalid aggregation."""
        result = runner.invoke(
            cli, ["group", sample_data_file, "-a", "invalid"]
        )
        assert result.exit_code != 0


class TestCliTop:
    """Tests for the top command."""

    def test_top_command_success(self, runner, sample_data_file):
        """Test top command with valid parameters."""
        result = runner.invoke(cli, ["top", sample_data_file])
        assert result.exit_code == 0
        assert "Top" in result.output

    def test_top_with_custom_number(self, runner, sample_data_file):
        """Test top with custom number of results."""
        result = runner.invoke(cli, ["top", sample_data_file, "-n", "3"])
        assert result.exit_code == 0

    def test_top_displays_ranking(self, runner, sample_data_file):
        """Test that top displays ranking numbers."""
        result = runner.invoke(cli, ["top", sample_data_file, "-n", "5"])
        assert result.exit_code == 0
        assert "Rank" in result.output or "1" in result.output

    def test_top_invalid_number(self, runner, sample_data_file):
        """Test top with invalid number."""
        result = runner.invoke(cli, ["top", sample_data_file, "-n", "0"])
        assert result.exit_code != 0
        assert "must be positive" in result.output.lower()


class TestCliCompare:
    """Tests for the compare command."""

    def test_compare_command_success(self, runner, sample_data_file):
        """Test compare command with valid periods."""
        result = runner.invoke(cli, ["compare", sample_data_file, "1", "2"])
        if result.exit_code != 0:
            print(f"Output: {result.output}")
        assert result.exit_code == 0
        assert "Comparison" in result.output

    def test_compare_displays_periods(self, runner, sample_data_file):
        """Test that compare displays both periods."""
        result = runner.invoke(cli, ["compare", sample_data_file, "1", "2"])
        assert result.exit_code == 0
        assert "1" in result.output
        assert "2" in result.output

    def test_compare_shows_difference(self, runner, sample_data_file):
        """Test that compare shows difference."""
        result = runner.invoke(cli, ["compare", sample_data_file, "1", "2"])
        assert result.exit_code == 0
        assert "Difference" in result.output

    def test_compare_shows_percentage(self, runner, sample_data_file):
        """Test that compare shows percentage change."""
        result = runner.invoke(cli, ["compare", sample_data_file, "1", "2"])
        assert result.exit_code == 0
        assert "Percentage" in result.output or "%" in result.output

    def test_compare_invalid_period(self, runner, sample_data_file):
        """Test compare with nonexistent period."""
        result = runner.invoke(cli, ["compare", sample_data_file, "001", "999"])
        assert result.exit_code != 0


class TestCliReport:
    """Tests for the report command."""

    def test_report_command_success(self, runner, sample_data_file):
        """Test report command with valid file."""
        result = runner.invoke(cli, ["report", sample_data_file])
        assert result.exit_code == 0
        assert "Report" in result.output
        assert "Statistics" in result.output

    def test_report_displays_summary(self, runner, sample_data_file):
        """Test that report displays summary statistics."""
        result = runner.invoke(cli, ["report", sample_data_file])
        assert result.exit_code == 0
        assert "Total:" in result.output
        assert "Average:" in result.output

    def test_report_displays_top_rubros(self, runner, sample_data_file):
        """Test that report displays top rubros."""
        result = runner.invoke(cli, ["report", sample_data_file])
        assert result.exit_code == 0
        assert "Top 5" in result.output or "Rubros" in result.output

    def test_report_save_to_file(self, runner, sample_data_file):
        """Test report with output file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            output_file = f.name

        try:
            result = runner.invoke(
                cli, ["report", sample_data_file, "-o", output_file]
            )
            assert result.exit_code == 0
            assert Path(output_file).exists()
            content = Path(output_file).read_text()
            assert "Report" in content or "Statistics" in content
        finally:
            Path(output_file).unlink()


class TestCliVersion:
    """Tests for version and help."""

    def test_version_flag(self, runner):
        """Test --version flag."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_help_flag(self, runner):
        """Test --help flag."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output or "usage:" in result.output.lower()

    def test_command_help(self, runner):
        """Test help for specific command."""
        result = runner.invoke(cli, ["info", "--help"])
        assert result.exit_code == 0
        assert "FILE_PATH" in result.output or "Usage" in result.output
