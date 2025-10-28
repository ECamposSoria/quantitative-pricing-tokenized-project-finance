from dataclasses import dataclass
import numpy as np
import pandas as pd

@dataclass
class TrancheParams:
    """
    Parámetros financieros por tramo de deuda.
    - name: 'senior' | 'mezz' | 'sub'
    - notional: monto inicial
    - rate_spread: spread sobre la curva base libre de riesgo (Cap. 3.4.8). :contentReference[oaicite:9]{index=9}
    - lgd: Loss Given Default base del tramo (Cap. 4.3.2). :contentReference[oaicite:10]{index=10}
    - priority: orden en el waterfall (1 = cobra primero). :contentReference[oaicite:11]{index=11}
    """
    name: str
    notional: float
    rate_spread: float
    lgd: float
    priority: int


@dataclass
class ProjectParams:
    """
    Parámetros determinísticos del caso base del proyecto satelital LEO IoT.

    Estos insumos vienen típicamente de data/input/leo_iot/*.csv:
    - revenue_projection
    - opex_projection
    - capex / rcapex calendario reposición satelital
    - taxes
    - working capital ΔWC
    - amortización deuda calendarizada por tramo

    Todo esto alimenta CFADS, waterfall, ratios DSCR/LLCR/PLCR (Cap. 1.4). :contentReference[oaicite:12]{index=12}
    """
    timeline_years: np.ndarray        # e.g. np.arange(1, 13)
    revenue: np.ndarray               # ingresos esperados
    opex: np.ndarray                  # costos operativos
    capex_maint: np.ndarray           # RCAPEX / mantenimiento satelital
    taxes: np.ndarray                 # impuestos proyectados
    delta_wc: np.ndarray              # variación capital de trabajo
    debt_schedule: pd.DataFrame       # calendario pagos intereses / capital por tramo
    tax_rate: float = 0.0
    wacc: float = 0.1
