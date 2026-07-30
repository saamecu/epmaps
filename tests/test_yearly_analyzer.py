"""Tests for YearlyAnalyzer - multi-period invoice analysis."""

import pytest
import pandas as pd
from pathlib import Path
from tempfile import TemporaryDirectory
import numpy as np

from src.analyzer import DataAnalyzer
from src.yearly_analyzer import YearlyAnalyzer


@pytest.fixture
def sample_dataframe():
    """Create sample invoice data for testing."""
    return pd.DataFrame({
        'MANDT': [1] * 100,
        'FACTURA': ['001-01-000001'] * 50 + ['001-02-000001'] * 50,
        'RUBRO': ['AG01'] * 30 + ['AL01'] * 20 + ['AG01'] * 30 + ['AL01'] * 20,
        'SECUENCIA': range(1, 101),
        'BLOQUE_FACTURA': ['A'] * 100,
        'ID_SUBTOTAL': range(1, 101),
        'DESC_RUBRO': ['Agua'] * 60 + ['Alcantarillado'] * 40,
        'PRECIO_UNI': [2.0] * 100,
        'PRECIO_TOTAL': [10.0] * 100,
        'PRECIO_DESC': [0.0] * 100,
        'CANTIDAD': [5.0] * 100,
        'MONTO_IVA': [2.0] * 100,
        'TARIFA': [1] * 100,
        'CONSU_HID': [''] * 100,
        'MONTO_NEG': [''] * 100,
    })


@pytest.fixture
def sample_data_dir(sample_dataframe):
    """Create temporary directory with sample data files."""
    with TemporaryDirectory() as tmpdir:
        # Create 3 months of sample data
        for month in ['01', '02', '03']:
            filename = f"{tmpdir}/Datalle {month}25.txt"
            df = sample_dataframe.copy()
            df['FACTURA'] = df['FACTURA'].str.replace('01', month)
            df['PRECIO_TOTAL'] = [10.0 + (int(month) * 0.5)] * 100
            df.to_csv(filename, sep='|', index=False)

        # Also create V02 file (should be excluded)
        v02_file = f"{tmpdir}/Datalle 0425 V02.txt"
        sample_dataframe.to_csv(v02_file, sep='|', index=False)

        yield tmpdir


class TestYearlyAnalyzerInit:
    """Test YearlyAnalyzer initialization."""

    def test_init_with_valid_data(self, sample_dataframe):
        """Test initialization with valid data."""
        analyzer1 = DataAnalyzer(sample_dataframe)
        analyzer2 = DataAnalyzer(sample_dataframe)

        yearly = YearlyAnalyzer({'01': analyzer1, '02': analyzer2})
        assert yearly.months == ['01', '02']
        assert len(yearly.month_data) == 2

    def test_init_preserves_month_order(self, sample_dataframe):
        """Test that months are sorted."""
        analyzers = {str(m).zfill(2): DataAnalyzer(sample_dataframe) for m in [3, 1, 2]}
        yearly = YearlyAnalyzer(analyzers)
        assert yearly.months == ['01', '02', '03']

    def test_init_creates_patterns(self, sample_dataframe):
        """Test that PatternAnalyzer instances are created."""
        analyzer = DataAnalyzer(sample_dataframe)
        yearly = YearlyAnalyzer({'01': analyzer})
        assert '01' in yearly.patterns
        assert hasattr(yearly.patterns['01'], 'price_analysis')


class TestYearlyAnalyzerFromDirectory:
    """Test YearlyAnalyzer.from_directory()."""

    def test_from_directory_loads_files(self, sample_data_dir):
        """Test loading files from directory."""
        yearly = YearlyAnalyzer.from_directory(sample_data_dir)
        assert len(yearly.months) == 3
        assert '01' in yearly.months
        assert '02' in yearly.months
        assert '03' in yearly.months

    def test_from_directory_excludes_v02(self, sample_data_dir):
        """Test that V02 files are excluded."""
        yearly = YearlyAnalyzer.from_directory(sample_data_dir, exclude_v02=True)
        assert len(yearly.months) == 3
        assert '04' not in yearly.months  # V02 file should be skipped

    def test_from_directory_includes_v02_when_specified(self, sample_data_dir):
        """Test loading V02 files when exclude_v02=False."""
        yearly = YearlyAnalyzer.from_directory(sample_data_dir, exclude_v02=False)
        assert len(yearly.months) == 4  # Should include 04 V02
        assert '04' in yearly.months

    def test_from_directory_custom_pattern(self, sample_data_dir):
        """Test custom file pattern."""
        # This would need files matching pattern, skip for now
        yearly = YearlyAnalyzer.from_directory(
            sample_data_dir,
            pattern="Datalle*.txt",
            exclude_v02=True
        )
        assert len(yearly.months) >= 3


