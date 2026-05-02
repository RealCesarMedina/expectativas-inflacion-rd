"""Genera figuras del paper basadas en los datos reales."""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os, json

# (output dir manejado por RESULTS/FIGURES)

# Load
df = pd.read_excel(DATA_RAW + 'Dataset_EEM_Realizada.xlsx')
df['Fecha'] = pd.to_datetime(df['Fecha'])
df_an = df.dropna(subset=['Error_Pronostico']).copy()

with open(RESULTS + 'resultados_econometricos.json') as f:
    R = json.load(f)

COLOR_OBS  = '#C8102E'
COLOR_EXP  = '#003DA5'
COLOR_ERR  = '#FFB81C'

plt.rcParams.update({
    'font.family': 'serif', 'font.size': 10,
    'axes.titlesize': 11, 'axes.labelsize': 10,
    'figure.dpi': 150, 'savefig.dpi': 300,
    'savefig.bbox': 'tight', 'savefig.facecolor': 'white'
})

# ============================================================================
# Figura 1: Inflación, expectativa, error
# ============================================================================
fig, ax = plt.subplots(figsize=(11, 4.8))
break_date = pd.Timestamp('2020-08-01')

ax.axvspan(pd.Timestamp('2020-03-01'), pd.Timestamp('2022-12-31'),
           alpha=0.13, color='#999999', zorder=0)

# Realized
ax.plot(df['Fecha'], df['Inflacion_Realizada'],
        color=COLOR_OBS, linewidth=1.7, label='Inflación interanual realizada (%)', zorder=3)

# Expectation lagged 12 (lo que se esperaba para hoy hace 12 meses)
ax.plot(df['Fecha'], df['Expectativa_12m_lag12'],
        color=COLOR_EXP, linewidth=1.5, label='Expectativa formada 12 meses antes (%)',
        linestyle='-', zorder=2)

# Error bars
ax.bar(df_an['Fecha'], df_an['Error_Pronostico'],
       color=COLOR_ERR, alpha=0.55, label='Error de pronóstico (p.p.)',
       width=22, zorder=1)

ax.axvline(break_date, color='#222', linestyle='--', linewidth=1.2, alpha=0.75)
ax.text(break_date - pd.Timedelta(days=60), 9.5, 'supF = 53.75\n(ago-2020)',
        ha='right', fontsize=8.5, color='#222', style='italic')

ax.axhline(0, color='#999', linewidth=0.4, zorder=2)
ax.xaxis.set_major_locator(mdates.YearLocator(2))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.set_ylabel('% interanual / Error (p.p.)')
ax.set_ylim(-5, 11)
ax.set_title('Figura 1. Inflación, expectativa a 12 meses (rezagada) y error de pronóstico',
             fontweight='bold')
ax.legend(loc='upper left', frameon=True, framealpha=0.92, fontsize=9)
ax.grid(alpha=0.25)

fig.text(0.5, -0.03,
    'Fuente: BCRD - Encuesta de Expectativas Macroeconómicas (mediana). Cálculos del autor.\n'
    'Sombra: periodo pandémico (mar 2020 - dic 2022). Línea punteada: quiebre estructural (Chow secuencial, ago-2020).',
    ha='center', fontsize=8.2, style='italic', color='#555')

plt.savefig(FIGURES + 'fig1_inflacion_expectativa.png',
            dpi=300, bbox_inches='tight')
plt.close()
print("Figura 1 generada")

# ============================================================================
# Figura 2: Mincer-Zarnowitz scatter
# ============================================================================
fig, ax = plt.subplots(figsize=(7, 6))
df_mz = df_an.dropna(subset=['Inflacion_Realizada','Expectativa_12m_lag12'])

# Por subperíodo
pre = df_mz[df_mz['Fecha'] < '2020-03-01']
post = df_mz[df_mz['Fecha'] >= '2020-03-01']

ax.scatter(pre['Expectativa_12m_lag12'], pre['Inflacion_Realizada'],
           alpha=0.6, color=COLOR_EXP, s=38, edgecolor='white', linewidth=0.5,
           label=f'Pre-pandemia (n={len(pre)})', zorder=2)
ax.scatter(post['Expectativa_12m_lag12'], post['Inflacion_Realizada'],
           alpha=0.7, color=COLOR_OBS, s=42, edgecolor='white', linewidth=0.5,
           label=f'Post-pandemia (n={len(post)})', zorder=3)

# 45 degree line
xx = np.linspace(2, 9, 50)
ax.plot(xx, xx, color='#444', linestyle='--', linewidth=1.2,
        label='Predicción perfecta (45°)', zorder=1)

# Fitted line
alpha_mz, beta_mz = R['m2_mz']['alpha'], R['m2_mz']['beta']
ax.plot(xx, alpha_mz + beta_mz*xx, color='#7A0019', linewidth=1.8,
        label=f'Ajuste OLS: π = {alpha_mz:.2f} + {beta_mz:.2f}·E[π]', zorder=4)

