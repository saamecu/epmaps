"""Data analysis module for invoice data comparison and statistics."""

from typing import Optional
import pandas as pd
import numpy as np

from src.data_reader import DataReader


class DataAnalyzer:
    """Analyzes invoice data with focus on month-to-month comparisons.

    This class provides methods to analyze invoice data, calculate statistics,
    and compare data across different time periods (months).

    Attributes:
        df: DataFrame containing the invoice data.
    """

    def __init__(self, df: pd.DataFrame) -> None:
        """Initialize DataAnalyzer with a DataFrame.

        Args:
            df: DataFrame containing invoice data with at least FACTURA column.

        Raises:
            ValueError: If DataFrame is empty.
            TypeError: If input is not a DataFrame.
        """
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame")

        if df.empty:
            raise ValueError("DataFrame cannot be empty")

        self.df = df.copy()

    @classmethod
    def from_file(cls, file_path: str, chunksize: Optional[int] = None):
        """Create DataAnalyzer from a data file.

        Args:
            file_path: Path to the data file.
            chunksize: If provided, data is processed in chunks and aggregated.

        Returns:
            DataAnalyzer instance with loaded data.
        """
        reader = DataReader(file_path)

        if chunksize:
            dfs = [chunk for chunk in reader.read_chunks(chunksize)]
            df = pd.concat(dfs, ignore_index=True)
        else:
            df = reader.read_full()

        return cls(df)

    def extract_month(self, factura_column: str = "FACTURA") -> pd.DataFrame:
        """Extract month information from invoice numbers.

        Assumes invoice format: MANDT-TIPDOC-NUMERO where TIPDOC indicates month.
        Example: 001-012-057647312 -> month 012

        Args:
            factura_column: Name of the invoice column. Defaults to 'FACTURA'.

        Returns:
            DataFrame with original data plus 'MONTH' column.
        """
        df = self.df.copy()

        if factura_column not in df.columns:
            raise ValueError(f"Column '{factura_column}' not found in DataFrame")

        # Extract month from invoice format: MANDT-TIPDOC-NUMERO
        df.loc[:, "MONTH"] = df[factura_column].str.split("-").str[1]

        return df

    def get_summary_stats(
        self, value_column: str = "PRECIO_TOTAL"
    ) -> dict:
        """Calculate summary statistics for invoice amounts.

        Args:
            value_column: Column to calculate statistics on.
                Defaults to 'PRECIO_TOTAL'.

        Returns:
            Dictionary with summary statistics.

        Raises:
            ValueError: If value_column not found in DataFrame.
        """
        if value_column not in self.df.columns:
            raise ValueError(f"Column '{value_column}' not found")

        data = pd.to_numeric(self.df[value_column], errors="coerce").dropna()

        return {
            "count": len(data),
            "sum": float(data.sum()),
            "mean": float(data.mean()),
            "median": float(data.median()),
            "std": float(data.std()),
            "min": float(data.min()),
            "max": float(data.max()),
        }

    def group_by_column(
        self,
        group_column: str,
        value_column: str = "PRECIO_TOTAL",
        aggregation: str = "sum",
    ) -> pd.DataFrame:
        """Group data by a column and aggregate values.

        Args:
            group_column: Column to group by (e.g., 'RUBRO').
            value_column: Column to aggregate. Defaults to 'PRECIO_TOTAL'.
            aggregation: Type of aggregation ('sum', 'mean', 'count', 'min', 'max').
                Defaults to 'sum'.

        Returns:
            DataFrame with grouped results.

        Raises:
            ValueError: If columns don't exist or aggregation is invalid.
        """
        if group_column not in self.df.columns:
            raise ValueError(f"Column '{group_column}' not found")

        if value_column not in self.df.columns:
            raise ValueError(f"Column '{value_column}' not found")

        valid_aggs = ["sum", "mean", "count", "min", "max"]
        if aggregation not in valid_aggs:
            raise ValueError(
                f"Invalid aggregation '{aggregation}'. "
                f"Must be one of: {valid_aggs}"
            )

        df = self.df.copy()
        df.loc[:, value_column] = pd.to_numeric(
            df[value_column], errors="coerce"
        )

        result = df.groupby(group_column)[value_column].agg(aggregation)
        return result.reset_index().rename(
            columns={value_column: aggregation.upper()}
        )

    def compare_periods(
        self,
        period_column: str,
        period1: str,
        period2: str,
        value_column: str = "PRECIO_TOTAL",
    ) -> dict:
        """Compare values between two periods.

        Args:
            period_column: Column containing period identifiers.
            period1: First period to compare.
            period2: Second period to compare.
            value_column: Column with values to compare.

        Returns:
            Dictionary with comparison results including:
            - period1_total, period2_total: Totals for each period
            - difference: Absolute difference
            - percentage_change: Percentage change from period1 to period2

        Raises:
            ValueError: If periods or columns don't exist.
        """
        if period_column not in self.df.columns:
            raise ValueError(f"Column '{period_column}' not found")

        if value_column not in self.df.columns:
            raise ValueError(f"Column '{value_column}' not found")

        df = self.df.copy()
        df.loc[:, value_column] = pd.to_numeric(
            df[value_column], errors="coerce"
        )

        # Filter by periods
        df1 = df[df[period_column].astype(str) == str(period1)][value_column]
        df2 = df[df[period_column].astype(str) == str(period2)][value_column]

        if df1.empty:
            raise ValueError(f"No data found for {period_column}={period1}")
        if df2.empty:
            raise ValueError(f"No data found for {period_column}={period2}")

        total1 = float(df1.sum())
        total2 = float(df2.sum())
        difference = total2 - total1
        percentage_change = (difference / total1 * 100) if total1 != 0 else 0

        return {
            "period1": str(period1),
            "period2": str(period2),
            "period1_total": total1,
            "period2_total": total2,
            "difference": difference,
            "percentage_change": round(percentage_change, 2),
        }

    def top_by_value(
        self,
        group_column: str,
        value_column: str = "PRECIO_TOTAL",
        n: int = 10,
    ) -> pd.DataFrame:
        """Get top N groups by value.

        Args:
            group_column: Column to group by.
            value_column: Column with values to sort by.
            n: Number of top results. Defaults to 10.

        Returns:
            DataFrame with top N groups sorted by value descending.

        Raises:
            ValueError: If columns don't exist or n is invalid.
        """
        if n <= 0:
            raise ValueError("n must be positive")

        grouped = self.group_by_column(
            group_column, value_column, aggregation="sum"
        )
        return grouped.sort_values("SUM", ascending=False).head(n)

    def get_row_count(self) -> int:
        """Get total number of rows in the data.

        Returns:
            Number of data rows.
        """
        return len(self.df)

    def get_columns(self) -> list[str]:
        """Get list of all column names.

        Returns:
            List of column names in the DataFrame.
        """
        return self.df.columns.tolist()
