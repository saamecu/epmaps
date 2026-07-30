"""Multi-year analysis module for year-over-year invoice data comparison."""

from typing import Dict, List
from pathlib import Path
import numpy as np

from src.yearly_analyzer import YearlyAnalyzer


class MultiYearAnalyzer:
    """Compares invoice data across multiple years.

    Wraps one YearlyAnalyzer per year and provides:
    - Year-over-year revenue and volume comparisons
    - Category-level growth across years
    - Seasonal consistency checks (is a monthly pattern, e.g. an
      August peak, a recurring trend or a one-off?)
    - Growth rate analysis across consecutive year pairs
    """

    def __init__(self, year_analyzers: Dict[str, YearlyAnalyzer]) -> None:
        """Initialize MultiYearAnalyzer with one YearlyAnalyzer per year.

        Args:
            year_analyzers: Dict mapping 4-digit year strings (e.g. "2025")
                to YearlyAnalyzer instances holding that year's data.
        """
        if not year_analyzers:
            raise ValueError("year_analyzers cannot be empty")

        self.year_analyzers = year_analyzers
        self.years = sorted(year_analyzers.keys())

    @classmethod
    def from_directory(
        cls,
        directory: str,
        pattern: str = "Datalle*.txt",
        exclude_v02: bool = True,
    ) -> "MultiYearAnalyzer":
        """Discover every year present in a directory and load one
        YearlyAnalyzer per year.

        Args:
            directory: Path to directory containing data files across
                one or more years (filenames like "Datalle MMYY.txt").
            pattern: Glob pattern for files (default: Datalle*.txt).
            exclude_v02: Skip files with V02 in name (default: True).

        Returns:
            MultiYearAnalyzer instance covering every year found.

        Raises:
            ValueError: If no valid "Datalle MMYY" files are found.
        """
        path = Path(directory)
        files = sorted(path.glob(pattern))

        if exclude_v02:
            files = [f for f in files if "V02" not in f.name]

        years_found = set()
        for file_path in files:
            _, file_year = YearlyAnalyzer.parse_period(file_path.stem)
            if file_year is not None:
                years_found.add(file_year)

        if not years_found:
            raise ValueError(f"No 'Datalle MMYY' files found in {directory}")

        year_analyzers = {
            year: YearlyAnalyzer.from_directory(directory, pattern=pattern, exclude_v02=exclude_v02, year=year)
            for year in sorted(years_found)
        }

        return cls(year_analyzers)

    def is_multi_year(self) -> bool:
        """Whether more than one year of data was loaded.

        Returns:
            True if 2+ years are available for comparison.
        """
        return len(self.years) >= 2

    def yearly_totals(self) -> Dict[str, Dict]:
        """Get high-level totals for every loaded year.

        Returns:
            Dict mapping year -> {revenue, records, invoices, months_loaded}.
        """
        totals = {}
        for year in self.years:
            metrics = self.year_analyzers[year].yearly_metrics()
            totals[year] = {
                "revenue": metrics["total_revenue"],
                "records": metrics["total_records"],
                "invoices": metrics["total_invoices"],
                "avg_monthly_revenue": metrics["avg_monthly_revenue"],
                "cv_monthly_revenue": metrics["cv_monthly_revenue"],
                "months_loaded": len(self.year_analyzers[year].months),
            }
        return totals

    def compare_years(self, year_a: str, year_b: str) -> Dict:
        """Compare two specific years.

        Args:
            year_a: Earlier (or baseline) year, e.g. "2024".
            year_b: Later (or comparison) year, e.g. "2025".

        Returns:
            Dict with revenue/records/invoices deltas and % changes,
            plus a category-level breakdown.

        Raises:
            KeyError: If either year wasn't loaded.
        """
        if year_a not in self.year_analyzers:
            raise KeyError(f"Year {year_a} not loaded. Available: {self.years}")
        if year_b not in self.year_analyzers:
            raise KeyError(f"Year {year_b} not loaded. Available: {self.years}")

        metrics_a = self.year_analyzers[year_a].yearly_metrics()
        metrics_b = self.year_analyzers[year_b].yearly_metrics()

        def _pct_change(old: float, new: float) -> float:
            return round(((new - old) / old) * 100, 1) if old > 0 else 0.0

        revenue_change = _pct_change(metrics_a["total_revenue"], metrics_b["total_revenue"])
        records_change = _pct_change(metrics_a["total_records"], metrics_b["total_records"])
        invoices_change = _pct_change(metrics_a["total_invoices"], metrics_b["total_invoices"])

        # Category-level comparison (top 5 by combined revenue)
        cats_a = self.year_analyzers[year_a].top_categories_yearly(top_n=10)
        cats_b = self.year_analyzers[year_b].top_categories_yearly(top_n=10)
        all_rubros = set(cats_a.keys()) | set(cats_b.keys())

        category_changes = {}
        for rubro in all_rubros:
            rev_a = cats_a.get(rubro, {}).get("total_revenue", 0)
            rev_b = cats_b.get(rubro, {}).get("total_revenue", 0)
            category_changes[rubro] = {
                f"{year_a}_revenue": rev_a,
                f"{year_b}_revenue": rev_b,
                "change_pct": _pct_change(rev_a, rev_b) if rev_a > 0 else None,
            }

        return {
            "year_a": year_a,
            "year_b": year_b,
            "revenue": {
                year_a: metrics_a["total_revenue"],
                year_b: metrics_b["total_revenue"],
                "change_pct": revenue_change,
            },
            "records": {
                year_a: metrics_a["total_records"],
                year_b: metrics_b["total_records"],
                "change_pct": records_change,
            },
            "invoices": {
                year_a: metrics_a["total_invoices"],
                year_b: metrics_b["total_invoices"],
                "change_pct": invoices_change,
            },
            "category_changes": category_changes,
        }

    def growth_rates(self) -> Dict[str, Dict]:
        """Calculate year-over-year growth rate for every consecutive year pair.

        Returns:
            Dict mapping "{year_a}->{year_b}" -> comparison summary.
        """
        rates = {}
        for i in range(1, len(self.years)):
            year_a, year_b = self.years[i - 1], self.years[i]
            comparison = self.compare_years(year_a, year_b)
            rates[f"{year_a}->{year_b}"] = {
                "revenue_change_pct": comparison["revenue"]["change_pct"],
                "records_change_pct": comparison["records"]["change_pct"],
                "invoices_change_pct": comparison["invoices"]["change_pct"],
            }
        return rates

    def seasonal_consistency(self) -> Dict:
        """Check whether monthly patterns repeat across loaded years.

        For each month present in every loaded year, reports the revenue
        in that month per year and whether it was consistently the
        peak/low month of its respective year.

        Returns:
            Dict with per-month cross-year data and consistency flags.
        """
        common_months = None
        for year in self.years:
            months = set(self.year_analyzers[year].months)
            common_months = months if common_months is None else common_months & months

        common_months = sorted(common_months) if common_months else []

        result = {}
        peak_months_per_year = {}
        low_months_per_year = {}

        for year in self.years:
            metrics = self.year_analyzers[year].yearly_metrics()
            peak_months_per_year[year] = metrics["peak_month"]
            low_months_per_year[year] = metrics["low_month"]

        for month in common_months:
            revenues_by_year = {}
            for year in self.years:
                monthly_metrics = self.year_analyzers[year].yearly_metrics()["monthly_metrics"]
                revenues_by_year[year] = monthly_metrics.get(month, {}).get("revenue", 0)

            result[month] = {
                "revenue_by_year": revenues_by_year,
                "was_peak_in": [y for y in self.years if peak_months_per_year[y] == month],
                "was_low_in": [y for y in self.years if low_months_per_year[y] == month],
            }

        recurring_peak = self._most_common_or_none(list(peak_months_per_year.values()))
        recurring_low = self._most_common_or_none(list(low_months_per_year.values()))

        return {
            "common_months": common_months,
            "monthly_breakdown": result,
            "peak_month_by_year": peak_months_per_year,
            "low_month_by_year": low_months_per_year,
            "recurring_peak_month": recurring_peak,
            "recurring_low_month": recurring_low,
        }

    @staticmethod
    def _most_common_or_none(values: List[str]) -> str:
        """Return the most frequent value if it appears in every entry, else None.

        Args:
            values: List of month strings, one per year.

        Returns:
            The month if it's the peak/low in every year, else None.
        """
        if not values:
            return None
        if len(set(values)) == 1:
            return values[0]
        return None

    def generate_comparison_report(self) -> str:
        """Generate a text report comparing all loaded years.

        Returns:
            Formatted text report.
        """
        report = []
        report.append("=" * 80)
        report.append("MULTI-YEAR COMPARISON REPORT")
        report.append("=" * 80)
        report.append("")

        if not self.is_multi_year():
            report.append(f"Only one year loaded ({self.years[0]}) — nothing to compare yet.")
            report.append("Add another year's 'Datalle MMYY.txt' files to this directory to unlock")
            report.append("year-over-year comparisons, growth rates, and seasonal consistency checks.")
            report.append("")
            report.append("=" * 80)
            return "\n".join(report)

        totals = self.yearly_totals()
        report.append("YEARLY TOTALS")
        report.append("-" * 80)
        for year in self.years:
            t = totals[year]
            report.append(
                f"{year}: ${t['revenue']:>14,.0f} revenue | {t['records']:>10,} records | "
                f"{t['months_loaded']:>2} months loaded"
            )
        report.append("")

        report.append("GROWTH RATES (Year over Year)")
        report.append("-" * 80)
        for pair, rates in self.growth_rates().items():
            report.append(
                f"{pair}: Revenue {rates['revenue_change_pct']:+.1f}% | "
                f"Records {rates['records_change_pct']:+.1f}% | "
                f"Invoices {rates['invoices_change_pct']:+.1f}%"
            )
        report.append("")

        seasonality = self.seasonal_consistency()
        report.append("SEASONAL CONSISTENCY")
        report.append("-" * 80)
        if seasonality["recurring_peak_month"]:
            report.append(
                f"Recurring peak month: {seasonality['recurring_peak_month']} "
                f"(consistent across all {len(self.years)} years)"
            )
        else:
            report.append(
                f"Peak month varies by year: {seasonality['peak_month_by_year']}"
            )

        if seasonality["recurring_low_month"]:
            report.append(
                f"Recurring low month: {seasonality['recurring_low_month']} "
                f"(consistent across all {len(self.years)} years)"
            )
        else:
            report.append(
                f"Low month varies by year: {seasonality['low_month_by_year']}"
            )
        report.append("")

        report.append("=" * 80)

        return "\n".join(report)
