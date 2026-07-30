"""Tests for MultiYearAnalyzer and the year-aware YearlyAnalyzer.from_directory()."""

import pytest
import pandas as pd
from pathlib import Path
from tempfile import TemporaryDirectory

from src.yearly_analyzer import YearlyAnalyzer
from src.multi_year_analyzer import MultiYearAnalyzer


def _make_month_df(revenue: float) -> pd.DataFrame:
    """Build a 100-row sample invoice DataFrame with a fixed revenue per line."""
    return pd.DataFrame({
        'MANDT': [1] * 100,
        'FACTURA': [f'001-01-{i:06d}' for i in range(100)],
        'RUBRO': ['AG01'] * 60 + ['AL01'] * 40,
        'SECUENCIA': range(1, 101),
        'BLOQUE_FACTURA': ['A'] * 100,
        'ID_SUBTOTAL': range(1, 101),
        'DESC_RUBRO': ['Agua'] * 60 + ['Alcantarillado'] * 40,
        'PRECIO_UNI': [2.0] * 100,
        'PRECIO_TOTAL': [revenue] * 100,
        'PRECIO_DESC': [0.0] * 100,
        'CANTIDAD': [5.0] * 100,
        'MONTO_IVA': [2.0] * 100,
        'TARIFA': [1] * 100,
        'CONSU_HID': [''] * 100,
        'MONTO_NEG': [''] * 100,
    })


@pytest.fixture
def two_year_dir():
    """Write 12 months of 2024 and 12 months of 2025 data to one directory.

    2024: flat $10/line revenue every month (no seasonality).
    2025: flat $10/line except August is a spike to $20 and July a dip to $5,
    so August is the peak and July is the low in BOTH years — a genuine
    recurring seasonal pattern the tests can assert on.
    """
    with TemporaryDirectory() as tmpdir:
        for month in range(1, 13):
            df_2024 = _make_month_df(10.0)
            df_2024.to_csv(f"{tmpdir}/Datalle {month:02d}24.txt", sep='|', index=False)

            if month == 8:
                revenue_2025 = 20.0
            elif month == 7:
                revenue_2025 = 5.0
            else:
                revenue_2025 = 10.0
            df_2025 = _make_month_df(revenue_2025)
            df_2025.to_csv(f"{tmpdir}/Datalle {month:02d}25.txt", sep='|', index=False)

        yield tmpdir


@pytest.fixture
def single_year_dir():
    """Write only 2025 data (12 months) to a directory."""
    with TemporaryDirectory() as tmpdir:
        for month in range(1, 13):
            df = _make_month_df(10.0 + month)
            df.to_csv(f"{tmpdir}/Datalle {month:02d}25.txt", sep='|', index=False)
        yield tmpdir


class TestParsePeriod:
    """Test YearlyAnalyzer.parse_period() filename parsing."""

    def test_parse_period_extracts_month_and_year(self):
        month, year = YearlyAnalyzer.parse_period("Datalle 0125")
        assert month == "01"
        assert year == "2025"

    def test_parse_period_december(self):
        month, year = YearlyAnalyzer.parse_period("Datalle 1224")
        assert month == "12"
        assert year == "2024"

    def test_parse_period_invalid_stem(self):
        month, year = YearlyAnalyzer.parse_period("NotAMatch")
        assert month is None
        assert year is None

    def test_parse_period_v02_suffix_still_parses_month_year(self):
        # V02 filtering happens at the glob level, not in parse_period itself
        month, year = YearlyAnalyzer.parse_period("Datalle 0125 V02")
        assert month == "01"
        assert year == "2025"


class TestYearlyAnalyzerYearFilter:
    """Test the year= filter added to YearlyAnalyzer.from_directory() for Fase 8."""

    def test_mixed_year_directory_without_filter_collides(self, two_year_dir):
        """Regression check: confirms the pre-Fase-8 behavior (no year filter)
        still only yields 12 months, since same month codes across years
        overwrite each other in the dict — this is exactly why the filter
        was added, and MultiYearAnalyzer must always pass year=.
        """
        analyzer = YearlyAnalyzer.from_directory(two_year_dir)
        assert len(analyzer.months) == 12

    def test_year_filter_isolates_2024(self, two_year_dir):
        analyzer = YearlyAnalyzer.from_directory(two_year_dir, year="2024")
        assert len(analyzer.months) == 12
        metrics = analyzer.yearly_metrics()
        # 2024 is flat $10/line * 100 lines * 12 months = $12,000
        assert metrics["total_revenue"] == pytest.approx(12000.0, abs=0.01)

    def test_year_filter_isolates_2025(self, two_year_dir):
        analyzer = YearlyAnalyzer.from_directory(two_year_dir, year="2025")
        assert len(analyzer.months) == 12
        metrics = analyzer.yearly_metrics()
        # 2025 has the Jul/Aug anomaly, so revenue differs from 2024
        assert metrics["total_revenue"] != pytest.approx(12000.0, abs=0.01)

    def test_year_filter_accepts_two_digit_year(self, two_year_dir):
        analyzer = YearlyAnalyzer.from_directory(two_year_dir, year="24")
        assert len(analyzer.months) == 12
        metrics = analyzer.yearly_metrics()
        assert metrics["total_revenue"] == pytest.approx(12000.0, abs=0.01)

    def test_no_year_filter_backward_compatible(self, single_year_dir):
        """Single-year directories behave identically with or without year=."""
        analyzer_default = YearlyAnalyzer.from_directory(single_year_dir)
        analyzer_filtered = YearlyAnalyzer.from_directory(single_year_dir, year="2025")

        assert analyzer_default.months == analyzer_filtered.months
        assert analyzer_default.yearly_metrics()["total_revenue"] == pytest.approx(
            analyzer_filtered.yearly_metrics()["total_revenue"], abs=0.01
        )


