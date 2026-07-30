"""Pattern analysis module for detecting trends and anomalies in invoice data."""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from src.analyzer import DataAnalyzer


class PatternAnalyzer:
    """Analyzes invoice data for patterns, trends, and anomalies.

    Identifies:
    - Price trends by category
    - Volume patterns
    - Seasonal trends
    - Anomalies and outliers
    - Category relationships
    """

    def __init__(self, analyzer: DataAnalyzer) -> None:
        """Initialize PatternAnalyzer with DataAnalyzer instance.

        Args:
            analyzer: DataAnalyzer instance with loaded data.
        """
        if not isinstance(analyzer, DataAnalyzer):
            raise TypeError("analyzer must be a DataAnalyzer instance")

        self.analyzer = analyzer
        self.df = analyzer.df.copy()

    @classmethod
    def from_file(cls, file_path: str):
        """Create PatternAnalyzer from file.

        Args:
            file_path: Path to data file.

        Returns:
            PatternAnalyzer instance.
        """
        analyzer = DataAnalyzer.from_file(file_path)
        return cls(analyzer)

    def extract_month_from_factura(self) -> pd.DataFrame:
        """Extract month from FACTURA column.

        FACTURA format: 001-012-057647312 where 012 is the month.

        Returns:
            DataFrame with MONTH column added.
        """
        df = self.df.copy()
        try:
            df.loc[:, "MONTH"] = df["FACTURA"].str.split("-").str[1]
        except Exception:
            df["MONTH"] = "unknown"
        return df

    def monthly_trends(self) -> Dict:
        """Analyze trends across months.

        Returns:
            Dictionary with monthly statistics and trends.
        """
        df = self.extract_month_from_factura()
        df.loc[:, "PRECIO_TOTAL"] = pd.to_numeric(df["PRECIO_TOTAL"], errors="coerce")

        monthly = df.groupby("MONTH")["PRECIO_TOTAL"].agg([
            "count",
            "sum",
            "mean",
            "std",
            "min",
            "max"
        ]).round(2)

        monthly = monthly.sort_values("sum", ascending=False)

        return {
            "monthly_stats": monthly.to_dict("index"),
            "top_month": monthly["sum"].idxmax(),
            "lowest_month": monthly["sum"].idxmin(),
            "avg_monthly_revenue": float(monthly["sum"].mean()),
            "month_count": len(monthly)
        }

    def category_trends(self) -> Dict:
        """Analyze trends by category (RUBRO).

        Returns:
            Dictionary with category statistics and trends.
        """
        df = self.df.copy()
        df.loc[:, "PRECIO_TOTAL"] = pd.to_numeric(df["PRECIO_TOTAL"], errors="coerce")

        category_stats = df.groupby("RUBRO").agg({
            "PRECIO_TOTAL": ["count", "sum", "mean", "std"],
            "CANTIDAD": ["sum", "mean"]
        }).round(2)

        categories = df["RUBRO"].unique()

        return {
            "categories": list(categories),
            "category_count": len(categories),
            "category_stats": category_stats.to_dict("index"),
            "dominant_category": df["RUBRO"].value_counts().idxmax()
        }

    def price_analysis(self) -> Dict:
        """Analyze price patterns and anomalies.

        Returns:
            Dictionary with price insights.
        """
        df = self.df.copy()
        df.loc[:, "PRECIO_TOTAL"] = pd.to_numeric(df["PRECIO_TOTAL"], errors="coerce")

        prices = df["PRECIO_TOTAL"].dropna()

        # Handle empty prices
        if len(prices) == 0:
            return {
                "price_stats": {
                    "mean": 0,
                    "median": 0,
                    "std": 0,
                    "min": 0,
                    "max": 0
                },
                "outlier_count": 0,
                "outlier_percentage": 0,
                "price_by_category": {}
            }

        # Calculate statistics
        mean_price = prices.mean()
        std_price = prices.std()
        median_price = prices.median()

        # Detect outliers (prices beyond 2 std dev)
        outliers = prices[(prices > mean_price + 2 * std_price) |
                         (prices < mean_price - 2 * std_price)]

        # Price ranges by category
        price_by_category = df.groupby("RUBRO")["PRECIO_TOTAL"].agg([
            "min", "mean", "max", "std"
        ]).round(2)

        return {
            "price_stats": {
                "mean": float(mean_price),
                "median": float(median_price),
                "std": float(std_price),
                "min": float(prices.min()),
                "max": float(prices.max())
            },
            "outlier_count": len(outliers),
            "outlier_percentage": round((len(outliers) / len(prices)) * 100, 2),
            "price_by_category": price_by_category.to_dict("index")
        }

    def volume_analysis(self) -> Dict:
        """Analyze quantity/volume patterns.

        Returns:
            Dictionary with volume insights.
        """
        df = self.df.copy()
        df.loc[:, "CANTIDAD"] = pd.to_numeric(df["CANTIDAD"], errors="coerce")

        quantities = df["CANTIDAD"].dropna()

        # Handle empty quantities
        if len(quantities) == 0:
            return {
                "total_volume": 0,
                "volume_stats": {
                    "mean": 0,
                    "std": 0,
                    "min": 0,
                    "max": 0
                },
                "volume_by_category": {},
                "top_volume_descriptions": {}
            }

        volume_by_category = df.groupby("RUBRO")["CANTIDAD"].agg([
            "count", "sum", "mean", "std"
        ]).round(2)

        volume_by_desc = df.groupby("DESC_RUBRO")["CANTIDAD"].agg([
            "count", "sum", "mean"
        ]).round(2).sort_values("sum", ascending=False).head(10)

        return {
            "total_volume": float(quantities.sum()),
            "volume_stats": {
                "mean": float(quantities.mean()),
                "std": float(quantities.std()),
                "min": float(quantities.min()),
                "max": float(quantities.max())
            },
            "volume_by_category": volume_by_category.to_dict("index"),
            "top_volume_descriptions": volume_by_desc.to_dict("index")
        }

    def correlation_analysis(self) -> Dict:
        """Analyze correlations between numeric columns.

        Returns:
            Dictionary with correlation insights.
        """
        df = self.df.copy()

        # Select numeric columns
        numeric_cols = ["PRECIO_UNI", "PRECIO_TOTAL", "CANTIDAD", "MONTO_IVA"]
        numeric_df = df[numeric_cols].apply(pd.to_numeric, errors="coerce")

        # Calculate correlations
        correlations = numeric_df.corr().round(3)

        return {
            "correlations": correlations.to_dict(),
            "price_quantity_correlation": float(
                numeric_df["PRECIO_TOTAL"].corr(numeric_df["CANTIDAD"])
            ),
            "price_iva_correlation": float(
                numeric_df["PRECIO_TOTAL"].corr(numeric_df["MONTO_IVA"])
            )
        }

    def anomaly_detection(self) -> Dict:
        """Detect anomalies in the data.

        Returns:
            Dictionary with anomaly insights.
        """
        df = self.df.copy()
        df.loc[:, "PRECIO_TOTAL"] = pd.to_numeric(df["PRECIO_TOTAL"], errors="coerce")

        anomalies = {
            "zero_price": len(df[df["PRECIO_TOTAL"] == 0]),
            "null_values": df.isnull().sum().to_dict(),
            "duplicate_records": df.duplicated().sum(),
            "duplicate_percentage": round(
                (df.duplicated().sum() / len(df)) * 100, 2
            )
        }

        # Negative prices
        negative_prices = len(df[df["PRECIO_TOTAL"] < 0])
        anomalies["negative_prices"] = negative_prices

        # Categories with inconsistent naming
        unique_descriptions = df["DESC_RUBRO"].nunique()
        anomalies["unique_descriptions"] = unique_descriptions

        return anomalies

    def generate_report(self) -> str:
        """Generate comprehensive pattern analysis report.

        Returns:
            Formatted text report.
        """
        report = []
        report.append("=" * 70)
        report.append("PATTERN ANALYSIS REPORT - Invoice Data")
        report.append("=" * 70)
        report.append("")

        # Monthly Trends
        report.append("MONTHLY TRENDS")
        report.append("-" * 70)
        monthly = self.monthly_trends()
        report.append(f"📅 Months analyzed: {monthly['month_count']}")
        report.append(f"📈 Top month: {monthly['top_month']} (highest revenue)")
        report.append(f"📉 Lowest month: {monthly['lowest_month']} (lowest revenue)")
        report.append(f"💰 Average monthly revenue: ${monthly['avg_monthly_revenue']:,.2f}")
        report.append("")

        # Category Analysis
        report.append("CATEGORY ANALYSIS")
        report.append("-" * 70)
        category = self.category_trends()
        report.append(f"🏷️  Total categories: {category['category_count']}")
        report.append(f"🔝 Dominant category: {category['dominant_category']}")
        report.append(f"📊 Categories: {', '.join(category['categories'])}")
        report.append("")

        # Price Analysis
        report.append("PRICE PATTERNS")
        report.append("-" * 70)
        price = self.price_analysis()
        report.append(
            f"💵 Average price: ${price['price_stats']['mean']:,.2f}"
        )
        report.append(
            f"📊 Median price: ${price['price_stats']['median']:,.2f}"
        )
        report.append(
            f"📈 Price range: ${price['price_stats']['min']:,.2f} - "
            f"${price['price_stats']['max']:,.2f}"
        )
        report.append(f"⚠️  Outliers detected: {price['outlier_count']:,} "
                     f"({price['outlier_percentage']}%)")
        report.append("")

        # Volume Analysis
        report.append("VOLUME PATTERNS")
        report.append("-" * 70)
        volume = self.volume_analysis()
        report.append(f"📦 Total volume: {volume['total_volume']:,.0f} units")
        report.append(
            f"📊 Average quantity per line: {volume['volume_stats']['mean']:.2f}"
        )
        report.append("")

        # Anomalies
        report.append("ANOMALIES DETECTED")
        report.append("-" * 70)
        anomalies = self.anomaly_detection()
        report.append(f"⚠️  Zero-price records: {anomalies['zero_price']:,}")
        report.append(f"⚠️  Negative prices: {anomalies['negative_prices']}")
        report.append(f"⚠️  Duplicate records: {anomalies['duplicate_records']:,} "
                     f"({anomalies['duplicate_percentage']}%)")
        report.append(f"⚠️  Null values by column:")
        for col, count in list(anomalies['null_values'].items())[:5]:
            if count > 0:
                report.append(f"    - {col}: {count:,}")
        report.append("")

        # Correlations
        report.append("CORRELATIONS")
        report.append("-" * 70)
        corr = self.correlation_analysis()
        report.append(f"📊 Price vs Quantity: {corr['price_quantity_correlation']:.3f}")
        report.append(f"📊 Price vs IVA: {corr['price_iva_correlation']:.3f}")
        report.append("")

        report.append("=" * 70)

        return "\n".join(report)

    def compare_with(self, other: "PatternAnalyzer") -> Dict:
        """Compare this period's patterns with another period.

        Args:
            other: Another PatternAnalyzer instance to compare with.

        Returns:
            Dictionary with comparison metrics.
        """
        self_metrics = self.price_analysis()
        other_metrics = other.price_analysis()

        self_revenue = self.df["PRECIO_TOTAL"].astype(float).sum()
        other_revenue = other.df["PRECIO_TOTAL"].astype(float).sum()
        revenue_change = ((self_revenue - other_revenue) / other_revenue * 100) if other_revenue != 0 else 0

        self_records = len(self.df)
        other_records = len(other.df)
        records_change = ((self_records - other_records) / other_records * 100) if other_records != 0 else 0

        return {
            "revenue_comparison": {
                "self": float(self_revenue),
                "other": float(other_revenue),
                "change": round(revenue_change, 1),
                "direction": "↑" if revenue_change > 0 else "↓"
            },
            "records_comparison": {
                "self": self_records,
                "other": other_records,
                "change": round(records_change, 1),
                "direction": "↑" if records_change > 0 else "↓"
            },
            "price_comparison": {
                "self_avg": self_metrics["price_stats"]["mean"],
                "other_avg": other_metrics["price_stats"]["mean"],
                "change": round((self_metrics["price_stats"]["mean"] - other_metrics["price_stats"]["mean"]) / other_metrics["price_stats"]["mean"] * 100, 1) if other_metrics["price_stats"]["mean"] > 0 else 0
            }
        }

    def get_summary_stats(self) -> Dict:
        """Get concise summary statistics for quick reporting.

        Returns:
            Dictionary with key metrics.
        """
        df = self.df.copy()
        df.loc[:, "PRECIO_TOTAL"] = pd.to_numeric(df["PRECIO_TOTAL"], errors="coerce")

        prices = df["PRECIO_TOTAL"].dropna()
        records = len(df)
        invoices = df["FACTURA"].nunique()

        return {
            "records": records,
            "invoices": invoices,
            "revenue": float(prices.sum()),
            "avg_price": float(prices.mean()),
            "median_price": float(prices.median()),
            "lines_per_invoice": records / invoices if invoices > 0 else 0,
            "categories": df["RUBRO"].nunique(),
            "dominant_category": df["RUBRO"].value_counts().idxmax() if not df.empty else "—",
        }