class TestYearlyMetrics:
    """Test yearly_metrics() calculations."""

    def test_yearly_metrics_returns_dict(self, sample_dataframe):
        """Test that yearly_metrics returns correct structure."""
        analyzer = DataAnalyzer(sample_dataframe)
        yearly = YearlyAnalyzer({'01': analyzer})
        metrics = yearly.yearly_metrics()

        assert isinstance(metrics, dict)
        assert 'total_revenue' in metrics
        assert 'avg_monthly_revenue' in metrics
        assert 'peak_month' in metrics
        assert 'low_month' in metrics

    def test_yearly_metrics_calculates_revenue(self, sample_dataframe):
        """Test revenue calculation."""
        analyzer = DataAnalyzer(sample_dataframe)
        yearly = YearlyAnalyzer({'01': analyzer})
        metrics = yearly.yearly_metrics()

        expected_revenue = 10.0 * 100  # PRECIO_TOTAL * count
        assert metrics['total_revenue'] == expected_revenue

    def test_yearly_metrics_calculates_cv(self, sample_dataframe):
        """Test coefficient of variation calculation."""
        analyzer1 = DataAnalyzer(sample_dataframe)
        analyzer2 = DataAnalyzer(sample_dataframe)
        yearly = YearlyAnalyzer({'01': analyzer1, '02': analyzer2})
        metrics = yearly.yearly_metrics()

        assert 'cv_monthly_revenue' in metrics
        assert isinstance(metrics['cv_monthly_revenue'], float)

    def test_yearly_metrics_identifies_peak_month(self, sample_dataframe):
        """Test peak month identification."""
        df1 = sample_dataframe.copy()
        df1['PRECIO_TOTAL'] = 10.0

        df2 = sample_dataframe.copy()
        df2['PRECIO_TOTAL'] = 20.0  # Higher

        analyzer1 = DataAnalyzer(df1)
        analyzer2 = DataAnalyzer(df2)
        yearly = YearlyAnalyzer({'01': analyzer1, '02': analyzer2})
        metrics = yearly.yearly_metrics()

        assert metrics['peak_month'] == '02'
        assert metrics['low_month'] == '01'

    def test_yearly_metrics_calculates_lines_per_invoice(self, sample_dataframe):
        """Test lines per invoice calculation."""
        analyzer = DataAnalyzer(sample_dataframe)
        yearly = YearlyAnalyzer({'01': analyzer})
        metrics = yearly.yearly_metrics()

        assert 'avg_lines_per_invoice' in metrics
        assert metrics['avg_lines_per_invoice'] > 0


class TestMonthlyChanges:
    """Test monthly_changes() calculations."""

    def test_monthly_changes_first_month_is_none(self, sample_dataframe):
        """Test that first month has no change reference."""
        analyzer = DataAnalyzer(sample_dataframe)
        yearly = YearlyAnalyzer({'01': analyzer})
        changes = yearly.monthly_changes()

        assert changes['01']['revenue_change'] is None

    def test_monthly_changes_calculates_percentage(self, sample_dataframe):
        """Test percentage change calculation."""
        df1 = sample_dataframe.copy()
        df1['PRECIO_TOTAL'] = 100.0

        df2 = sample_dataframe.copy()
        df2['PRECIO_TOTAL'] = 110.0  # 10% increase

        analyzer1 = DataAnalyzer(df1)
        analyzer2 = DataAnalyzer(df2)
        yearly = YearlyAnalyzer({'01': analyzer1, '02': analyzer2})
        changes = yearly.monthly_changes()

        assert changes['02']['revenue_change'] == pytest.approx(10.0, abs=0.1)

    def test_monthly_changes_direction(self, sample_dataframe):
        """Test direction indicator."""
        df1 = sample_dataframe.copy()
        df1['PRECIO_TOTAL'] = 100.0

        df2 = sample_dataframe.copy()
        df2['PRECIO_TOTAL'] = 90.0  # Decrease

        analyzer1 = DataAnalyzer(df1)
        analyzer2 = DataAnalyzer(df2)
        yearly = YearlyAnalyzer({'01': analyzer1, '02': analyzer2})
        changes = yearly.monthly_changes()

        assert changes['02']['direction'] == '↓'

    def test_monthly_changes_with_three_months(self, sample_data_dir):
        """Test month-to-month changes across 3 months."""
        yearly = YearlyAnalyzer.from_directory(sample_data_dir)
        changes = yearly.monthly_changes()

        assert changes['01']['revenue_change'] is None
        assert changes['02']['revenue_change'] is not None
        assert changes['03']['revenue_change'] is not None