class TestMultiYearAnalyzerInit:
    """Test MultiYearAnalyzer initialization."""

    def test_init_requires_data(self):
        with pytest.raises(ValueError):
            MultiYearAnalyzer({})

    def test_init_stores_sorted_years(self, two_year_dir):
        analyzer = MultiYearAnalyzer.from_directory(two_year_dir)
        assert analyzer.years == ["2024", "2025"]

    def test_is_multi_year_true(self, two_year_dir):
        analyzer = MultiYearAnalyzer.from_directory(two_year_dir)
        assert analyzer.is_multi_year() is True

    def test_is_multi_year_false_for_single_year(self, single_year_dir):
        analyzer = MultiYearAnalyzer.from_directory(single_year_dir)
        assert analyzer.is_multi_year() is False
        assert analyzer.years == ["2025"]


class TestFromDirectory:
    """Test MultiYearAnalyzer.from_directory() year auto-detection."""

    def test_from_directory_no_files_raises(self):
        with TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError):
                MultiYearAnalyzer.from_directory(tmpdir)

    def test_from_directory_each_year_has_12_months(self, two_year_dir):
        analyzer = MultiYearAnalyzer.from_directory(two_year_dir)
        for year in analyzer.years:
            assert len(analyzer.year_analyzers[year].months) == 12


class TestYearlyTotals:
    """Test yearly_totals()."""

    def test_yearly_totals_returns_all_years(self, two_year_dir):
        analyzer = MultiYearAnalyzer.from_directory(two_year_dir)
        totals = analyzer.yearly_totals()

        assert "2024" in totals
        assert "2025" in totals

    def test_yearly_totals_fields(self, two_year_dir):
        analyzer = MultiYearAnalyzer.from_directory(two_year_dir)
        totals = analyzer.yearly_totals()

        for year_data in totals.values():
            assert "revenue" in year_data
            assert "records" in year_data
            assert "invoices" in year_data
            assert "months_loaded" in year_data
            assert year_data["months_loaded"] == 12

    def test_yearly_totals_2024_revenue(self, two_year_dir):
        analyzer = MultiYearAnalyzer.from_directory(two_year_dir)
        totals = analyzer.yearly_totals()
        assert totals["2024"]["revenue"] == pytest.approx(12000.0, abs=0.01)


class TestCompareYears:
    """Test compare_years()."""

    def test_compare_years_unknown_year_raises(self, two_year_dir):
        analyzer = MultiYearAnalyzer.from_directory(two_year_dir)
        with pytest.raises(KeyError):
            analyzer.compare_years("2024", "2099")

    def test_compare_years_returns_structure(self, two_year_dir):
        analyzer = MultiYearAnalyzer.from_directory(two_year_dir)
        comparison = analyzer.compare_years("2024", "2025")

        assert "revenue" in comparison
        assert "records" in comparison
        assert "invoices" in comparison
        assert "category_changes" in comparison

    def test_compare_years_revenue_values(self, two_year_dir):
        analyzer = MultiYearAnalyzer.from_directory(two_year_dir)
        comparison = analyzer.compare_years("2024", "2025")

        assert comparison["revenue"]["2024"] == pytest.approx(12000.0, abs=0.01)
        assert "change_pct" in comparison["revenue"]

    def test_compare_years_category_changes_has_both_rubros(self, two_year_dir):
        analyzer = MultiYearAnalyzer.from_directory(two_year_dir)
        comparison = analyzer.compare_years("2024", "2025")

        assert "AG01" in comparison["category_changes"]
        assert "AL01" in comparison["category_changes"]


