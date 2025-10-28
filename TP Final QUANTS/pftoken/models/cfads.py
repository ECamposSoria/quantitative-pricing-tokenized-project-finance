import numpy as np
from dataclasses import dataclass
from .params import ProjectParams

@dataclass
class CFADSResult:
    cfads: np.ndarray
    ebitda: np.ndarray

class CFADSModel:
    """
    Calcula CFADS año a año.

    Definición en el TP:
    CFADS_t = EBITDA_t - Impuestos_t - CAPEX_mantenimiento_t - ΔWC_t. :contentReference[oaicite:13]{index=13}

    EBITDA_t = Revenue_t - OPEX_t. :contentReference[oaicite:14]{index=14}
    """

    def __init__(self, params: ProjectParams):
        self.p = params

    def run(self) -> CFADSResult:
        revenue = self.p.revenue
        opex = self.p.opex
        capex = self.p.capex_maint
        taxes = self.p.taxes
        d_wc = self.p.delta_wc

        ebitda = revenue - opex
        cfads = ebitda - taxes - capex - d_wc

        return CFADSResult(cfads=cfads, ebitda=ebitda)
