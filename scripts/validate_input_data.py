#!/usr/bin/env python3
"""Validate input CSV files against the Proyecto LEO IOT.xlsx source of truth."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "input" / "leo_iot"
EXCEL_PATH = ROOT / "Proyecto LEO IOT.xlsx"


class ValidationError(AssertionError):
    """Custom assertion to distinguish validation failures."""


def load_workbook_data():
    if not EXCEL_PATH.exists():
        raise ValidationError(f"Missing Excel source: {EXCEL_PATH}")
    return load_workbook(EXCEL_PATH, data_only=True)


def validate_tranches(wb) -> None:
    """Ensure tranches.csv matches Excel principal and spread data."""
    df = pd.read_csv(DATA_DIR / "tranches.csv")
    ws = wb["Params (waterfall only)"]

    expected_principals = {
        "senior": ws["B2"].value * 1_000_000,
        "mezzanine": ws["B3"].value * 1_000_000,
        "subordinated": ws["B4"].value * 1_000_000,
    }

    for tranche, expected in expected_principals.items():
        actual = df.loc[df["tranche_name"] == tranche, "initial_principal"].item()
        if actual != expected:
            raise ValidationError(
                f"{tranche} principal mismatch: expected {expected}, got {actual}"
            )

    principal_sum = df["initial_principal"].sum()
    if principal_sum != 72_000_000:
        raise ValidationError(f"Principal sum mismatch: {principal_sum}")

    expected_spreads = {"senior": 100, "mezzanine": 350, "subordinated": 600}
    for tranche, spread in expected_spreads.items():
        actual_spread = df.loc[df["tranche_name"] == tranche, "spread_bps"].item()
        if actual_spread != spread:
            raise ValidationError(
                f"{tranche} spread mismatch: expected {spread}, got {actual_spread}"
            )

    print("✓ tranches.csv validated")


def validate_revenue_projection(wb) -> None:
    """Ensure revenue_projection.csv columns match the Excel CFADS sheet."""
    df = pd.read_csv(DATA_DIR / "revenue_projection.csv")
    ws = wb["CFADS"]

    excel_rows: List[Dict[str, float]] = []
    for row in ws.iter_rows(min_row=4, max_row=18, min_col=2, max_col=9, values_only=True):
        year, revenue, opex, maintenance, wc, tax, rcapex, cfads = row
        excel_rows.append(
            {
                "year": int(year),
                "revenue_gross": float(revenue),
                "opex": float(opex),
                "maintenance_opex": float(maintenance),
                "working_cap_change": float(wc),
                "tax_paid": float(tax),
                "capex": 0.0,
                "rcapex": float(rcapex),
                "cfads": float(cfads),
            }
        )

    excel_df = pd.DataFrame(excel_rows)
    merged = df.merge(excel_df, on="year", suffixes=("_csv", "_excel"))

    for column in ["revenue_gross", "opex", "maintenance_opex", "working_cap_change", "tax_paid", "rcapex", "cfads"]:
        diff = (merged[f"{column}_csv"] - merged[f"{column}_excel"]).abs().max()
        if diff > 0.01:
            raise ValidationError(f"{column} mismatch exceeds tolerance: {diff}")

    revenue_total = df["revenue_gross"].sum()
    if abs(revenue_total - 360.0) > 0.01:
        raise ValidationError(f"Revenue total mismatch: {revenue_total}")

    if abs(df["cfads"].sum() - 214.5) > 0.01:
        raise ValidationError("CFADS sum mismatch")

    print("✓ revenue_projection.csv validated")


def validate_debt_schedule(wb) -> None:
    """Validate debt_schedule.csv against Excel waterfall schedule."""
    df = pd.read_csv(DATA_DIR / "debt_schedule.csv")
    ws = wb["Debt Service"]

    excel_rows = []
    cols_map = {"senior": (2, 3), "mezzanine": (4, 5), "subordinated": (6, 7)}
    for row in ws.iter_rows(min_row=3, max_row=17, min_col=2, max_col=10, values_only=True):
        year = row[0]
        if year is None:
            continue
        year = int(year)
        for tranche, (interest_idx, principal_idx) in cols_map.items():
            interest = row[interest_idx] or 0.0
            principal = row[principal_idx] or 0.0
            excel_rows.append(
                {
                    "year": year,
                    "tranche_name": tranche,
                    "interest_due": int(round(interest * 1_000_000)),
                    "principal_due": int(round(principal * 1_000_000)),
                }
            )

    excel_df = pd.DataFrame(excel_rows)
    merged = df.merge(excel_df, on=["year", "tranche_name"], suffixes=("_csv", "_excel"))

    for column in ["interest_due", "principal_due"]:
        diff = (merged[f"{column}_csv"] - merged[f"{column}_excel"]).abs().max()
        if diff > 1:
            raise ValidationError(f"{column} mismatch: max diff {diff}")

    for year in range(1, 5):
        grace_principal = df.loc[df["year"] == year, "principal_due"].sum()
        if grace_principal != 0:
            raise ValidationError(f"Year {year} principal should be 0 (grace period)")

    total_principal = df["principal_due"].sum()
    if total_principal != 72_000_000:
        raise ValidationError(f"Principal repayment mismatch: {total_principal}")

    print("✓ debt_schedule.csv validated")


def main():
    try:
        wb = load_workbook_data()
        validate_tranches(wb)
        validate_revenue_projection(wb)
        validate_debt_schedule(wb)
        print("\n✓✓✓ ALL INPUT DATA VALIDATED ✓✓✓")
    except ValidationError as exc:
        print(f"\n✗✗✗ VALIDATION FAILED: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