class TestGrowthRates:
    """Test growth_rates()."""

    def test_growth_rates_returns_dict(self, two_year_dir):
        analyzer = MultiYearAnalyzer.from_directory(two_year_dir)
        rates = analyzer.growth_rates()

        assert "2024->2025" in rates

    def test_growth_rates_fields(self, two_year_dir):
        analyzer = MultiYearAnalyzer.from_directory(two_year_dir)
        rates = analyzer.growth_rates()["2024->2025"]

        assert "revenue_change_pct" in rates
        assert "records_change_pct" in rates
        assert "invoices_change_pct" in rates

    def test_growth_rates_positive_for_higher_revenue_year(self, two_year_dir):
        analyzer = MultiYearAnalyzer.from_directory(two_year_dir)
        rates = analyzer.growth_rates()["2024->2025"]
        # 2025 has a net-positive July/August anomaly ($5 dip, $20 spike
        # average out higher than flat $10), so 2025 > 2024 revenue.
        assert rates["revenue_change_pct"] > 0


class TestSeasonalConsistency:
    """Test seasonal_consistency()."""

    def test_seasonal_consistency_returns_structure(self, two_year_dir):
        analyzer = MultiYearAnalyzer.from_directory(two_year_dir)
        result = analyzer.seasonal_consistency()

        assert "common_months" in result
        assert "monthly_breakdown" in result
        assert "peak_month_by_year" in result
        assert "low_month_by_year" in result

    def test_seasonal_consistency_common_months_all_twelve(self, two_year_dir):
        analyzer = MultiYearAnalyzer.from_directory(two_year_dir)
        result = analyzer.seasonal_consistency()
        assert len(result["common_months"]) == 12

    def test_seasonal_consistency_detects_no_recurring_peak(self, two_year_dir):
        """2024 is flat (peak is arbitrary/first max), 2025 peaks in August —
        they won't agree, so no recurring peak should be detected."""
        analyzer = MultiYearAnalyzer.from_directory(two_year_dir)
        result = analyzer.seasonal_consistency()
        assert result["recurring_peak_month"] is None

    def test_seasonal_consistency_2025_peak_is_august(self, two_year_dir):
        analyzer = MultiYearAnalyzer.from_directory(two_year_dir)
        result = analyzer.seasonal_consistency()
        assert result["peak_month_by_year"]["2025"] == "08"

    def test_seasonal_consistency_2025_low_is_july(self, two_year_dir):
        analyzer = MultiYearAnalyzer.from_directory(two_year_dir)
        result = analyzer.seasonal_consistency()
        assert result["low_month_by_year"]["2025"] == "07"


class TestRecurringPatternDetection:
    """Test the recurring-pattern case where both years genuinely agree."""

    def test_recurring_peak_detected_when_both_years_agree(self):
        with TemporaryDirectory() as tmpdir:
            for month in range(1, 13):
                revenue = 20.0 if month == 8 else 10.0
                for year_suffix in ["24", "25"]:
                    df = _make_month_df(revenue)
                    df.to_csv(f"{tmpdir}/Datalle {month:02d}{year_suffix}.txt", sep='|', index=False)

            analyzer = MultiYearAnalyzer.from_directory(tmpdir)
            result = analyzer.seasonal_consistency()

            assert result["recurring_peak_month"] == "08"
            assert "2024" in result["monthly_breakdown"]["08"]["was_peak_in"]
            assert "2025" in result["monthly_breakdown"]["08"]["was_peak_in"]


class TestComparisonReport:
    """Test generate_comparison_report()."""

    def test_report_single_year_graceful(self, single_year_dir):
        analyzer = MultiYearAnalyzer.from_directory(single_year_dir)
        report = analyzer.generate_comparison_report()

        assert "Only one year loaded" in report
        assert "2025" in report

    def test_report_multi_year_has_sections(self, two_year_dir):
        analyzer = MultiYearAnalyzer.from_directory(two_year_dir)
        report = analyzer.generate_comparison_report()

        assert "YEARLY TOTALS" in report
        assert "GROWTH RATES" in report
        assert "SEASONAL CONSISTENCY" in report
        assert "2024" in report
        assert "2025" in report

    def test_report_returns_string(self, two_year_dir):
        analyzer = MultiYearAnalyzer.from_directory(two_year_dir)
        report = analyzer.generate_comparison_report()
        assert isinstance(report, str)
        assert len(report) > 100


class TestIntegration:
    """Integration test covering the full multi-year workflow."""

    def test_full_workflow(self, two_year_dir):
        analyzer = MultiYearAnalyzer.from_directory(two_year_dir)

        assert analyzer.is_multi_year()
        totals = analyzer.yearly_totals()
        assert len(totals) == 2

        comparison = analyzer.compare_years("2024", "2025")
        assert comparison["revenue"]["change_pct"] != 0

        rates = analyzer.growth_rates()
        assert len(rates) == 1

        seasonality = analyzer.seasonal_consistency()
        assert seasonality["peak_month_by_year"]["2025"] == "08"

        report = analyzer.generate_comparison_report()
        assert len(report) > 0
