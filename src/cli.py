"""Command-line interface for EPMaps invoice data analysis."""

from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from src.data_reader import DataReader
from src.analyzer import DataAnalyzer


console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="epmaps")
def cli():
    """EPMaps - Invoice Data Analysis and Comparison Tool.

    Analyze and compare invoice data across multiple time periods.
    """
    pass


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
def info(file_path: str) -> None:
    """Display information about a data file.

    Prints file metadata including size, column names, and row count.
    """
    try:
        reader = DataReader(file_path)
        file_info = reader.get_file_info()
        columns = reader.get_columns()

        console.print("\n[bold cyan]File Information[/bold cyan]")
        console.print(f"Path: {file_info['path']}")
        console.print(f"Size: {file_info['size_mb']} MB")
        console.print(f"Columns: {len(columns)}")
        console.print(f"Columns: {', '.join(columns)}")
        console.print()

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort()


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "-c",
    "--column",
    default="PRECIO_TOTAL",
    help="Column to calculate statistics on.",
)
def stats(file_path: str, column: str) -> None:
    """Display summary statistics for a data file.

    Shows count, sum, mean, median, std, min, and max values.
    """
    try:
        analyzer = DataAnalyzer.from_file(file_path)

        if column not in analyzer.get_columns():
            console.print(f"[bold red]Error:[/bold red] Column '{column}' not found")
            raise click.Abort()

        stats_dict = analyzer.get_summary_stats(value_column=column)

        console.print(f"\n[bold cyan]Statistics for {column}[/bold cyan]")
        table = Table(show_header=False, box=None)
        for key, value in stats_dict.items():
            formatted_value = f"{value:,.2f}" if isinstance(value, float) else str(value)
            table.add_row(f"[cyan]{key.upper()}[/cyan]", formatted_value)
        console.print(table)
        console.print()

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort()


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "-g",
    "--group-by",
    default="RUBRO",
    help="Column to group by.",
)
@click.option(
    "-v",
    "--value-column",
    default="PRECIO_TOTAL",
    help="Column with values to aggregate.",
)
@click.option(
    "-a",
    "--aggregation",
    type=click.Choice(["sum", "mean", "count", "min", "max"]),
    default="sum",
    help="Aggregation method.",
)
def group(file_path: str, group_by: str, value_column: str, aggregation: str) -> None:
    """Group and aggregate data by a column.

    Display data grouped by specified column with chosen aggregation.
    """
    try:
        analyzer = DataAnalyzer.from_file(file_path)
        result = analyzer.group_by_column(group_by, value_column, aggregation)

        console.print(
            f"\n[bold cyan]Data Grouped by {group_by} "
            f"({aggregation.upper()})[/bold cyan]"
        )
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column(group_by)
        table.add_column(f"{aggregation.upper()}")

        for _, row in result.iterrows():
            table.add_row(str(row[group_by]), f"{row[aggregation.upper()]:,.2f}")

        console.print(table)
        console.print()

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort()


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "-g",
    "--group-by",
    default="RUBRO",
    help="Column to group by.",
)
@click.option(
    "-v",
    "--value-column",
    default="PRECIO_TOTAL",
    help="Column with values to sort by.",
)
@click.option(
    "-n",
    "--number",
    type=int,
    default=10,
    help="Number of top items to display.",
)
def top(file_path: str, group_by: str, value_column: str, number: int) -> None:
    """Display top N items by value.

    Shows the top N groups sorted by value in descending order.
    """
    try:
        if number <= 0:
            console.print("[bold red]Error:[/bold red] Number must be positive")
            raise click.Abort()

        analyzer = DataAnalyzer.from_file(file_path)
        result = analyzer.top_by_value(group_by, value_column, n=number)

        console.print(f"\n[bold cyan]Top {number} {group_by} by {value_column}[/bold cyan]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Rank", style="cyan")
        table.add_column(group_by)
        table.add_column(f"Total", justify="right")

        for idx, (_, row) in enumerate(result.iterrows(), 1):
            table.add_row(str(idx), str(row[group_by]), f"${row['SUM']:,.2f}")

        console.print(table)
        console.print()

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort()


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.argument("period1", type=str)
@click.argument("period2", type=str)
@click.option(
    "-p",
    "--period-column",
    default="MONTH",
    help="Column containing period identifiers.",
)
@click.option(
    "-v",
    "--value-column",
    default="PRECIO_TOTAL",
    help="Column with values to compare.",
)
def compare(
    file_path: str,
    period1: str,
    period2: str,
    period_column: str,
    value_column: str,
) -> None:
    """Compare data between two periods.

    Shows totals, difference, and percentage change between periods.
    """
    try:
        analyzer = DataAnalyzer.from_file(file_path)
        result = analyzer.compare_periods(period_column, period1, period2, value_column)

        console.print(f"\n[bold cyan]Period Comparison: {period1} vs {period2}[/bold cyan]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Period")
        table.add_column("Total")

        table.add_row(f"{result['period1']}", f"${result['period1_total']:,.2f}")
        table.add_row(f"{result['period2']}", f"${result['period2_total']:,.2f}")

        console.print(table)

        difference = result["difference"]
        pct_change = result["percentage_change"]
        color = "green" if difference >= 0 else "red"

        console.print(f"\n[cyan]Difference:[/cyan] [{color}]${difference:,.2f}[/{color}]")
        console.print(f"[cyan]Percentage Change:[/cyan] [{color}]{pct_change:+.2f}%[/{color}]")
        console.print()

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort()


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    help="Output file path for the report (optional).",
)
def report(file_path: str, output: Optional[str]) -> None:
    """Generate a comprehensive analysis report.

    Creates a summary report with key statistics and insights.
    """
    try:
        analyzer = DataAnalyzer.from_file(file_path)
        reader = DataReader(file_path)

        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("EPMaps - Invoice Data Analysis Report")
        report_lines.append("=" * 60)
        report_lines.append("")

        # File info
        file_info = reader.get_file_info()
        report_lines.append(f"File: {file_info['path']}")
        report_lines.append(f"Size: {file_info['size_mb']} MB")
        report_lines.append(f"Total Rows: {analyzer.get_row_count()}")
        report_lines.append("")

        # Summary stats
        report_lines.append("Summary Statistics (PRECIO_TOTAL):")
        report_lines.append("-" * 40)
        stats = analyzer.get_summary_stats("PRECIO_TOTAL")
        report_lines.append(f"Total: ${stats['sum']:,.2f}")
        report_lines.append(f"Average: ${stats['mean']:,.2f}")
        report_lines.append(f"Median: ${stats['median']:,.2f}")
        report_lines.append(f"Std Dev: ${stats['std']:,.2f}")
        report_lines.append(f"Min: ${stats['min']:,.2f}")
        report_lines.append(f"Max: ${stats['max']:,.2f}")
        report_lines.append("")

        # Top by rubro
        report_lines.append("Top 5 Rubros by Total:")
        report_lines.append("-" * 40)
        top_rubros = analyzer.top_by_value("RUBRO", n=5)
        for idx, (_, row) in enumerate(top_rubros.iterrows(), 1):
            report_lines.append(
                f"{idx}. {row['RUBRO']}: ${row['SUM']:,.2f}"
            )
        report_lines.append("")
        report_lines.append("=" * 60)

        report_text = "\n".join(report_lines)
        console.print(report_text)

        if output:
            Path(output).write_text(report_text)
            console.print(f"\n[green]Report saved to: {output}[/green]\n")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort()


if __name__ == "__main__":
    cli()
