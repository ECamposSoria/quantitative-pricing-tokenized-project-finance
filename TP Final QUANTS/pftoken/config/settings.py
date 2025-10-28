from dataclasses import dataclass

@dataclass
class ModelSettings:
    """
    Parámetros globales / flags del motor.

    - base_currency: 'USD', 'USDC', 'CBDC' (Cap. 2.12.1). :contentReference[oaicite:6]{index=6}
    - discount_curve: nombre de la curva base libre de riesgo usada para descontar
      (SOFR, swap USD, tasa CBDC del banco central). Reisin (2025). :contentReference[oaicite:7]{index=7}
    - n_sims: número de trayectorias Monte Carlo (5k-10k recomendado). :contentReference[oaicite:8]{index=8}
    - horizon_years: vida relevante del proyecto / deuda.
    """
    base_currency: str = "USD"
    discount_curve: str = "SOFR"
    n_sims: int = 5000
    horizon_years: int = 12
