import pandas as pd
import numpy as np
from .params import ProjectParams, TrancheParams

def load_project_data(base_path: str):
    """
    Carga CSVs del caso LEO IoT (data/input/leo_iot/).
    Estos archivos son la base empírica del modelo (Cap. 2). :contentReference[oaicite:21]{index=21}

    Esperado:
    - project_params.csv
    - tranches.csv
    - rcapex_schedule.csv
    - revenue_projection.csv
    """
    # placeholders con estructura mínima
    project_df = pd.read_csv(f"{base_path}/project_params.csv")
    tranches_df = pd.read_csv(f"{base_path}/tranches.csv")
    rev_df = pd.read_csv(f"{base_path}/revenue_projection.csv")
    opex_df = pd.read_csv(f"{base_path}/opex_projection.csv")
    capex_df = pd.read_csv(f"{base_path}/rcapex_schedule.csv")
    wc_df = pd.read_csv(f"{base_path}/working_capital.csv")
    taxes_df = pd.read_csv(f"{base_path}/taxes.csv")
    debt_sched = pd.read_csv(f"{base_path}/debt_schedule.csv")

    years = project_df["year"].to_numpy()
    p = ProjectParams(
        timeline_years=years,
        revenue=rev_df["revenue"].to_numpy(),
        opex=opex_df["opex"].to_numpy(),
        capex_maint=capex_df["capex_maint"].to_numpy(),
        taxes=taxes_df["taxes"].to_numpy(),
        delta_wc=wc_df["delta_wc"].to_numpy(),
        debt_schedule=debt_sched,
        tax_rate=project_df["tax_rate"].iloc[0],
        wacc=project_df["wacc"].iloc[0],
    )

    tranches = [
        TrancheParams(
            name=row["name"],
            notional=row["notional"],
            rate_spread=row["rate_spread_bps"] / 10000.0,
            lgd=row["lgd"],
            priority=row["priority"],
        )
        for _, row in tranches_df.iterrows()
    ]

    return p, tranches
