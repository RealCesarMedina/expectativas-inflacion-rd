"""Regenerar Figuras 2, 4 y 6 con las correcciones finales de estilo y bandas IC95%."""
import pandas as pd, numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import statsmodels.api as sm
import json

# Estilo consistente
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 10.5,
    'axes.titlesize': 12,
    'axes.labelsize': 10.5,
    'xtick.labelsize': 9.5,
    'ytick.labelsize': 9.5,
    'legend.fontsize': 9,
    'figure.dpi': 110,
    'savefig.dpi': 250,
    'savefig.bbox': 'tight',
    'figure.facecolor': 'white',
})
COLOR_OBS = '#C8102E'   # rojo
COLOR_EXP = '#1F4E8C'   # azul
COLOR_ERR = '#F2A900'   # amarillo

# Datos comunes
ds = pd.read_csv('output/dataset_oficial.csv')
ds['Fecha'] = pd.to_datetime(ds['Fecha'])
eem = pd.read_excel('Historico-EEM.xlsx', sheet_name='Mediana', header=[7,8])
eem.columns = [' '.join(c).replace('Unnamed: 0_level_1','').replace('Unnamed: 1_level_1','').strip() for c in eem.columns]
eem = eem.dropna(subset=['Año','Mes']).copy()
eem['Año'] = eem['Año'].astype(int); eem['Mes'] = eem['Mes'].astype(int)
eem['Fecha'] = pd.to_datetime(dict(year=eem['Año'], month=eem['Mes'], day=1))
eem = eem.rename(columns={'Inflación En 12 meses': 'E_pi_12m'})
ds = ds.merge(eem[['Fecha','E_pi_12m']], on='Fecha', how='left')
ds['E_pi_dado_t12'] = ds['E_pi_12m'].shift(12)
ds['error'] = ds['pi_t'] - ds['E_pi_dado_t12']

resultados = json.load(open('output/resultados.json'))
break_date = pd.Timestamp('2020-03-01')

# ============================================================
# FIGURA 2 - MZ con leyenda explícita y Wald de subperíodos
# ============================================================
df_an = ds[ds['Fecha'] >= '2010-06-01'].dropna(subset=['pi_t','E_pi_dado_t12']).reset_index(drop=True)
df_pre  = df_an[df_an['Fecha'] <  break_date]
df_post = df_an[df_an['Fecha'] >= break_date]

t2_full = resultados['t2_mincer_zarnowitz']['full']
t2_pre  = resultados['t2_mincer_zarnowitz']['pre']
t2_post = resultados['t2_mincer_zarnowitz']['post']

fig, ax = plt.subplots(figsize=(7.6, 5.8))

# Pre y post con colores y leyenda explícita
ax.scatter(df_pre['E_pi_dado_t12'], df_pre['pi_t'], color='#5070B0', alpha=0.55,
           s=35, edgecolor='white', linewidth=0.5, label=f'Pre-pandemia (N={len(df_pre)})')
ax.scatter(df_post['E_pi_dado_t12'], df_post['pi_t'], color='#C04040', alpha=0.55,
           s=35, edgecolor='white', linewidth=0.5, label=f'Post-pandemia (N={len(df_post)})')

xr = np.linspace(df_an['E_pi_dado_t12'].min()-0.3, df_an['E_pi_dado_t12'].max()+0.3, 50)
ax.plot(xr, xr, color='grey', linestyle='--', linewidth=1, label='45° (predicción perfecta)')
ax.plot(xr, t2_full['alpha'] + t2_full['beta']*xr, color=COLOR_OBS, linewidth=2,
        label=f"OLS muestra completa: α={t2_full['alpha']:.2f}, β={t2_full['beta']:.2f}")

ax.set_xlabel(r'Expectativa de inflación a 12m, $E_{t-12}[\pi_t]$ (%)')
ax.set_ylabel(r'Inflación interanual realizada $\pi_t$ (%)')
ax.set_title('Mincer-Zarnowitz: realizado vs. esperado a 12 meses', fontweight='bold')
ax.legend(loc='upper left', fontsize=8.8, framealpha=0.92)
ax.grid(alpha=0.25)

# Nota inferior con Wald de subperíodos
nota = (
    f"Wald (HAC Newey-West): full χ²={t2_full['wald_chi2']:.2f} (p={t2_full['wald_p']:.3f}, no rechaza), "
    f"pre χ²={t2_pre['wald_chi2']:.2f} (p={t2_pre['wald_p']:.3f}, rechaza al 5%), "
    f"post χ²={t2_post['wald_chi2_hodrick']:.2f} (p={t2_post['wald_p_hodrick']:.3f} bajo Hodrick, rechaza al 1%)."
)
fig.text(0.5, -0.04, nota, ha='center', fontsize=8.0, style='italic', color='#444', wrap=True)

plt.savefig(FIGURES + 'fig2_mz_scatter.png', bbox_inches='tight')
plt.close()
print("Figura 2 regenerada")

# ============================================================
# FIGURA 4 - Lambda rolling SIN eje ψ + bandas IC95% + endpoint
# ============================================================
df_roll = pd.read_csv('output/lambda_rolling_ci.csv')
df_roll['fecha'] = pd.to_datetime(df_roll['fecha'])