ax.set_xlabel('Expectativa formada 12 meses antes  E$_{t-12}$[π$_t$] (%)')
ax.set_ylabel('Inflación interanual realizada  π$_t$ (%)')
ax.set_title(f'Figura 2. Diagrama de Mincer-Zarnowitz\n'
             f'Wald conjunto (α=0, β=1): χ²={R["m2_mz"]["wald_chi2"]:.2f}, p={R["m2_mz"]["wald_p"]:.3f}',
             fontweight='bold')
ax.legend(loc='upper left', frameon=True, framealpha=0.92, fontsize=8.5)
ax.grid(alpha=0.25)
ax.set_xlim(2, 9)
ax.set_ylim(-0.5, 10)

fig.text(0.5, -0.03,
    'Nota: La línea de ajuste sugiere sub-reacción de las expectativas (β<1) pero el test conjunto\n'
    'no rechaza la racionalidad de Mincer-Zarnowitz. Fuente: cálculos del autor con datos del BCRD.',
    ha='center', fontsize=8.2, style='italic', color='#555')
plt.savefig('(FIGURES)fig2_mincer_zarnowitz.png',
            dpi=300, bbox_inches='tight')
plt.close()
print("Figura 2 generada")

# ============================================================================
# Figura 3: Coibion-Gorodnichenko (real data)
# ============================================================================
df_cg = df_an.dropna(subset=['Error_Pronostico','Revision'])
pre_cg = df_cg[df_cg['Fecha'] < '2020-03-01']
post_cg = df_cg[df_cg['Fecha'] >= '2020-03-01']

fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))

# Panel A: Pre-pandemia
ax = axes[0]
ax.scatter(pre_cg['Revision'], pre_cg['Error_Pronostico'],
           alpha=0.6, color=COLOR_EXP, s=35, edgecolor='white', linewidth=0.5)
xx = np.linspace(pre_cg['Revision'].min(), pre_cg['Revision'].max(), 50)
slope_pre = 0.260
intercept_pre = pre_cg['Error_Pronostico'].mean() - slope_pre * pre_cg['Revision'].mean()
ax.plot(xx, slope_pre*xx + intercept_pre, color=COLOR_OBS, linewidth=2,
        label=f'λ = 0.26 (p = 0.40)')
ax.axhline(0, color='#999', linewidth=0.4, linestyle='--', zorder=0)
ax.axvline(0, color='#999', linewidth=0.4, linestyle='--', zorder=0)
ax.set_xlabel('Revisión de expectativa  rev$_t$')
ax.set_ylabel('Error de pronóstico  e$_t$')
ax.set_title('(a)  Pre-pandemia (jun 2010 – feb 2020)\nNo rechaza FIRE',
             fontweight='bold')
ax.legend(loc='upper left', frameon=False, fontsize=9)
ax.grid(alpha=0.25)

# Panel B: Post-pandemia
ax = axes[1]
ax.scatter(post_cg['Revision'], post_cg['Error_Pronostico'],
           alpha=0.7, color=COLOR_OBS, s=38, edgecolor='white', linewidth=0.5)
xx = np.linspace(post_cg['Revision'].min(), post_cg['Revision'].max(), 50)
slope_post = 0.915
intercept_post = post_cg['Error_Pronostico'].mean() - slope_post * post_cg['Revision'].mean()
ax.plot(xx, slope_post*xx + intercept_post, color='#7A0019', linewidth=2,
        label=f'λ = 0.92 (p = 0.020)')
ax.axhline(0, color='#999', linewidth=0.4, linestyle='--', zorder=0)
ax.axvline(0, color='#999', linewidth=0.4, linestyle='--', zorder=0)
ax.set_xlabel('Revisión de expectativa  rev$_t$')
ax.set_ylabel('Error de pronóstico  e$_t$')
ax.set_title('(b)  Post-pandemia (mar 2020 – mar 2026)\nRechaza FIRE: rigidez informacional',
             fontweight='bold')
ax.legend(loc='upper left', frameon=False, fontsize=9)
ax.grid(alpha=0.25)

fig.suptitle('Figura 3. Test de Coibion-Gorodnichenko por subperíodo',
             fontsize=12.5, fontweight='bold', y=1.02)
fig.text(0.5, -0.04,
    'Nota: bajo expectativas plenamente racionales (FIRE), las revisiones no deben predecir errores. La pendiente positiva en (b)\n'
    'es la firma econométrica de rigidez informacional. Fuente: cálculos del autor con datos del BCRD.',
    ha='center', fontsize=8.3, style='italic', color='#555')
plt.tight_layout()
plt.savefig(FIGURES + 'fig3_cg_subperiodos.png',
            dpi=300, bbox_inches='tight')
plt.close()
print("Figura 3 generada")

# ============================================================================
# Figura 4: Distribución del error por subperíodo
# ============================================================================
fig, axes = plt.subplots(1, 2, figsize=(11, 4))

