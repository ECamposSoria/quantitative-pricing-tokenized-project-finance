import numpy as np

def compute_dscr(cfads: np.ndarray,
                 debt_service: np.ndarray) -> np.ndarray:
    """
    DSCR_t = CFADS_t / ServicioDeuda_t. :contentReference[oaicite:15]{index=15}
    ServicioDeuda_t = Intereses_t + Amortización_t.
    """
    # evitar división por cero
    with np.errstate(divide="ignore", invalid="ignore"):
        dscr = np.where(debt_service > 0, cfads / debt_service, np.inf)
    return dscr


def present_value(cashflows: np.ndarray, r: float) -> float:
    """
    Valor Presente Neto simple, usada como building block
    para LLCR y PLCR. :contentReference[oaicite:16]{index=16}
    """
    T = np.arange(len(cashflows))
    disc = 1.0 / (1.0 + r) ** T
    return float(np.sum(cashflows * disc))


def compute_llcr(cfads_future: np.ndarray,
                 debt_outstanding: float,
                 discount_rate: float) -> float:
    """
    LLCR = VP(CFADS desde t hasta maturity deuda) / DeudaRestante_t. :contentReference[oaicite:17]{index=17}
    """
    vp = present_value(cfads_future, discount_rate)
    return vp / debt_outstanding if debt_outstanding > 0 else np.inf


def compute_plcr(cfads_full: np.ndarray,
                 debt_initial: float,
                 discount_rate: float) -> float:
    """
    PLCR = VP(CFADS vida total del proyecto) / DeudaInicial. :contentReference[oaicite:18]{index=18}
    """
    vp = present_value(cfads_full, discount_rate)
    return vp / debt_initial if debt_initial > 0 else np.inf