fig, ax = plt.subplots(figsize=(11, 4.8))

# Sombreado post-pandémico
ax.axvspan(break_date, df_roll['fecha'].max(), alpha=0.10, color='grey', zorder=0)

# Sombreado endpoint sensible (últimos 12 meses = h)
endpoint_start = df_roll['fecha'].max() - pd.DateOffset(months=12)
ax.axvspan(endpoint_start, df_roll['fecha'].max(), alpha=0.15, color='#FF9999', zorder=0,
           label='Zona endpoint sensible (h=12m)')

# Bandas IC95%
ax.fill_between(df_roll['fecha'], df_roll['lo'], df_roll['hi'],
                color=COLOR_OBS, alpha=0.15, label='IC 95% (HAC Newey-West)')

# Línea λ
ax.plot(df_roll['fecha'], df_roll['lambda'], color=COLOR_OBS, linewidth=1.8,
        label=r'$\lambda$ - rigidez informacional')

# Línea de referencia en cero
ax.axhline(0, color='black', linewidth=0.4, linestyle='-', alpha=0.5)

# Marcas de quiebres relevantes
ax.axvline(pd.Timestamp('2017-01-01'), color='grey', linewidth=0.6, linestyle=':', alpha=0.7)
ax.text(pd.Timestamp('2017-02-01'), 2.5, 'Rediseño\nEEM 2017', fontsize=8.5, style='italic', color='#555')

ax.set_ylabel(r'$\lambda$ — coeficiente de Coibion-Gorodnichenko (rolling 36m)', fontsize=10.5)
ax.set_xlabel('Fecha (final de la ventana de 36 meses)')
ax.set_title('Evolución temporal del coeficiente de Coibion-Gorodnichenko con IC 95%',
             fontweight='bold', fontsize=12)

ax.legend(loc='upper left', fontsize=9, framealpha=0.92, ncol=1)
ax.grid(alpha=0.25)
ax.xaxis.set_major_locator(mdates.YearLocator(2))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

# Ajustar ylim para excluir outliers de SE muy grandes
ymin = max(-2.5, df_roll['lo'].min() - 0.2)
ymax = min(4.0, df_roll['hi'].max() + 0.2)
ax.set_ylim(ymin, ymax)

plt.savefig(FIGURES + 'fig4_lambda_rolling.png', bbox_inches='tight')
plt.close()
print("Figura 4 regenerada (sin eje ψ, con bandas y endpoint marcado)")

# ============================================================
# FIGURA 6 - Bai-Perron con fechas correctas y medias correctas
# ============================================================
medias = resultados['bai_perron']['medias_segmentos_m3']
breaks_fechas = ['2012-02', '2020-08', '2023-02']

fig, ax = plt.subplots(figsize=(11, 4.6))
df_an_bp = df_an.dropna(subset=['error']).reset_index(drop=True)

# Barras de error
ax.bar(df_an_bp['Fecha'], df_an_bp['error'], color=COLOR_ERR, alpha=0.55,
       label='Error de pronóstico (p.p.)', width=22, zorder=1)
ax.axhline(0, color='black', linewidth=0.4, alpha=0.7)

# Líneas verticales en quiebres
for d in breaks_fechas:
    bd = pd.Timestamp(d + '-01')
    ax.axvline(bd, color='grey', linestyle='--', linewidth=1.0, alpha=0.8, zorder=2)
    ax.text(bd, 7, f' {d}', fontsize=9, style='italic', color='#444',
            verticalalignment='top', horizontalalignment='left')

# Línea de media por segmento
for seg in medias:
    fi = pd.Timestamp(seg['fecha_inicio'] + '-01')
    ff = pd.Timestamp(seg['fecha_fin'] + '-01')
    ax.hlines(seg['media'], fi, ff, color='#A02020', linewidth=2.4, zorder=3)
    # Etiqueta con μ
    mid = fi + (ff - fi)/2
    ax.text(mid, seg['media'] + (0.5 if seg['media'] >= 0 else -0.6),
            f"μ = {seg['media']:.2f}",
            fontsize=10, fontweight='bold', color='#A02020', ha='center')

ax.set_xlabel('Fecha')
ax.set_ylabel('Error de pronóstico (p.p.)')
ax.set_title(f'Quiebres estructurales múltiples (Bai-Perron, m = 3 con BIC monótonamente decreciente hasta m=5)',
             fontweight='bold', fontsize=12)

ax.legend(loc='lower left', fontsize=9, framealpha=0.92)
ax.grid(alpha=0.25)
ax.xaxis.set_major_locator(mdates.YearLocator(2))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.set_ylim(-7, 8)

# Nota
fig.text(0.5, -0.03,
         f"Fuente: cálculos propios. Líneas rojas indican la media del error en cada subperíodo definido por los quiebres óptimos. Trimming del 10%.",
         ha='center', fontsize=8.3, style='italic', color='#444')

plt.savefig(FIGURES + 'fig6_bai_perron.png', bbox_inches='tight')
plt.close()
print("Figura 6 regenerada (fechas corregidas: 2012-02, 2020-08, 2023-02)")