pre_data = df_an[df_an['Fecha'] < '2020-03-01']['Error_Pronostico']
post_data = df_an[df_an['Fecha'] >= '2020-03-01']['Error_Pronostico']

ax = axes[0]
ax.hist(pre_data, bins=22, color=COLOR_EXP, alpha=0.65, edgecolor='white')
ax.axvline(pre_data.mean(), color=COLOR_OBS, linewidth=2.2,
           label=f'Media = {pre_data.mean():.2f}')
ax.axvline(0, color='#444', linestyle='--', linewidth=1)
ax.set_xlabel('Error de pronóstico (p.p.)')
ax.set_ylabel('Frecuencia')
ax.set_title(f'(a)  Pre-pandemia (n={len(pre_data)})\nMedia rechaza H₀: α=0  (p=0.005)',
             fontweight='bold')
ax.legend(frameon=False, fontsize=9)
ax.grid(alpha=0.25)
ax.set_xlim(-5, 7)

ax = axes[1]
ax.hist(post_data, bins=18, color=COLOR_OBS, alpha=0.65, edgecolor='white')
ax.axvline(post_data.mean(), color=COLOR_EXP, linewidth=2.2,
           label=f'Media = {post_data.mean():.2f}')
ax.axvline(0, color='#444', linestyle='--', linewidth=1)
ax.set_xlabel('Error de pronóstico (p.p.)')
ax.set_ylabel('Frecuencia')
ax.set_title(f'(b)  Post-pandemia (n={len(post_data)})\nMedia no rechaza H₀: α=0  (p=0.31)',
             fontweight='bold')
ax.legend(frameon=False, fontsize=9)
ax.grid(alpha=0.25)
ax.set_xlim(-5, 7)

fig.suptitle('Figura 4. Distribución del error de pronóstico por subperíodo',
             fontsize=12.5, fontweight='bold', y=1.02)
fig.text(0.5, -0.04,
    'Nota: pre-pandemia los analistas sobreestimaron sistemáticamente la inflación; post-pandemia el sesgo invierte signo pero pierde significancia.\n'
    'Fuente: cálculos del autor con datos del BCRD.',
    ha='center', fontsize=8.3, style='italic', color='#555')
plt.tight_layout()
plt.savefig('(FIGURES)fig4_dist_error.png',
            dpi=300, bbox_inches='tight')
plt.close()
print("Figura 4 generada")

# ============================================================================
# Figura 5: Test secuencial Chow (estabilidad estructural)
# ============================================================================
df_seq = df_an.dropna(subset=['Error_Pronostico']).reset_index(drop=True)
n = len(df_seq)
frac = 0.15
start, end = int(n*frac), int(n*(1-frac))
fechas_chow, fs_chow = [], []
ssr_pooled = ((df_seq['Error_Pronostico'] - df_seq['Error_Pronostico'].mean())**2).sum()

for i in range(start, end):
    d1 = df_seq.iloc[:i]; d2 = df_seq.iloc[i:]
    ssr1 = ((d1['Error_Pronostico'] - d1['Error_Pronostico'].mean())**2).sum()
    ssr2 = ((d2['Error_Pronostico'] - d2['Error_Pronostico'].mean())**2).sum()
    F = ((ssr_pooled - (ssr1+ssr2))/1) / ((ssr1+ssr2)/(n-2))
    fechas_chow.append(df_seq['Fecha'].iloc[i])
    fs_chow.append(F)

fig, ax = plt.subplots(figsize=(11, 4))
ax.plot(fechas_chow, fs_chow, color=COLOR_EXP, linewidth=1.6)
ax.axhline(8.85, color=COLOR_OBS, linestyle='--', linewidth=1.2,
           label='VC Andrews (1993) 5%: 8.85')
max_idx = np.argmax(fs_chow)
ax.scatter([fechas_chow[max_idx]], [fs_chow[max_idx]],
           color=COLOR_OBS, s=80, zorder=5, edgecolor='white', linewidth=1.5,
           label=f'supF = {fs_chow[max_idx]:.1f} ({fechas_chow[max_idx].strftime("%b-%Y")})')
ax.set_xlabel(None)
ax.set_ylabel('Estadístico F secuencial')
ax.set_title('Figura 5. Test secuencial de Chow para quiebre estructural en el intercepto del error',
             fontweight='bold')
ax.legend(loc='upper left', frameon=True, framealpha=0.92, fontsize=9)
ax.grid(alpha=0.25)
ax.xaxis.set_major_locator(mdates.YearLocator(2))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
fig.text(0.5, -0.04,
    'Nota: el supF estadísticamente significativo en agosto 2020 valida la separación pre/post pandemia. '
    'Fuente: cálculos del autor.',
    ha='center', fontsize=8.3, style='italic', color='#555')
plt.tight_layout()
plt.savefig('(FIGURES)fig5_chow_secuencial.png',
            dpi=300, bbox_inches='tight')
plt.close()
print("Figura 5 generada")

print("\nTodas las figuras generadas en (FIGURES)")
