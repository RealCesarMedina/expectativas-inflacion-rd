"""Generar figuras 6 y 7: Bai-Perron y sesgo condicional."""
# ============================================================================
# Configuración portable de rutas
# ============================================================================
import os
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, '..', '..'))  # raíz del paquete
DATA_RAW = os.path.join(_ROOT, '01_data_raw') + os.sep
RESULTS  = os.path.join(_ROOT, '03_resultados') + os.sep
FIGURES  = os.path.join(_ROOT, '04_figuras') + os.sep
os.makedirs(RESULTS, exist_ok=True)
os.makedirs(FIGURES, exist_ok=True)
# ============================================================================


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import json

with open(RESULTS + 'resultados_econometricos.json') as f: R = json.load(f)

# Reconstruir datos para gráficos
ds = pd.read_csv(RESULTS + 'Dataset_Consolidado_BCRD.csv')
ds['Fecha'] = pd.to_datetime(ds['Fecha'])
eem = pd.read_excel(DATA_RAW + 'Historico-EEM_BCRD.xlsx', sheet_name='Mediana', header=[7,8])
eem.columns = [' '.join(c).replace('Unnamed: 0_level_1','').replace('Unnamed: 1_level_1','').strip() for c in eem.columns]
eem = eem.dropna(subset=['Año','Mes']).copy()
eem['Año'] = eem['Año'].astype(int); eem['Mes'] = eem['Mes'].astype(int)
eem['Fecha'] = pd.to_datetime(dict(year=eem['Año'], month=eem['Mes'], day=1))
eem = eem.sort_values('Fecha').reset_index(drop=True)
eem.rename(columns={'Inflación En 12 meses': 'E_pi_12m'}, inplace=True)
df = eem.merge(ds[['Fecha','pi_t']], on='Fecha', how='left')
df['E_pi_t_dado_t12'] = df['E_pi_12m'].shift(12)
df['error'] = df['pi_t'] - df['E_pi_t_dado_t12']
df_an = df[df['error'].notna()].copy().reset_index(drop=True)

plt.rcParams.update({'font.family':'serif','font.size':10,
                     'figure.dpi':150,'savefig.dpi':300,
                     'savefig.bbox':'tight','savefig.facecolor':'white'})
COLOR_OBS, COLOR_EXP, COLOR_ERR = '#C8102E', '#003DA5', '#FFB81C'
COLOR_GREEN = '#2E8B57'

# ============================================================================
# Figura 6: Bai-Perron — quiebres múltiples sobre el error
# ============================================================================
fechas_bp = R['bai_perron']['optimo_bic']['fechas']  # ['2012-04', '2020-08', '2023-02']
fechas_bp_dt = [pd.Timestamp(f + '-01') for f in fechas_bp]

fig, ax = plt.subplots(figsize=(11, 4.5))
ax.bar(df_an['Fecha'], df_an['error'], color=COLOR_ERR, alpha=0.55, width=25, label='Error de pronóstico (p.p.)')

# Calcular medias por segmento
fechas_corte_completa = [df_an['Fecha'].min()] + fechas_bp_dt + [df_an['Fecha'].max()]
for i in range(len(fechas_corte_completa) - 1):
    sub = df_an[(df_an['Fecha'] >= fechas_corte_completa[i]) & 
                (df_an['Fecha'] < fechas_corte_completa[i+1])]
    if len(sub) > 5:
        media = sub['error'].mean()
        ax.hlines(media, fechas_corte_completa[i], fechas_corte_completa[i+1],
                 color=COLOR_OBS, linewidth=2.2, zorder=4)
        # Etiqueta de la media
        x_mid = fechas_corte_completa[i] + (fechas_corte_completa[i+1] - fechas_corte_completa[i])/2
        ax.text(x_mid, media + 0.4, f'μ = {media:.2f}', ha='center', fontsize=9,
                color=COLOR_OBS, fontweight='bold')

