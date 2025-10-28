import numpy as np

def implied_asset_value(cfads_path: np.ndarray, discount_rate: float) -> float:
    """
    Aproxima V_t como VP de CFADS futuros simulados (Cap. 3.2.4.2). :contentReference[oaicite:19]{index=19}
    """
    T = np.arange(len(cfads_path))
    disc = 1.0 / (1.0 + discount_rate) ** T
    return float(np.sum(cfads_path * disc))


def merton_default_flag(cfads_path: np.ndarray,
                        debt_outstanding: float,
                        discount_rate: float) -> int:
    """
    Default estructural si V_t < Deuda_t (Cap. 3.2.4.4). :contentReference[oaicite:20]{index=20}
    Returns 1 si default, 0 si no.
    """
    v = implied_asset_value(cfads_path, discount_rate)
    return 1 if v < debt_outstanding else 0
