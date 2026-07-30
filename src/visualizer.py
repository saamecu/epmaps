"""Data visualization module for creating charts and graphs."""

from typing import Optional
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from src.analyzer import DataAnalyzer


class DataVisualizer:
    """Creates visualizations for invoice data analysis.

    This class provides methods to generate interactive charts using Plotly,
    including trend lines, bar charts, and comparison visualizations.
    """

    def __init__(self, analyzer: DataAnalyzer) -> None:
        """Initialize DataVisualizer with a DataAnalyzer instance.

        Args:
            analyzer: DataAnalyzer instance with data to visualize.

        Raises:
            TypeError: If analyzer is not a DataAnalyzer instance.
        """
        if not isinstance(analyzer, DataAnalyzer):
            raise TypeError("analyzer must be a DataAnalyzer instance")

        self.analyzer = analyzer
        self.df = analyzer.df

    @classmethod
    def from_file(cls, file_path: str):
        """Create DataVisualizer from a data file.

        Args:
            file_path: Path to the data file.

        Returns:
            DataVisualizer instance.
        """
        analyzer = DataAnalyzer.from_file(file_path)
        return cls(analyzer)

    def bar_chart_by_category(
        self,
        category_column: str = "RUBRO",
        value_column: str = "PRECIO_TOTAL",
        title: Optional[str] = None,
        n_top: int = 10,
    ) -> go.Figure:
        """Create a bar chart grouped by category.

        Args:
            category_column: Column to group by. Defaults to 'RUBRO'.
            value_column: Column with values to plot. Defaults to 'PRECIO_TOTAL'.
            title: Chart title (auto-generated if None).
            n_top: Number of top categories to display. Defaults to 10.

        Returns:
            Plotly Figure object.

        Raises:
            ValueError: If columns don't exist.
        """
        if category_column not in self.df.columns:
            raise ValueError(f"Column '{category_column}' not found")
        if value_column not in self.df.columns:
            raise ValueError(f"Column '{value_column}' not found")

        grouped = self.analyzer.top_by_value(
            category_column, value_column, n=n_top
        )

        if title is None:
            title = f"Top {n_top} {category_column} by {value_column}"

        fig = go.Figure(
            data=[
                go.Bar(
                    x=grouped[category_column],
                    y=grouped["SUM"],
                    marker=dict(color="rgba(55, 128, 191, 0.7)"),
                    text=grouped["SUM"].apply(lambda x: f"${x:,.0f}"),
                    textposition="auto",
                )
            ]
        )

        fig.update_layout(
            title=title,
            xaxis_title=category_column,
            yaxis_title=f"Total {value_column}",
            hovermode="x unified",
            template="plotly_white",
            height=500,
        )

        return fig

    def line_chart_trend(
        self,
        period_column: str = "MONTH",
        value_column: str = "PRECIO_TOTAL",
        title: Optional[str] = None,
    ) -> go.Figure:
        """Create a line chart showing trends over time/periods.

        Args:
            period_column: Column with period identifiers. Defaults to 'MONTH'.
            value_column: Column with values to plot. Defaults to 'PRECIO_TOTAL'.
            title: Chart title (auto-generated if None).

        Returns:
            Plotly Figure object.

        Raises:
            ValueError: If columns don't exist.
        """
        if period_column not in self.df.columns:
            raise ValueError(f"Column '{period_column}' not found")
        if value_column not in self.df.columns:
            raise ValueError(f"Column '{value_column}' not found")

        df = self.df.copy()
        df.loc[:, value_column] = pd.to_numeric(df[value_column], errors="coerce")

        # Aggregate by period
        trend_data = (
            df.groupby(period_column)[value_column]
            .sum()
            .reset_index()
            .sort_values(period_column)
        )

        if title is None:
            title = f"{value_column} Trend by {period_column}"

        fig = go.Figure(
            data=[
                go.Scatter(
                    x=trend_data[period_column].astype(str),
                    y=trend_data[value_column],
                    mode="lines+markers",
                    name=value_column,
                    line=dict(color="rgb(55, 128, 191)", width=3),
                    marker=dict(size=8),
                )
            ]
        )

        fig.update_layout(
            title=title,
            xaxis_title=period_column,
            yaxis_title=value_column,
            hovermode="x unified",
            template="plotly_white",
            height=500,
        )

        return fig

    def pie_chart_distribution(
        self,
        category_column: str = "RUBRO",
        value_column: str = "PRECIO_TOTAL",
        title: Optional[str] = None,
    ) -> go.Figure:
        """Create a pie chart showing distribution by category.

        Args:
            category_column: Column to group by. Defaults to 'RUBRO'.
            value_column: Column with values for distribution. Defaults to 'PRECIO_TOTAL'.
            title: Chart title (auto-generated if None).

        Returns:
            Plotly Figure object.

        Raises:
            ValueError: If columns don't exist.
        """
        if category_column not in self.df.columns:
            raise ValueError(f"Column '{category_column}' not found")
        if value_column not in self.df.columns:
            raise ValueError(f"Column '{value_column}' not found")

        grouped = self.analyzer.group_by_column(
            category_column, value_column, aggregation="sum"
        )

        if title is None:
            title = f"Distribution of {value_column} by {category_column}"

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=grouped[category_column],
                    values=grouped["SUM"],
                    hoverinfo="label+value+percent",
                )
            ]
        )

        fig.update_layout(
            title=title,
            template="plotly_white",
            height=500,
        )

        return fig

    def comparison_bar_chart(
        self,
        period_column: str = "MONTH",
        period1: str = None,
        period2: str = None,
        category_column: str = "RUBRO",
        value_column: str = "PRECIO_TOTAL",
        title: Optional[str] = None,
    ) -> go.Figure:
        """Create a comparison bar chart between two periods.

        Args:
            period_column: Column with period identifiers.
            period1: First period to compare.
            period2: Second period to compare.
            category_column: Column to group by. Defaults to 'RUBRO'.
            value_column: Column with values. Defaults to 'PRECIO_TOTAL'.
            title: Chart title (auto-generated if None).

        Returns:
            Plotly Figure object.

        Raises:
            ValueError: If periods or columns not found.
        """
        if period1 is None or period2 is None:
            raise ValueError("period1 and period2 must be specified")

        if period_column not in self.df.columns:
            raise ValueError(f"Column '{period_column}' not found")

        df = self.df.copy()
        df.loc[:, value_column] = pd.to_numeric(df[value_column], errors="coerce")

        # Filter by periods
        df1 = df[df[period_column].astype(str) == str(period1)]
        df2 = df[df[period_column].astype(str) == str(period2)]

        if df1.empty:
            raise ValueError(f"No data found for {period_column}={period1}")
        if df2.empty:
            raise ValueError(f"No data found for {period_column}={period2}")

        # Group by category
        group1 = (
            df1.groupby(category_column)[value_column]
            .sum()
            .reset_index()
            .sort_values(value_column, ascending=False)
            .head(10)
        )
        group2 = (
            df2.groupby(category_column)[value_column]
            .sum()
            .reset_index()
            .sort_values(value_column, ascending=False)
            .head(10)
        )

        # Get common categories
        categories = list(set(group1[category_column]) & set(group2[category_column]))
        if not categories:
            raise ValueError("No common categories between periods")

        group1_filtered = group1[group1[category_column].isin(categories)].set_index(
            category_column
        )
        group2_filtered = group2[group2[category_column].isin(categories)].set_index(
            category_column
        )

        if title is None:
            title = f"Comparison: {period_column} {period1} vs {period2}"

        fig = go.Figure(
            data=[
                go.Bar(name=f"Period {period1}", x=categories,
                       y=[group1_filtered.loc[c, value_column] if c in group1_filtered.index else 0 for c in categories]),
                go.Bar(name=f"Period {period2}", x=categories,
                       y=[group2_filtered.loc[c, value_column] if c in group2_filtered.index else 0 for c in categories]),
            ]
        )

        fig.update_layout(
            title=title,
            xaxis_title=category_column,
            yaxis_title=value_column,
            barmode="group",
            hovermode="x unified",
            template="plotly_white",
            height=500,
        )

        return fig

    def summary_dashboard(
        self,
        value_column: str = "PRECIO_TOTAL",
    ) -> go.Figure:
        """Create a summary dashboard with multiple visualizations.

        Args:
            value_column: Column with values. Defaults to 'PRECIO_TOTAL'.

        Returns:
            Plotly Figure object with subplots.
        """
        from plotly.subplots import make_subplots

        # Get data
        stats = self.analyzer.get_summary_stats(value_column)
        top_rubros = self.analyzer.top_by_value("RUBRO", value_column, n=5)

        # Create subplots
        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=(
                "Top 5 Rubros",
                "Total vs Average",
                "Distribution by Rubro",
                "Statistics",
            ),
            specs=[
                [{"type": "bar"}, {"type": "bar"}],
                [{"type": "pie"}, {"type": "indicator"}],
            ],
        )

        # Top rubros bar chart
        fig.add_trace(
            go.Bar(
                x=top_rubros["RUBRO"],
                y=top_rubros["SUM"],
                marker=dict(color="rgba(55, 128, 191, 0.7)"),
                name="Total",
            ),
            row=1,
            col=1,
        )

        # Total vs Average
        fig.add_trace(
            go.Bar(
                x=["Total", "Average"],
                y=[stats["sum"], stats["mean"]],
                marker=dict(color=["rgba(55, 128, 191, 0.7)", "rgba(50, 171, 96, 0.7)"]),
                name="Amount",
            ),
            row=1,
            col=2,
        )

        # Distribution pie chart
        fig.add_trace(
            go.Pie(
                labels=top_rubros["RUBRO"],
                values=top_rubros["SUM"],
                name="Distribution",
            ),
            row=2,
            col=1,
        )

        # Stats indicator
        fig.add_trace(
            go.Indicator(
                mode="number+delta",
                value=stats["sum"],
                title={"text": f"Total {value_column}"},
                domain={"x": [0, 1], "y": [0, 1]},
            ),
            row=2,
            col=2,
        )

        fig.update_layout(
            title_text="Invoice Data Summary Dashboard",
            height=900,
            showlegend=False,
            template="plotly_white",
        )

        return fig

    def save_chart(self, fig: go.Figure, file_path: str) -> None:
        """Save a chart to HTML file.

        Args:
            fig: Plotly Figure object to save.
            file_path: Path to save the HTML file.
        """
        fig.write_html(file_path)

    def show_chart(self, fig: go.Figure) -> None:
        """Display a chart in the browser.

        Args:
            fig: Plotly Figure object to display.
        """
        fig.show()