# Líneas verticales en quiebres
for f in fechas_bp_dt:
    ax.axvline(f, color='black', linestyle='--', linewidth=1, alpha=0.65, zorder=3)
    ax.text(f + pd.Timedelta(days=20), ax.get_ylim()[1]*0.9, f.strftime('%Y-%m'),
            fontsize=8.5, style='italic', color='black')

ax.axhline(0, color='grey', linewidth=0.5)
ax.set_ylabel('Error de pronóstico (p.p.)')
ax.set_title('Quiebres estructurales múltiples (Bai-Perron, m = 3 óptimo por BIC)',
             fontweight='bold', fontsize=12)
ax.legend(loc='lower left', fontsize=9)
ax.grid(alpha=0.25)
ax.xaxis.set_major_locator(mdates.YearLocator(2))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
fig.text(0.5, -0.04,
         'Fuente: cálculos propios. Líneas rojas indican la media del error en cada subperíodo definido por los quiebres óptimos.',
         ha='center', fontsize=8.3, style='italic', color='#444')
plt.savefig(FIGURES + 'fig6_bai_perron.png', bbox_inches='tight')
plt.close()
print("Figura 6 generada (Bai-Perron)")

# ============================================================================
# Figura 7: sesgo condicional al estado
# ============================================================================
mediana_pi = df_an['pi_t'].median()
df_an['estado'] = np.where(df_an['pi_t'] > mediana_pi, 'Inflación alta', 'Inflación baja')

fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))

# Panel A: scatter por estado
ax = axes[0]
ax.axhline(0, color='grey', linewidth=0.5)
for est, color in [('Inflación baja', COLOR_EXP), ('Inflación alta', COLOR_OBS)]:
    sub = df_an[df_an['estado'] == est]
    ax.scatter(sub['pi_t'], sub['error'], alpha=0.5, color=color, s=30, label=est,
              edgecolor='white', linewidth=0.4)
    media = sub['error'].mean()
    ax.hlines(media, sub['pi_t'].min(), sub['pi_t'].max(), color=color, linewidth=2,
             linestyle='--')
ax.axvline(mediana_pi, color='black', linewidth=0.8, linestyle=':', alpha=0.5)
ax.set_xlabel('Inflación realizada $\\pi_t$ (%)')
ax.set_ylabel('Error de pronóstico $e_t$ (p.p.)')
ax.set_title('Asimetría del sesgo según el estado de inflación', fontweight='bold')
ax.legend(loc='lower right', fontsize=9)
ax.grid(alpha=0.25)

# Panel B: distribución del error por estado
ax = axes[1]
sub_baja = df_an[df_an['estado'] == 'Inflación baja']['error']
sub_alta = df_an[df_an['estado'] == 'Inflación alta']['error']
ax.hist(sub_baja, bins=20, alpha=0.55, color=COLOR_EXP, label=f'Inflación baja (μ={sub_baja.mean():.2f})')
ax.hist(sub_alta, bins=20, alpha=0.55, color=COLOR_OBS, label=f'Inflación alta (μ={sub_alta.mean():.2f})')
ax.axvline(0, color='black', linewidth=0.5)
ax.axvline(sub_baja.mean(), color=COLOR_EXP, linewidth=2, linestyle='--')
ax.axvline(sub_alta.mean(), color=COLOR_OBS, linewidth=2, linestyle='--')
ax.set_xlabel('Error de pronóstico $e_t$ (p.p.)')
ax.set_ylabel('Frecuencia')
ax.set_title('Distribución del error por régimen', fontweight='bold')
ax.legend(loc='upper left', fontsize=9)
ax.grid(alpha=0.25)

fig.suptitle(f'Sesgo condicional: subestimación bajo inflación alta, sobreestimación bajo inflación baja\n(Diferencia: 3.04 p.p., p < 0.001)',
             fontsize=11, y=1.02)
plt.tight_layout()
plt.savefig(FIGURES + 'fig7_sesgo_condicional.png', bbox_inches='tight')
plt.close()
print("Figura 7 generada (sesgo condicional)")
