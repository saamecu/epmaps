"""Yearly analyzer for multi-period invoice data analysis."""

from typing import Dict, List, Tuple
from pathlib import Path
import pandas as pd
import numpy as np

from src.analyzer import DataAnalyzer
from src.pattern_analyzer import PatternAnalyzer


class YearlyAnalyzer:
    """Analyzes invoice data across multiple periods (months, years).

    Combines data from multiple DataAnalyzer instances to find:
    - Seasonal patterns
    - Year-over-year trends
    - Category evolution
    - Anomalies and outliers
    - Correlation patterns
    """

    def __init__(self, month_data: Dict[str, DataAnalyzer]) -> None:
        """Initialize YearlyAnalyzer with multiple months of data.

        Args:
            month_data: Dict mapping month_id (01-12) to DataAnalyzer instances.
        """
        self.month_data = month_data
        self.months = sorted(month_data.keys())
        self.patterns = {m: PatternAnalyzer(month_data[m]) for m in self.months}
        self._yearly_metrics_cache: Dict = None
        self._top_categories_cache: Dict = None
        self._top_categories_cache_n: int = 0
        self._price_evolution_cache: Dict = None

    def _to_numeric(self, series: pd.Series) -> pd.Series:
        """Safely convert series to numeric, handling pandas nullable types.

        Args:
            series: Series to convert.

        Returns:
            Numeric series.
        """
        try:
            if series.dtype == 'object':
                return pd.to_numeric(series, errors="coerce")
            return series
        except:
            return pd.to_numeric(series, errors="coerce")

    @classmethod
    def from_directory(cls, directory: str, pattern: str = "Datalle*.txt", exclude_v02: bool = True):
        """Create YearlyAnalyzer from directory of files.

        Args:
            directory: Path to directory containing data files.
            pattern: Glob pattern for files (default: Datalle*.txt).
            exclude_v02: Skip files with V02 in name (default: True).

        Returns:
            YearlyAnalyzer instance with loaded data.
        """
        path = Path(directory)
        files = sorted(path.glob(pattern))

        if exclude_v02:
            files = [f for f in files if "V02" not in f.name]

        month_data = {}
        for file_path in files:
            # Extract month from filename (Datalle MMYY.txt or Datalle 0125.txt)
            parts = file_path.stem.split()
            if len(parts) >= 2:
                date_str = parts[1]  # MMYY format
                month_id = date_str[:2]  # MM
                month_data[month_id] = DataAnalyzer.from_file(str(file_path))

        return cls(month_data)

    def yearly_metrics(self) -> Dict:
        """Calculate yearly aggregate metrics.

        Scans every monthly DataFrame, so the result is cached after the
        first call — repeated calls (including indirect ones from
        monthly_changes(), Forecaster, and AnomalyDetector) are free.

        Returns:
            Dictionary with yearly statistics.
        """
        if self._yearly_metrics_cache is not None:
            return self._yearly_metrics_cache

        metrics = {}

        for month_id in self.months:
            df = self.month_data[month_id].df
            # Don't use to_numeric if already numeric
            try:
                prices = df["PRECIO_TOTAL"].dropna()
                if prices.dtype == 'object':
                    prices = pd.to_numeric(prices, errors="coerce").dropna()
            except:
                prices = pd.to_numeric(df["PRECIO_TOTAL"], errors="coerce").dropna()

            try:
                quantities = df["CANTIDAD"].dropna()
                if quantities.dtype == 'object':
                    quantities = pd.to_numeric(quantities, errors="coerce").dropna()
            except:
                quantities = pd.to_numeric(df["CANTIDAD"], errors="coerce").dropna()

            metrics[month_id] = {
                "records": len(df),
                "revenue": float(prices.sum()),
                "invoices": df["FACTURA"].nunique(),
                "avg_price": float(prices.mean()) if len(prices) > 0 else 0,
                "median_price": float(prices.median()) if len(prices) > 0 else 0,
                "avg_quantity": float(quantities.mean()) if len(quantities) > 0 else 0,
            }

        # Aggregate statistics
        revenues = [metrics[m]["revenue"] for m in self.months]
        records = [metrics[m]["records"] for m in self.months]
        invoices = [metrics[m]["invoices"] for m in self.months]

        mean_rev = np.mean(revenues)
        cv = (np.std(revenues) / mean_rev) * 100 if mean_rev > 0 else 0
        total_inv = sum(invoices)
        lines_per_inv = sum(records) / total_inv if total_inv > 0 else 0

        self._yearly_metrics_cache = {
            "monthly_metrics": metrics,
            "total_revenue": sum(revenues),
            "avg_monthly_revenue": mean_rev,
            "median_monthly_revenue": np.median(revenues),
            "std_monthly_revenue": np.std(revenues),
            "cv_monthly_revenue": cv,
            "min_monthly_revenue": min(revenues),
            "max_monthly_revenue": max(revenues),
            "total_records": sum(records),
            "avg_monthly_records": np.mean(records),
            "total_invoices": total_inv,
            "avg_lines_per_invoice": lines_per_inv,
            "peak_month": max(self.months, key=lambda m: metrics[m]["revenue"]),
            "low_month": min(self.months, key=lambda m: metrics[m]["revenue"]),
        }
        return self._yearly_metrics_cache

    def monthly_changes(self) -> Dict:
        """Calculate month-over-month changes.

        Returns:
            Dictionary with MoM percentage changes.
        """
        metrics = self.yearly_metrics()["monthly_metrics"]
        changes = {}

        for i, month in enumerate(self.months):
            if i == 0:
                changes[month] = {"revenue_change": None, "records_change": None}
            else:
                prev_month = self.months[i - 1]
                prev_revenue = metrics[prev_month]["revenue"]
                curr_revenue = metrics[month]["revenue"]

                if prev_revenue > 0:
                    revenue_change = ((curr_revenue - prev_revenue) / prev_revenue) * 100
                else:
                    revenue_change = 0

                prev_records = metrics[prev_month]["records"]
                curr_records = metrics[month]["records"]

                if prev_records > 0:
                    records_change = ((curr_records - prev_records) / prev_records) * 100
                else:
                    records_change = 0

                changes[month] = {
                    "revenue_change": round(revenue_change, 1),
                    "records_change": round(records_change, 1),
                    "direction": "↑" if revenue_change > 0 else "↓",
                }

        return changes

    def category_evolution(self) -> Dict:
        """Analyze category revenue evolution across months.

        Returns:
            Dictionary with category trends per month.
        """
        evolution = {}

        for month_id in self.months:
            df = self.month_data[month_id].df.copy()
            df["PRECIO_TOTAL"] = self._to_numeric(df["PRECIO_TOTAL"])

            category_revenue = df.groupby("RUBRO")["PRECIO_TOTAL"].sum().sort_values(ascending=False)

            evolution[month_id] = {
                rubro: float(category_revenue[rubro]) for rubro in category_revenue.head(10).index
            }

        return evolution

    def top_categories_yearly(self, top_n: int = 5) -> Dict:
        """Get top categories across entire year.

        Concatenates every monthly DataFrame, so the result is cached.
        Categories are revenue-ordered, so a request for a smaller top_n
        than what's already cached is served by slicing the cached dict
        instead of re-scanning the full dataset.

        Args:
            top_n: Number of top categories to return.

        Returns:
            Dictionary with category statistics and trends.
        """
        if self._top_categories_cache is not None and top_n <= self._top_categories_cache_n:
            return dict(list(self._top_categories_cache.items())[:top_n])

        all_data = []
        for month_id in self.months:
            df = self.month_data[month_id].df.copy()
            df["MONTH"] = month_id
            all_data.append(df)

        combined_df = pd.concat(all_data, ignore_index=True)
        combined_df["PRECIO_TOTAL"] = self._to_numeric(combined_df["PRECIO_TOTAL"])

        # Total revenue by category
        category_total = combined_df.groupby("RUBRO")["PRECIO_TOTAL"].sum().sort_values(ascending=False)
        top_categories = category_total.head(top_n)

        result = {}
        for rubro in top_categories.index:
            rubro_data = combined_df[combined_df["RUBRO"] == rubro]
            monthly_revenue = rubro_data.groupby("MONTH")["PRECIO_TOTAL"].sum()

            if len(monthly_revenue) > 0 and monthly_revenue.notna().any():
                avg_monthly = float(monthly_revenue.mean())
                std_monthly = float(monthly_revenue.std())
                cv = round((std_monthly / avg_monthly) * 100, 1) if avg_monthly > 0 else 0
                min_month = monthly_revenue.idxmin()
                max_month = monthly_revenue.idxmax()
            else:
                avg_monthly = 0
                std_monthly = 0
                cv = 0
                min_month = "—"
                max_month = "—"

            result[rubro] = {
                "total_revenue": float(top_categories[rubro]),
                "pct_of_total": round((top_categories[rubro] / category_total.sum()) * 100, 1),
                "monthly_revenue": {m: float(monthly_revenue.get(m, 0)) for m in self.months},
                "avg_monthly": avg_monthly,
                "std_monthly": std_monthly,
                "cv_monthly": cv,
                "min_month": min_month,
                "max_month": max_month,
                "records_total": int(rubro_data.shape[0]),
            }

        self._top_categories_cache = result
        self._top_categories_cache_n = top_n
        return result

    def price_evolution(self) -> Dict:
        """Analyze price changes across months.

        Scans every monthly DataFrame, so the result is cached after the
        first call.

        Returns:
            Dictionary with monthly price statistics.
        """
        if self._price_evolution_cache is not None:
            return self._price_evolution_cache

        evolution = {}

        for month_id in self.months:
            df = self.month_data[month_id].df.copy()
            prices = self._to_numeric(df["PRECIO_TOTAL"]).dropna()

            if len(prices) > 0:
                mean_val = prices.mean()
                std_val = prices.std()
                evolution[month_id] = {
                    "avg": float(mean_val) if pd.notna(mean_val) else 0,
                    "median": float(prices.median()),
                    "std": float(std_val) if pd.notna(std_val) else 0,
                    "min": float(prices.min()),
                    "max": float(prices.max()),
                    "q25": float(prices.quantile(0.25)),
                    "q75": float(prices.quantile(0.75)),
                }
            else:
                evolution[month_id] = {
                    "avg": 0, "median": 0, "std": 0, "min": 0, "max": 0, "q25": 0, "q75": 0
                }

        self._price_evolution_cache = evolution
        return evolution

    def anomalies_by_month(self) -> Dict:
        """Detect anomalies per month.

        Returns:
            Dictionary with anomaly count by month.
        """
        anomalies = {}

        for month_id in self.months:
            df = self.month_data[month_id].df.copy()
            df["PRECIO_TOTAL"] = self._to_numeric(df["PRECIO_TOTAL"])

            anomalies[month_id] = {
                "zero_price": int(len(df[df["PRECIO_TOTAL"] == 0])),
                "negative_price": int(len(df[df["PRECIO_TOTAL"] < 0])),
                "duplicate_records": int(df.duplicated().sum()),
                "null_percentage": round((df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100, 2),
            }

        return anomalies

    def generate_yearly_report(self) -> str:
        """Generate comprehensive yearly analysis report.

        Returns:
            Formatted text report.
        """
        report = []
        metrics = self.yearly_metrics()
        changes = self.monthly_changes()
        top_cats = self.top_categories_yearly()
        prices = self.price_evolution()

        report.append("=" * 80)
        report.append("YEARLY INVOICE ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")

        # Summary
        report.append("YEARLY SUMMARY")
        report.append("-" * 80)
        report.append(f"Total Revenue:              ${metrics['total_revenue']:>15,.0f}")
        report.append(f"Average Monthly Revenue:    ${metrics['avg_monthly_revenue']:>15,.0f}")
        report.append(f"Monthly Std Dev:            ${metrics['std_monthly_revenue']:>15,.0f}")
        report.append(f"Coefficient of Variation:   {metrics['cv_monthly_revenue']:>14.1f}%")
        report.append(f"Revenue Range:              ${metrics['min_monthly_revenue']:,.0f} - "
                     f"${metrics['max_monthly_revenue']:,.0f}")
        report.append(f"Peak Month:                 {metrics['peak_month']} "
                     f"(${metrics['monthly_metrics'][metrics['peak_month']]['revenue']:,.0f})")
        report.append(f"Low Month:                  {metrics['low_month']} "
                     f"(${metrics['monthly_metrics'][metrics['low_month']]['revenue']:,.0f})")
        report.append("")

        report.append("VOLUME SUMMARY")
        report.append("-" * 80)
        report.append(f"Total Records:              {metrics['total_records']:>16,}")
        report.append(f"Average Monthly Records:    {metrics['avg_monthly_records']:>16,.0f}")
        report.append(f"Total Invoices:             {metrics['total_invoices']:>16,}")
        report.append(f"Avg Lines per Invoice:      {metrics['avg_lines_per_invoice']:>16.2f}")
        report.append("")

        report.append("MONTHLY PROGRESSION")
        report.append("-" * 80)
        for month in self.months:
            m_data = metrics["monthly_metrics"][month]
            m_change = changes[month]
            change_str = f"{m_change['direction']} {abs(m_change['revenue_change']):.1f}%" \
                if m_change['revenue_change'] is not None else "—"
            report.append(f"Month {month}: ${m_data['revenue']:>12,.0f} | "
                         f"{m_data['records']:>9,} records | {change_str:>8} | "
                         f"${m_data['avg_price']:>6.2f} avg price")
        report.append("")

        report.append("TOP 5 CATEGORIES")
        report.append("-" * 80)
        for rubro, data in top_cats.items():
            report.append(f"{rubro}: ${data['total_revenue']:>12,.0f} ({data['pct_of_total']:>5.1f}%) | "
                         f"Var: {data['cv_monthly']:.1f}% | "
                         f"Range: {data['min_month']}-{data['max_month']}")
        report.append("")

        report.append("PRICE ANALYSIS")
        report.append("-" * 80)
        for month in self.months:
            p = prices[month]
            report.append(f"Month {month}: Avg ${p['avg']:>6.2f} | "
                         f"Median ${p['median']:>6.2f} | "
                         f"Range ${p['min']:>6.2f}-${p['max']:>6.2f}")
        report.append("")

        report.append("=" * 80)

        return "\n".join(report)
