"""
Script para generar el gráfico de la Curva Zero USD desde datos FRED.
Ejecutar: python scripts/plot_zero_curve.py
El gráfico se guarda en outputs/zero_curve_chart.png
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Datos de FRED (DGS series, 20-nov-2025)
maturities = np.array([1, 2, 3, 5, 7, 10, 15, 20, 30])
zero_rates = np.array([3.65, 3.55, 3.56, 3.68, 3.87, 4.10, 4.39, 4.68, 4.73])  # en %

# Calcular Discount Factors: DF(t) = (1 + r)^(-t)
discount_factors = (1 + zero_rates / 100) ** (-maturities)

# Interpolación para curva suave
maturities_smooth = np.linspace(0.5, 30, 100)
zero_rates_smooth = np.interp(maturities_smooth, maturities, zero_rates)

# Bandas de shock ±50 bps
shock_bps = 50
upper_band = zero_rates_smooth + shock_bps / 100
lower_band = zero_rates_smooth - shock_bps / 100

# Crear figura con dos ejes Y
fig, ax1 = plt.subplots(figsize=(12, 7))

# Color scheme profesional
color_zero = '#1f4e79'  # azul oscuro
color_df = '#2e7d32'    # verde oscuro
color_band = '#bbdefb'  # azul claro

# Eje izquierdo: Zero Rate
ax1.set_xlabel('Madurez (Años)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Zero Rate (%)', color=color_zero, fontsize=12, fontweight='bold')

# Banda de shock
ax1.fill_between(maturities_smooth, lower_band, upper_band,
                  alpha=0.3, color=color_band, label='Banda de shock ±50 bps')

# Curva zero (línea principal)
ax1.plot(maturities_smooth, zero_rates_smooth, color=color_zero,
         linewidth=2.5, label='Zero Rate (FRED)', zorder=5)

# Nodos de bootstrapping
ax1.scatter(maturities, zero_rates, color=color_zero, s=80,
            edgecolors='white', linewidths=2, zorder=10, label='Nodos observados')

ax1.tick_params(axis='y', labelcolor=color_zero)
ax1.set_ylim(2.5, 5.5)
ax1.set_xlim(0, 32)

# Eje derecho: Discount Factor
ax2 = ax1.twinx()
ax2.set_ylabel('Discount Factor', color=color_df, fontsize=12, fontweight='bold')

# Curva de discount factors
df_smooth = (1 + zero_rates_smooth / 100) ** (-maturities_smooth)
ax2.plot(maturities_smooth, df_smooth, color=color_df,
         linewidth=2, linestyle='--', label='Discount Factor', zorder=4)

# Nodos de DF
ax2.scatter(maturities, discount_factors, color=color_df, s=60,
            marker='s', edgecolors='white', linewidths=1.5, zorder=9)

ax2.tick_params(axis='y', labelcolor=color_df)
ax2.set_ylim(0, 1.1)

# Título
plt.title('Curva Zero USD - Fuente: FRED (DGS Series, Nov 2025)\nHorizonte del Proyecto: 15 Años',
          fontsize=14, fontweight='bold', pad=20)

# Línea vertical en año 15 (horizonte del proyecto)
ax1.axvline(x=15, color='red', linestyle=':', alpha=0.7, linewidth=1.5)
ax1.annotate('Horizonte\n15 años', xy=(15, 3.0), fontsize=9,
             ha='center', color='red', alpha=0.8)

# Leyenda combinada
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right',
           fontsize=10, framealpha=0.95)

# Grid
ax1.grid(True, alpha=0.3, linestyle='-')
ax1.set_axisbelow(True)

# Anotaciones de tasas clave
for i, (m, r) in enumerate(zip(maturities, zero_rates)):
    if m in [1, 5, 10, 15]:  # Solo mostrar algunos
        ax1.annotate(f'{r:.2f}%', xy=(m, r), xytext=(m+0.5, r+0.15),
                    fontsize=9, color=color_zero, fontweight='bold')

plt.tight_layout()

# Guardar
output_path = Path('outputs/zero_curve_chart.png')
output_path.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(output_path, dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none')
print(f"✅ Gráfico guardado en: {output_path}")

# También mostrar
plt.show()
