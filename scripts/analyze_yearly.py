#!/usr/bin/env python3
"""Script to analyze yearly invoice data using YearlyAnalyzer."""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.yearly_analyzer import YearlyAnalyzer


def main():
    """Main entry point for yearly analysis."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/analyze_yearly.py <data_directory>")
        print("       python scripts/analyze_yearly.py /Volumes/My\\ Passport/EPMAPS/PROCESOS\\ COMERCIAL\\ FINANCIERA/Datos\\ ISU")
        sys.exit(1)

    data_dir = sys.argv[1]

    print(f"📊 Loading data from: {data_dir}")
    print("   Excluding V02 files...")

    # Load all data files
    analyzer = YearlyAnalyzer.from_directory(data_dir, exclude_v02=True)

    print(f"✓ Loaded {len(analyzer.months)} months of data")
    print()

    # Generate report
    report = analyzer.generate_yearly_report()
    print(report)

    # Save detailed analysis to JSON
    output_file = Path(data_dir).parent / "yearly_analysis.json"
    detailed = {
        "yearly_metrics": analyzer.yearly_metrics(),
        "monthly_changes": analyzer.monthly_changes(),
        "top_categories": analyzer.top_categories_yearly(),
        "price_evolution": analyzer.price_evolution(),
        "anomalies": analyzer.anomalies_by_month(),
    }

    with open(output_file, "w") as f:
        json.dump(detailed, f, indent=2, default=str)

    print(f"\n✓ Detailed analysis saved to: {output_file}")

    # Save text report
    report_file = Path(data_dir).parent / "yearly_analysis.txt"
    with open(report_file, "w") as f:
        f.write(report)

    print(f"✓ Text report saved to: {report_file}")


if __name__ == "__main__":
    main()