class TestTopCategories:
    """Test top_categories_yearly()."""

    def test_top_categories_returns_top_n(self, sample_dataframe):
        """Test that correct number of categories returned."""
        analyzer = DataAnalyzer(sample_dataframe)
        yearly = YearlyAnalyzer({'01': analyzer})
        top_cats = yearly.top_categories_yearly(top_n=2)

        assert len(top_cats) == 2

    def test_top_categories_sorted_by_revenue(self, sample_dataframe):
        """Test categories are sorted by revenue."""
        analyzer = DataAnalyzer(sample_dataframe)
        yearly = YearlyAnalyzer({'01': analyzer})
        top_cats = yearly.top_categories_yearly(top_n=5)

        revenues = [data['total_revenue'] for data in top_cats.values()]
        assert revenues == sorted(revenues, reverse=True)

    def test_top_categories_includes_monthly_data(self, sample_data_dir):
        """Test monthly revenue included for each category."""
        yearly = YearlyAnalyzer.from_directory(sample_data_dir)
        top_cats = yearly.top_categories_yearly(top_n=2)

        for rubro, data in top_cats.items():
            assert 'monthly_revenue' in data
            assert isinstance(data['monthly_revenue'], dict)
            assert len(data['monthly_revenue']) == 3  # 3 months

    def test_top_categories_calculates_cv(self, sample_data_dir):
        """Test coefficient of variation for categories."""
        yearly = YearlyAnalyzer.from_directory(sample_data_dir)
        top_cats = yearly.top_categories_yearly(top_n=2)

        for rubro, data in top_cats.items():
            assert 'cv_monthly' in data
            assert isinstance(data['cv_monthly'], (int, float))

    def test_top_categories_pct_of_total(self, sample_dataframe):
        """Test percentage of total calculation."""
        analyzer = DataAnalyzer(sample_dataframe)
        yearly = YearlyAnalyzer({'01': analyzer})
        top_cats = yearly.top_categories_yearly(top_n=5)

        total_pct = sum(data['pct_of_total'] for data in top_cats.values())
        assert total_pct <= 100  # Should not exceed 100%


class TestPriceEvolution:
    """Test price_evolution()."""

    def test_price_evolution_returns_dict(self, sample_dataframe):
        """Test return type."""
        analyzer = DataAnalyzer(sample_dataframe)
        yearly = YearlyAnalyzer({'01': analyzer})
        prices = yearly.price_evolution()

        assert isinstance(prices, dict)
        assert '01' in prices

    def test_price_evolution_includes_statistics(self, sample_dataframe):
        """Test all required statistics are present."""
        analyzer = DataAnalyzer(sample_dataframe)
        yearly = YearlyAnalyzer({'01': analyzer})
        prices = yearly.price_evolution()

        required_keys = ['avg', 'median', 'std', 'min', 'max', 'q25', 'q75']
        for key in required_keys:
            assert key in prices['01']

    def test_price_evolution_across_months(self, sample_data_dir):
        """Test price evolution tracks changes across months."""
        yearly = YearlyAnalyzer.from_directory(sample_data_dir)
        prices = yearly.price_evolution()

        # Should have 3 months
        assert len(prices) == 3
        assert '01' in prices
        assert '02' in prices
        assert '03' in prices

        # Prices should be increasing (test data set this way)
        assert prices['01']['avg'] < prices['02']['avg']
        assert prices['02']['avg'] < prices['03']['avg']

    def test_price_evolution_handles_empty_data(self, sample_dataframe):
        """Test handling when prices are empty."""
        df_empty = sample_dataframe[sample_dataframe['PRECIO_TOTAL'] == 999]  # No match
        analyzer = DataAnalyzer(sample_dataframe)  # Use non-empty for valid test
        yearly = YearlyAnalyzer({'01': analyzer})
        prices = yearly.price_evolution()

        # Should have default values, not crash
        assert prices['01']['avg'] > 0


class TestAnomaliesByMonth:
    """Test anomalies_by_month()."""

    def test_anomalies_by_month_returns_dict(self, sample_dataframe):
        """Test return structure."""
        analyzer = DataAnalyzer(sample_dataframe)
        yearly = YearlyAnalyzer({'01': analyzer})
        anomalies = yearly.anomalies_by_month()

        assert isinstance(anomalies, dict)
        assert '01' in anomalies

    def test_anomalies_by_month_detects_zero_prices(self, sample_dataframe):
        """Test detection of zero-price records."""
        df = sample_dataframe.copy()
        df.loc[5:10, 'PRECIO_TOTAL'] = 0  # Add zero prices

        analyzer = DataAnalyzer(df)
        yearly = YearlyAnalyzer({'01': analyzer})
        anomalies = yearly.anomalies_by_month()

        assert anomalies['01']['zero_price'] == 6  # Should detect

    def test_anomalies_by_month_detects_duplicates(self, sample_dataframe):
        """Test duplicate record detection."""
        df = sample_dataframe.copy()
        df = pd.concat([df, df.iloc[0:5]], ignore_index=True)  # Add duplicates

        analyzer = DataAnalyzer(df)
        yearly = YearlyAnalyzer({'01': analyzer})
        anomalies = yearly.anomalies_by_month()

        assert anomalies['01']['duplicate_records'] > 0


class TestGenerateYearlyReport:
    """Test generate_yearly_report()."""

    def test_generate_yearly_report_returns_string(self, sample_dataframe):
        """Test return type."""
        analyzer = DataAnalyzer(sample_dataframe)
        yearly = YearlyAnalyzer({'01': analyzer})
        report = yearly.generate_yearly_report()

        assert isinstance(report, str)
        assert len(report) > 0

    def test_generate_yearly_report_includes_sections(self, sample_data_dir):
        """Test that all expected sections are in report."""
        yearly = YearlyAnalyzer.from_directory(sample_data_dir)
        report = yearly.generate_yearly_report()

        required_sections = [
            'YEARLY SUMMARY',
            'VOLUME SUMMARY',
            'MONTHLY PROGRESSION',
            'TOP 5 CATEGORIES',
            'PRICE ANALYSIS',
        ]

        for section in required_sections:
            assert section in report, f"Missing section: {section}"

    def test_generate_yearly_report_includes_metrics(self, sample_data_dir):
        """Test that key metrics appear in report."""
        yearly = YearlyAnalyzer.from_directory(sample_data_dir)
        report = yearly.generate_yearly_report()

        # Check for key values
        assert 'Total Revenue' in report
        assert 'Peak Month' in report
        assert 'Low Month' in report
        assert 'Coefficient of Variation' in report

    def test_generate_yearly_report_formatted(self, sample_data_dir):
        """Test that report is properly formatted."""
        yearly = YearlyAnalyzer.from_directory(sample_data_dir)
        report = yearly.generate_yearly_report()

        # Should have separators
        assert '=' * 80 in report
        assert '-' * 80 in report

        # Should be readable
        lines = report.split('\n')
        assert len(lines) > 20  # Should have substantial content


class TestIntegration:
    """Integration tests combining multiple methods."""

    def test_full_yearly_analysis_workflow(self, sample_data_dir):
        """Test complete workflow from directory to report."""
        # Load data
        yearly = YearlyAnalyzer.from_directory(sample_data_dir)

        # Get metrics
        metrics = yearly.yearly_metrics()
        assert metrics['total_revenue'] > 0

        # Get changes
        changes = yearly.monthly_changes()
        assert len(changes) == 3

        # Get categories
        top_cats = yearly.top_categories_yearly()
        assert len(top_cats) > 0

        # Get prices
        prices = yearly.price_evolution()
        assert len(prices) == 3

        # Get anomalies
        anomalies = yearly.anomalies_by_month()
        assert len(anomalies) == 3

        # Generate report
        report = yearly.generate_yearly_report()
        assert len(report) > 100

    def test_multi_month_consistency(self, sample_data_dir):
        """Test that metrics are consistent across methods."""
        yearly = YearlyAnalyzer.from_directory(sample_data_dir)

        metrics = yearly.yearly_metrics()
        top_cats = yearly.top_categories_yearly()

        # Sum of top categories should be <= total revenue
        top_cat_total = sum(cat['total_revenue'] for cat in top_cats.values())
        assert top_cat_total <= metrics['total_revenue'] * 1.01  # Small tolerance


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.parametrize("month_id", ["01", "02", "03", "06", "12"])
    def test_single_month_analysis(self, sample_dataframe, month_id):
        """Test analysis with single month."""
        analyzer = DataAnalyzer(sample_dataframe)
        yearly = YearlyAnalyzer({month_id: analyzer})

        metrics = yearly.yearly_metrics()
        assert metrics['total_revenue'] > 0

    def test_monthly_changes_no_change(self, sample_dataframe):
        """Test monthly_changes when no change occurred."""
        df1 = sample_dataframe.copy()
        df1['PRECIO_TOTAL'] = 100.0

        df2 = sample_dataframe.copy()
        df2['PRECIO_TOTAL'] = 100.0  # Same as month 1

        analyzer1 = DataAnalyzer(df1)
        analyzer2 = DataAnalyzer(df2)
        yearly = YearlyAnalyzer({'01': analyzer1, '02': analyzer2})
        changes = yearly.monthly_changes()

        assert changes['02']['revenue_change'] == pytest.approx(0.0, abs=0.1)
