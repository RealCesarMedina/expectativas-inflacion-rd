"""
Análisis econométrico — Racionalidad de expectativas RD.

Características:
1. Test de eficiencia informacional con VARIABLES OBSERVABLES OFICIALES del BCRD
   (TPM efectiva, tipo de cambio nominal, PIB real interanual), no con las
   medianas del panel EEM.
2. IPC oficial empalmado por el BCRD (serie continua 2009-2026 sin gap 2012).
3. Corrección de Bonferroni y FDR (Benjamini-Hochberg) para pruebas múltiples.
4. VIFs para diagnóstico de multicolinealidad en la regresión de eficiencia.
5. Tests Chow exógenos en fechas de cambio metodológico de la EEM (2014, 2017).
6. Reporte de magnitud económica de coeficientes (R² parcial, intervalos).
"""
# ============================================================================
# Configuración portable de rutas
# ============================================================================
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_ROOT = _os.path.abspath(_os.path.join(_HERE, '..', '..'))
DATA_RAW = _os.path.join(_ROOT, '01_data_raw') + _os.sep
RESULTS  = _os.path.join(_ROOT, '03_resultados') + _os.sep
FIGURES  = _os.path.join(_ROOT, '04_figuras') + _os.sep
_os.makedirs(RESULTS, exist_ok=True)
_os.makedirs(FIGURES, exist_ok=True)
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
import statsmodels.api as sm
from statsmodels.regression.linear_model import OLS
from statsmodels.stats.sandwich_covariance import cov_hac
from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.stats.diagnostic import (acorr_breusch_godfrey, het_breuschpagan,
                                          linear_reset, acorr_ljungbox)
from statsmodels.stats.stattools import jarque_bera
from statsmodels.stats.outliers_influence import variance_inflation_factor
from scipy import stats
import warnings, json, os

warnings.filterwarnings("ignore")
# (output dir manejado por RESULTS/FIGURES)
# (output dir manejado por RESULTS/FIGURES)

# ============================================================================
# 1. CARGAR DATOS OFICIALES
# ============================================================================
ds = pd.read_csv(RESULTS + 'Dataset_Consolidado_BCRD.csv')
ds['Fecha'] = pd.to_datetime(ds['Fecha'])
print(f"Dataset oficial: {len(ds)} obs ({ds['Fecha'].min().strftime('%Y-%m')} a {ds['Fecha'].max().strftime('%Y-%m')})")

# ============================================================================
# 2. CARGAR EEM (medianas del consenso)
# ============================================================================
eem = pd.read_excel(DATA_RAW + 'Historico-EEM_BCRD.xlsx', sheet_name='Mediana', header=[7,8])
eem.columns = [' '.join(c).replace('Unnamed: 0_level_1','').replace('Unnamed: 1_level_1','').strip() for c in eem.columns]
eem = eem.dropna(subset=['Año','Mes']).copy()
eem['Año'] = eem['Año'].astype(int)
eem['Mes'] = eem['Mes'].astype(int)
eem['Fecha'] = pd.to_datetime(dict(year=eem['Año'], month=eem['Mes'], day=1))
eem = eem.sort_values('Fecha').reset_index(drop=True)
eem.rename(columns={
    'Inflación En 12 meses': 'E_pi_12m',
    'Tasa de política monetaria (TPM) Mes actual': 'E_tpm_mes',
    'Variación porcentual interanual implícita del tipo de cambio Año actual': 'E_tc_act',
    'Crecimiento interanual del PIB real Año actual': 'E_pib_act',
}, inplace=True)

# ============================================================================
# 3. CONSTRUIR VARIABLES DEL ANÁLISIS
# ============================================================================
df = eem.merge(ds[['Fecha','pi_t','TPM_obs','var_tc','var_pib']], on='Fecha', how='left')
df['E_pi_t_dado_t12'] = df['E_pi_12m'].shift(12)
df['error'] = df['pi_t'] - df['E_pi_t_dado_t12']
df['error_lag12'] = df['error'].shift(12)
df['revision'] = df['E_pi_12m'] - df['E_pi_12m'].shift(1)

# Variables del set de información disponible al momento de pronosticar (t-13)
# IMPORTANTE: variables OBSERVABLES OFICIALES, no del panel
df['pi_lag13']  = df['pi_t'].shift(13)
df['tpm_obs_lag13'] = df['TPM_obs'].shift(13)
df['vtc_obs_lag13'] = df['var_tc'].shift(13)
df['vpib_obs_lag13'] = df['var_pib'].shift(13)

mask_full = df['error'].notna()
df_an = df[mask_full].copy().reset_index(drop=True)
fecha_corte = pd.Timestamp('2020-03-01')
df_pre  = df_an[df_an['Fecha'] <  fecha_corte].copy()
df_post = df_an[df_an['Fecha'] >= fecha_corte].copy()

print(f"\nMuestra analítica: {df_an['Fecha'].min().strftime('%Y-%m')} a {df_an['Fecha'].max().strftime('%Y-%m')}")
print(f"  N total: {len(df_an)} | pre-pandemia: {len(df_pre)} | post-pandemia: {len(df_post)}")

# ============================================================================
# 4. DESCRIPTIVAS
# ============================================================================
vars_desc = {
    'Inflación π_t (%)': df_an['pi_t'],
    'Expectativa E[π_{t+12}] (%)': df_an['E_pi_12m'],
    'Error de pronóstico e_t (p.p.)': df_an['error'],
    'Revisión rev_t (p.p.)': df_an['revision'],
    'TPM observada (%)': df_an['TPM_obs'],
    'Var. tipo de cambio observada (%)': df_an['var_tc'],
    'Crec. PIB real observado (%)': df_an['var_pib'],
}
stats_desc = []
for n, s in vars_desc.items():
    s = s.dropna()
    stats_desc.append({'Variable':n,'N':len(s),
        'Media':round(s.mean(),3),'Mediana':round(s.median(),3),
        'DesvEst':round(s.std(),3),'Min':round(s.min(),3),
        'Max':round(s.max(),3),'Asimetria':round(stats.skew(s),3),
        'Curtosis':round(stats.kurtosis(s, fisher=False),3)})
df_desc = pd.DataFrame(stats_desc)
print("\n=== DESCRIPTIVAS ===")
print(df_desc.to_string(index=False))

# ============================================================================
# 5. RAÍCES UNITARIAS
# ============================================================================
def pr(s, nombre):
    s = s.dropna()
    adf = adfuller(s, regression='c', autolag='BIC')
    kp_t, kp_p, _, kp_cv = kpss(s, regression='c', nlags='auto')
    return {'Serie':nombre,'ADF stat':round(adf[0],3),'ADF p':round(adf[1],3),
            'ADF 5%':round(adf[4]['5%'],3),'KPSS stat':round(kp_t,3),
            'KPSS p':round(kp_p,3),
            'Conclusión':'I(0)' if (adf[1]<0.10 and kp_t<kp_cv['5%']) else 'Inconclusivo'}
raices = pd.DataFrame([
    pr(df_an['pi_t'], 'Inflación π_t'),
    pr(df_an['E_pi_12m'], 'Expectativa E[π_{t+12}]'),
    pr(df_an['error'], 'Error de pronóstico'),
    pr(df_an['revision'].dropna(), 'Revisión'),
    pr(df_an['TPM_obs'].dropna(), 'TPM observada'),
])
print("\n=== RAÍCES UNITARIAS ===")
print(raices.to_string(index=False))

# ============================================================================
# 6. INFERENCIA HAC
# ============================================================================
def hac_cov(m, lag_min=11):
    nlags = max(lag_min, int(np.ceil(4*(m.nobs/100)**(2/9))))
    return cov_hac(m, nlags=nlags)
def hac_cov_hodrick(m, h=12):
    return cov_hac(m, nlags=2*h-1)
def wald_test_hac(m, V, R, q):
    beta = m.params.values
    diff = R @ beta - q
    M = R @ V @ R.T
    chi2 = float(diff @ np.linalg.inv(M) @ diff)
    df_w = R.shape[0]
    p = 1 - stats.chi2.cdf(chi2, df_w)
    return chi2, df_w, p

# ============================================================================
# 7. TEST 1 - INSESGAMIENTO
# ============================================================================
def test_ins(d, e):
    y = d['error']
    X = pd.DataFrame({'const':1.0}, index=y.index)
    m = OLS(y, X, missing='drop').fit()
    V = hac_cov(m)
    se = np.sqrt(np.diag(V))[0]
    t = m.params.iloc[0] / se
    p = 2*(1 - stats.norm.cdf(abs(t)))
    return {'alpha':float(m.params.iloc[0]), 'se':float(se),'t':float(t),'p':float(p),'n':int(m.nobs)}

t1_full = test_ins(df_an, "Full"); t1_pre = test_ins(df_pre, "Pre"); t1_post = test_ins(df_post, "Post")
print("\n=== TEST 1: INSESGAMIENTO ===")
for et, t in [('Full', t1_full), ('Pre', t1_pre), ('Post', t1_post)]:
    print(f"  [{et}] α={t['alpha']:.4f}, SE_HAC={t['se']:.4f}, p={t['p']:.4f}, N={t['n']}")

# ============================================================================
# 8. TEST 2 - MINCER-ZARNOWITZ
# ============================================================================
def test_mz(d, e):
    y = d['pi_t']
    X = pd.DataFrame({'const':1.0,'E_pi':d['E_pi_t_dado_t12']}, index=y.index)
    mask = y.notna() & X['E_pi'].notna()
    y, X = y[mask], X[mask]
    m = OLS(y, X).fit()
    V = hac_cov(m); se = np.sqrt(np.diag(V))
    p = 2*(1-stats.norm.cdf(np.abs(m.params.values/se)))
    R = np.array([[1,0],[0,1]]); q = np.array([0,1])
    chi2, _, pwald = wald_test_hac(m, V, R, q)
    Vh = hac_cov_hodrick(m, h=12)
    chi2h, _, pwh = wald_test_hac(m, Vh, R, q)
    return {'alpha':float(m.params.iloc[0]),'beta':float(m.params.iloc[1]),
            'se_alpha':float(se[0]),'se_beta':float(se[1]),
            'p_alpha':float(p[0]),'p_beta':float(p[1]),
            'wald_chi2':float(chi2),'wald_p':float(pwald),
            'wald_chi2_hodrick':float(chi2h),'wald_p_hodrick':float(pwh),
            'r2':float(m.rsquared),'n':int(m.nobs)}

t2_full = test_mz(df_an, "Full"); t2_pre = test_mz(df_pre, "Pre"); t2_post = test_mz(df_post, "Post")
print("\n=== TEST 2: MINCER-ZARNOWITZ ===")
for et, t in [('Full', t2_full), ('Pre', t2_pre), ('Post', t2_post)]:
    print(f"  [{et}] α={t['alpha']:.3f}, β={t['beta']:.3f}, Wald χ²={t['wald_chi2']:.2f} (p_NW={t['wald_p']:.3f}, p_H={t['wald_p_hodrick']:.3f}), R²={t['r2']:.3f}, N={t['n']}")

# ============================================================================
# 9. TEST 3 - PERSISTENCIA
# ============================================================================
def test_pers(d, e):
    y = d['error']
    X = pd.DataFrame({'const':1.0,'error_lag12':d['error_lag12']}, index=y.index)
    mask = y.notna() & X['error_lag12'].notna()
    y, X = y[mask], X[mask]
    m = OLS(y, X).fit()
    V = hac_cov(m); se = np.sqrt(np.diag(V))
    p = 2*(1-stats.norm.cdf(np.abs(m.params.values/se)))
    return {'alpha':float(m.params.iloc[0]),'rho':float(m.params.iloc[1]),
            'se_alpha':float(se[0]),'se_rho':float(se[1]),
            'p_alpha':float(p[0]),'p_rho':float(p[1]),
            'r2':float(m.rsquared),'n':int(m.nobs)}

t3_full = test_pers(df_an, "Full"); t3_pre = test_pers(df_pre, "Pre")
print("\n=== TEST 3: PERSISTENCIA ===")
for et, t in [('Full', t3_full), ('Pre', t3_pre)]:
    print(f"  [{et}] ρ={t['rho']:.4f}, p={t['p_rho']:.4f}, R²={t['r2']:.3f}, N={t['n']}")

# ============================================================================
# 10. TEST 4 - EFICIENCIA INFORMACIONAL CON VARIABLES OBSERVABLES OFICIALES
# ============================================================================
print("\n=== TEST 4: EFICIENCIA INFORMACIONAL (variables observables oficiales) ===")
y = df_an['error']
X = pd.DataFrame({'const':1.0,
                  'pi_lag13':df_an['pi_lag13'],
                  'tpm_obs_lag13':df_an['tpm_obs_lag13'],
                  'vtc_obs_lag13':df_an['vtc_obs_lag13'],
                  'vpib_obs_lag13':df_an['vpib_obs_lag13']}, index=y.index)
mask = y.notna() & X.drop(columns='const').notna().all(axis=1)
y_e, X_e = y[mask], X[mask]
m4 = OLS(y_e, X_e).fit()
V4 = hac_cov(m4); se4 = np.sqrt(np.diag(V4))
p4 = 2*(1-stats.norm.cdf(np.abs(m4.params.values/se4)))
R4 = np.zeros((4,5))
for i in range(4): R4[i, i+1] = 1
chi24, _, pw4 = wald_test_hac(m4, V4, R4, np.zeros(4))
print(f"  N={int(m4.nobs)}, R²={m4.rsquared:.3f}")
labels = ['const','π_t-13','TPM_obs_t-13','Var_TC_obs_t-13','Var_PIB_obs_t-13']
for i, n in enumerate(labels):
    print(f"  {n}: coef={m4.params.iloc[i]:.4f}, SE={se4[i]:.4f}, p={p4[i]:.4f}")
print(f"  Wald conjunto γ=0: χ²(4)={chi24:.3f}, p={pw4:.4f}")

# VIFs (problema #9)
print("\n  VIFs (multicolinealidad):")
X_for_vif = X_e.drop(columns='const').values
vifs = [variance_inflation_factor(X_for_vif, i) for i in range(X_for_vif.shape[1])]
vif_dict = {}
for n, v in zip(labels[1:], vifs):
    print(f"    {n}: VIF={v:.2f}")
    vif_dict[n] = float(v)

# R² parcial: contribución única de cada regresor
print("\n  R² parciales (contribución única):")
r2_full = m4.rsquared
r2_partial = {}
for i, var_name in enumerate(['pi_lag13','tpm_obs_lag13','vtc_obs_lag13','vpib_obs_lag13']):
    X_red = X_e.drop(columns=var_name)
    m_red = OLS(y_e, X_red).fit()
    r2p = r2_full - m_red.rsquared
    r2_partial[labels[i+1]] = float(r2p)
    print(f"    {labels[i+1]}: ΔR² = {r2p:.4f}")

t4_dict = {'params':m4.params.tolist(),'se':se4.tolist(),'p':p4.tolist(),
           'wald_chi2':float(chi24),'wald_p':float(pw4),
           'r2':float(m4.rsquared),'n':int(m4.nobs),
           'vifs':vif_dict,'r2_partial':r2_partial,
           'labels':labels}

# ============================================================================
# 11. TEST 5 - COIBION-GORODNICHENKO
# ============================================================================
def test_cg(d, e):
    y = d['error']
    X = pd.DataFrame({'const':1.0,'revision':d['revision']}, index=y.index)
    mask = y.notna() & X['revision'].notna()
    y, X = y[mask], X[mask]
    m = OLS(y, X).fit()
    V = hac_cov(m); se = np.sqrt(np.diag(V))
    p = 2*(1-stats.norm.cdf(np.abs(m.params.values/se)))
    Vh = hac_cov_hodrick(m, h=12); seh = np.sqrt(np.diag(Vh))
    ph = 2*(1-stats.norm.cdf(np.abs(m.params.values/seh)))
    lam = float(m.params.iloc[1])
    psi = 1/(1+lam) if lam>-1 else None
    return {'alpha':float(m.params.iloc[0]),'lambda':lam,
            'se_alpha':float(se[0]),'se_lambda':float(se[1]),
            'p_alpha':float(p[0]),'p_lambda':float(p[1]),
            'p_lambda_hodrick':float(ph[1]),
            'psi':psi,'r2':float(m.rsquared),'n':int(m.nobs)}

t5_full = test_cg(df_an, "Full"); t5_pre = test_cg(df_pre, "Pre"); t5_post = test_cg(df_post, "Post")
print("\n=== TEST 5: COIBION-GORODNICHENKO ===")
for et, t in [('Full', t5_full), ('Pre', t5_pre), ('Post', t5_post)]:
    psi_str = f"{t['psi']:.3f}" if t['psi'] is not None else "n.a."
    print(f"  [{et}] λ={t['lambda']:.3f}, p_NW={t['p_lambda']:.4f}, p_H={t['p_lambda_hodrick']:.4f}, ψ={psi_str}, N={t['n']}")

# ============================================================================
# 12. INTERACCIÓN PANDEMIA
# ============================================================================
dpost = (df_an['Fecha'] >= fecha_corte).astype(int)
y = df_an['error']
X = pd.DataFrame({'const':1.0,'revision':df_an['revision'],
                  'post':dpost,'rev_x_post':df_an['revision']*dpost}, index=y.index)
mask = y.notna() & X['revision'].notna()
y_i, X_i = y[mask], X[mask]
m_inter = OLS(y_i, X_i).fit()
V_inter = hac_cov(m_inter)
se_inter = np.sqrt(np.diag(V_inter))
p_inter = 2*(1-stats.norm.cdf(np.abs(m_inter.params.values/se_inter)))
R_in = np.array([[0,0,1,0],[0,0,0,1]])
chi_in, _, p_in = wald_test_hac(m_inter, V_inter, R_in, np.zeros(2))
inter_dict = {'params':m_inter.params.tolist(),'se':se_inter.tolist(),
              'p':p_inter.tolist(),'wald_regime_chi2':float(chi_in),
              'wald_regime_p':float(p_in),'r2':float(m_inter.rsquared),'n':int(m_inter.nobs)}
print(f"\n=== INTERACCIÓN PANDEMIA ===")
print(f"  Wald conjunto cambio régimen: χ²(2)={chi_in:.3f}, p={p_in:.4f}")

# ============================================================================
# 13. TESTS CHOW EXÓGENOS EN CAMBIOS METODOLÓGICOS DE LA EEM
# ============================================================================
print("\n=== TEST CHOW EXÓGENO EN FECHAS DE CAMBIO METODOLÓGICO EEM ===")
def chow_test(serie, fechas, fecha_corte):
    """Chow F-test con bandwidth equiv. a HAC bw."""
    s = serie.dropna().reset_index(drop=True)
    f = fechas.reset_index(drop=True)
    pre  = s[f < fecha_corte]
    post = s[f >= fecha_corte]
    if len(pre) < 5 or len(post) < 5:
        return None
    n1, n2 = len(pre), len(post)
    ssr_pre  = np.sum((pre - pre.mean())**2)
    ssr_post = np.sum((post - post.mean())**2)
    ssr_pool = np.sum((s - s.mean())**2)
    F = ((ssr_pool - (ssr_pre + ssr_post)) / 1) / ((ssr_pre + ssr_post) / (n1 + n2 - 2))
    p = 1 - stats.f.cdf(F, 1, n1+n2-2)
    return {'F':float(F), 'p':float(p), 'n1':n1, 'n2':n2, 'fecha':fecha_corte.strftime('%Y-%m')}

chow_2014 = chow_test(df_an['error'], df_an['Fecha'], pd.Timestamp('2014-01-01'))
chow_2017 = chow_test(df_an['error'], df_an['Fecha'], pd.Timestamp('2017-01-01'))
print(f"  Chow exógeno 2014-01 (rediseño EEM): F={chow_2014['F']:.3f}, p={chow_2014['p']:.4f}")
print(f"  Chow exógeno 2017-01 (rediseño EEM): F={chow_2017['F']:.3f}, p={chow_2017['p']:.4f}")

# ============================================================================
# 14. DIAGNÓSTICOS MZ
# ============================================================================
y = df_an['pi_t']
X = pd.DataFrame({'const':1.0,'E_pi':df_an['E_pi_t_dado_t12']}, index=y.index)
mask = y.notna() & X['E_pi'].notna()
y, X = y[mask], X[mask]
m_mz = OLS(y, X).fit()
bp_st, bp_p, _, _ = het_breuschpagan(m_mz.resid, m_mz.model.exog)
bg_st, bg_p, _, _ = acorr_breusch_godfrey(m_mz, nlags=12)
reset_t = linear_reset(m_mz, power=[2,3], use_f=True)
jb_st, jb_p, _, _ = jarque_bera(m_mz.resid)
lb = acorr_ljungbox(m_mz.resid, lags=[12], return_df=True)
diag = {'bp':(float(bp_st),float(bp_p)),'bg':(float(bg_st),float(bg_p)),
        'reset':(float(reset_t.fvalue),float(reset_t.pvalue)),
        'jb':(float(jb_st),float(jb_p)),
        'lb':(float(lb['lb_stat'].iloc[0]), float(lb['lb_pvalue'].iloc[0]))}

# ============================================================================
# 15. QUANDT-ANDREWS
# ============================================================================
def quandt_andrews(serie, fechas, trim=0.15):
    s = serie.dropna().reset_index(drop=True)
    n = len(s)
    f = fechas.reset_index(drop=True)
    start = int(n*trim); end = int(n*(1-trim))
    f_stats = []
    for tau in range(start, end):
        d = (np.arange(n) >= tau).astype(int)
        X = sm.add_constant(d)
        try:
            mf = OLS(s, X).fit()
            mr = OLS(s, np.ones(n)).fit()
            f_stats.append((tau, ((mr.ssr-mf.ssr)/1)/(mf.ssr/(n-2)), f.iloc[tau]))
        except: pass
    f_arr = np.array([x[1] for x in f_stats])
    sup_f = np.max(f_arr)
    arg = np.argmax(f_arr)
    tau_star, fecha_qb = f_stats[arg][0], f_stats[arg][2]
    if sup_f > 12.16: pa = '< 0.01'
    elif sup_f > 8.85: pa = '< 0.05'
    elif sup_f > 7.04: pa = '< 0.10'
    else: pa = '> 0.10'
    return sup_f, tau_star, fecha_qb, pa

sup_f, tau_star, fecha_qb, p_andrews = quandt_andrews(df_an['error'], df_an['Fecha'])
print(f"\n=== QUANDT-ANDREWS ===")
print(f"  supF={sup_f:.3f}, fecha={fecha_qb.strftime('%Y-%m')}, p_Andrews={p_andrews}")

# ============================================================================
# 16. OUT-OF-SAMPLE Y DIEBOLD-MARIANO
# ============================================================================
print("\n=== OUT-OF-SAMPLE Y DIEBOLD-MARIANO ===")
fecha_split = pd.Timestamp('2019-01-01')
oos = df_an[df_an['Fecha'] >= fecha_split].copy().reset_index(drop=True)

df_an['rw_forecast'] = df_an['pi_t'].shift(12)
df_an['ancla_forecast'] = 4.0

def ar_forecast_recursive(df_full, fecha_t, h=12, lag=1):
    fecha_train_end = fecha_t - pd.DateOffset(months=h)
    train = df_full[df_full['Fecha'] <= fecha_train_end]['pi_t'].dropna()
    if len(train) < lag + 12: return np.nan
    y = train.iloc[lag:].values
    X_lags = np.column_stack([train.shift(k).iloc[lag:].values for k in range(1, lag+1)])
    X = np.column_stack([np.ones(len(y)), X_lags])
    valid = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
    y, X = y[valid], X[valid]
    if len(y) < lag + 5: return np.nan
    try:
        b = np.linalg.lstsq(X, y, rcond=None)[0]
        last_obs = train.iloc[-lag:].values[::-1]
        for _ in range(h):
            x = np.concatenate([[1.0], last_obs[:lag]])
            yh = float(x @ b)
            last_obs = np.concatenate([[yh], last_obs[:-1]])
        return yh
    except: return np.nan

oos['ar1_forecast'] = [ar_forecast_recursive(df_an, f, h=12, lag=1) for f in oos['Fecha']]
oos = oos.merge(df_an[['Fecha','rw_forecast','ancla_forecast']], on='Fecha', how='left')
oos['err_eem']   = oos['pi_t'] - oos['E_pi_t_dado_t12']
oos['err_rw']    = oos['pi_t'] - oos['rw_forecast']
oos['err_ar1']   = oos['pi_t'] - oos['ar1_forecast']
oos['err_ancla'] = oos['pi_t'] - oos['ancla_forecast']
oos_clean = oos.dropna(subset=['err_eem','err_rw','err_ar1','err_ancla'])

def metricas(err):
    err = err.dropna()
    return {'RMSE':float(np.sqrt(np.mean(err**2))),'MAE':float(np.mean(np.abs(err))),
            'ME':float(np.mean(err)),'N':len(err)}

m_eem = metricas(oos_clean['err_eem']); m_rw = metricas(oos_clean['err_rw'])
m_ar1 = metricas(oos_clean['err_ar1']); m_ancla = metricas(oos_clean['err_ancla'])

def diebold_mariano(err1, err2, h=12):
    e1, e2 = err1.dropna().values, err2.dropna().values
    n = min(len(e1), len(e2)); e1, e2 = e1[:n], e2[:n]
    d = e1**2 - e2**2
    mean_d = np.mean(d); bw = h-1
    gamma_0 = np.var(d, ddof=1); lrv = gamma_0
    for k in range(1, bw+1):
        cov = np.cov(d[k:], d[:-k], ddof=1)[0,1]
        weight = 1 - k/(bw+1)
        lrv += 2 * weight * cov
    lrv = max(lrv, 1e-8)
    dm_stat = mean_d / np.sqrt(lrv/n)
    K = ((n + 1 - 2*h + (h*(h-1))/n) / n)**0.5
    dm_corr = K * dm_stat
    p_two = 2*(1 - stats.t.cdf(abs(dm_corr), df=n-1))
    return {'mean_d':float(mean_d),'dm':float(dm_stat),'dm_corr':float(dm_corr),
            'p_value':float(p_two),'n':n}

dm1 = diebold_mariano(oos_clean['err_eem'], oos_clean['err_rw'])
dm2 = diebold_mariano(oos_clean['err_eem'], oos_clean['err_ar1'])
dm3 = diebold_mariano(oos_clean['err_eem'], oos_clean['err_ancla'])
dm4 = diebold_mariano(oos_clean['err_rw'], oos_clean['err_ancla'])

print(f"  RMSE: EEM={m_eem['RMSE']:.2f}, RW={m_rw['RMSE']:.2f}, AR(1)={m_ar1['RMSE']:.2f}, Ancla={m_ancla['RMSE']:.2f}")
print(f"  DM EEM vs RW: {dm1['dm_corr']:.2f} (p={dm1['p_value']:.3f})")
print(f"  DM EEM vs Ancla: {dm3['dm_corr']:.2f} (p={dm3['p_value']:.3f})")

oos_pre = oos_clean[oos_clean['Fecha'] < fecha_corte]
oos_post = oos_clean[oos_clean['Fecha'] >= fecha_corte]
m_eem_pre = metricas(oos_pre['err_eem']); m_rw_pre = metricas(oos_pre['err_rw'])
m_eem_post = metricas(oos_post['err_eem']); m_rw_post = metricas(oos_post['err_rw'])
dm_pre = diebold_mariano(oos_pre['err_eem'], oos_pre['err_rw']) if len(oos_pre)>12 else None
dm_post = diebold_mariano(oos_post['err_eem'], oos_post['err_rw']) if len(oos_post)>12 else None

dm_results = {
    'oos_completa': {'EEM':m_eem,'RW':m_rw,'AR1':m_ar1,'Ancla':m_ancla,
                     'DM_EEM_vs_RW':dm1,'DM_EEM_vs_AR1':dm2,
                     'DM_EEM_vs_Ancla':dm3,'DM_RW_vs_Ancla':dm4},
    'oos_pre':  {'EEM':m_eem_pre,'RW':m_rw_pre,'DM_EEM_vs_RW':dm_pre},
    'oos_post': {'EEM':m_eem_post,'RW':m_rw_post,'DM_EEM_vs_RW':dm_post},
}

# ============================================================================
# 17. CORRECCIONES POR PRUEBAS MÚLTIPLES
# ============================================================================
print("\n=== CORRECCIONES POR PRUEBAS MÚLTIPLES ===")
# Recolectar p-valores principales
p_principales = {
    't1_pre_alpha': t1_pre['p'],
    't1_full_alpha': t1_full['p'],
    't1_post_alpha': t1_post['p'],
    't2_pre_wald_H': t2_pre['wald_p_hodrick'],
    't2_post_wald_H': t2_post['wald_p_hodrick'],
    't2_full_wald_H': t2_full['wald_p_hodrick'],
    't3_full_rho': t3_full['p_rho'],
    't4_wald': pw4,
    't5_pre_lambda_H': t5_pre['p_lambda_hodrick'],
    't5_post_lambda_H': t5_post['p_lambda_hodrick'],
    't5_full_lambda_H': t5_full['p_lambda_hodrick'],
    'interaccion': p_in,
    'chow_2014': chow_2014['p'],
    'chow_2017': chow_2017['p'],
}
m_tests = len(p_principales)
print(f"  Familia de tests: m = {m_tests}")
print(f"  α familia-wise (Bonferroni 5%): {0.05/m_tests:.5f}")
print(f"  Tests con p < α/m (Bonferroni significativos al 5%):")
for k, p in sorted(p_principales.items(), key=lambda x: x[1]):
    sig_bonf = '***' if p < 0.01/m_tests else ('**' if p < 0.05/m_tests else ('*' if p < 0.10/m_tests else ''))
    print(f"    {k}: p={p:.5f} {sig_bonf}")

# Benjamini-Hochberg FDR
ps_sorted = sorted(p_principales.items(), key=lambda x: x[1])
print(f"\n  Benjamini-Hochberg FDR (q=5%):")
for i, (k, p) in enumerate(ps_sorted):
    threshold = 0.05 * (i+1) / m_tests
    pass_bh = p <= threshold
    print(f"    rank={i+1}, {k}: p={p:.5f}, threshold={threshold:.5f}, {'pasa BH' if pass_bh else 'no pasa'}")

bonf_dict = {'m_tests':m_tests, 'alpha_5pct_bonf':0.05/m_tests,
              'p_values':p_principales}

# ============================================================================
# 18. EXPORTAR
# ============================================================================
psi_pre  = 1/(1+t5_pre['lambda'])  if t5_pre['lambda']>-1 else None
psi_post = 1/(1+t5_post['lambda']) if t5_post['lambda']>-1 else None

resultados = {
    'meta': {
        'fecha_inicio': df_an['Fecha'].min().strftime('%Y-%m'),
        'fecha_fin': df_an['Fecha'].max().strftime('%Y-%m'),
        'n_total': len(df_an), 'n_pre': len(df_pre), 'n_post': len(df_post),
        'fuente_ipc': 'IPC oficial empalmado por el BCRD (base oct 2019 - sep 2020 = 100, transformada de bases anteriores)',
        'fuente_tpm': 'TPM oficial del BCRD, serie mensual 2004-2026',
        'fuente_tc': 'Tipo de cambio nominal (compra), promedio mensual a partir del histórico diario del BCRD',
        'fuente_pib': 'Índice de volumen del PIB real, BCRD, frecuencia trimestral mensualizada',
    },
    'descriptivas': df_desc.to_dict('records'),
    'raices': raices.to_dict('records'),
    't1_insesgamiento': {'full':t1_full,'pre':t1_pre,'post':t1_post},
    't2_mincer_zarnowitz': {'full':t2_full,'pre':t2_pre,'post':t2_post},
    't3_persistencia': {'full':t3_full,'pre':t3_pre},
    't4_eficiencia_info_oficial': t4_dict,
    't5_coibion_gorod': {'full':t5_full,'pre':t5_pre,'post':t5_post,
                         'psi_pre':psi_pre,'psi_post':psi_post},
    'interaccion_pandemia': inter_dict,
    'chow_eem_2014': chow_2014,
    'chow_eem_2017': chow_2017,
    'diagnosticos': {k: list(v) for k,v in diag.items()},
    'quiebre': {'sup_f':float(sup_f),'fecha':fecha_qb.strftime('%Y-%m'),
                'tau':int(tau_star),'p_andrews':p_andrews},
    'diebold_mariano': dm_results,
    'pruebas_multiples': bonf_dict,
}
# Sanear NaN
def san(o):
    if isinstance(o, dict): return {k:san(v) for k,v in o.items()}
    if isinstance(o, list): return [san(x) for x in o]
    if isinstance(o, float) and (np.isnan(o) or np.isinf(o)): return None
    return o
resultados = san(resultados)

with open(RESULTS + 'resultados_econometricos.json','w') as f:
    json.dump(resultados, f, indent=2, default=str)

# ============================================================================
# 19. FIGURAS
# ============================================================================
plt.rcParams.update({'font.family':'serif','font.size':10,
                     'figure.dpi':150,'savefig.dpi':300,
                     'savefig.bbox':'tight','savefig.facecolor':'white'})
COLOR_OBS, COLOR_EXP, COLOR_ERR = '#C8102E', '#003DA5', '#FFB81C'
break_date = pd.Timestamp('2020-03-01')

# Figura 1
fig, ax = plt.subplots(figsize=(11, 4.8))
ax.axvspan(break_date, df_an['Fecha'].max(), alpha=0.10, color='grey', zorder=0)
ax.bar(df_an['Fecha'], df_an['error'], color=COLOR_ERR, alpha=0.5,
       label='Error de pronóstico (p.p.)', width=25, zorder=1)
ax.plot(df_an['Fecha'], df_an['pi_t'], color=COLOR_OBS, linewidth=1.6,
        label='Inflación interanual realizada (%)', zorder=3)
ax.plot(df_an['Fecha'], df_an['E_pi_t_dado_t12'], color=COLOR_EXP, linewidth=1.6,
        label='Expectativa a 12m (rezagada 12 meses)', zorder=3)
ax.axhline(0, color='grey', linewidth=0.4)
ax.axvline(break_date, color='black', linestyle='--', linewidth=1, alpha=0.5)
ax.text(break_date - pd.Timedelta(days=60), ax.get_ylim()[1]*0.9,
        'Mar 2020', ha='right', fontsize=8.5, style='italic')
ax.set_ylabel('Variación interanual (%) / Error (p.p.)')
ax.set_title('Inflación realizada vs. expectativa formada 12 meses antes — República Dominicana',
             fontweight='bold', fontsize=12)
ax.legend(loc='upper left', frameon=True, framealpha=0.9, fontsize=9)
ax.grid(alpha=0.25)
ax.xaxis.set_major_locator(mdates.YearLocator(2))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
fig.text(0.5, -0.05,
         'Fuente: cálculos propios con IPC oficial empalmado del BCRD y EEM-BCRD.',
         ha='center', fontsize=8.3, style='italic', color='#444')
plt.savefig(FIGURES + 'fig1_inflacion_expectativa.png', bbox_inches='tight')
plt.close()

# Figura 2 - MZ
fig, ax = plt.subplots(figsize=(7, 5.5))
ax.scatter(df_an['E_pi_t_dado_t12'], df_an['pi_t'],
           c=df_an['Fecha'].map(lambda x: 1 if x >= break_date else 0),
           cmap='coolwarm', alpha=0.6, s=35, edgecolor='white', linewidth=0.5)
xr = np.linspace(df_an['E_pi_t_dado_t12'].min()-0.5,
                  df_an['E_pi_t_dado_t12'].max()+0.5, 50)
ax.plot(xr, xr, color='grey', linestyle='--', linewidth=1, label='45° (predicción perfecta)')
ax.plot(xr, t2_full['alpha'] + t2_full['beta']*xr, color=COLOR_OBS, linewidth=2,
        label=f"OLS: α={t2_full['alpha']:.2f}, β={t2_full['beta']:.2f}")
ax.set_xlabel('Expectativa de inflación a 12m (rezagada)')
ax.set_ylabel('Inflación interanual realizada (%)')
ax.set_title(f"Mincer-Zarnowitz   (Wald χ²={t2_full['wald_chi2']:.2f}, p={t2_full['wald_p']:.4f})",
             fontweight='bold')
ax.legend(loc='upper left', fontsize=9)
ax.grid(alpha=0.25)
plt.savefig(FIGURES + 'fig2_mz_scatter.png', bbox_inches='tight')
plt.close()

# Figura 3 - CG
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
for ax_i, (sub_data, etiq, t_dict) in enumerate([
    (df_pre,  f"Pre-pandemia ({df_pre['Fecha'].min().strftime('%Ym%m')} – {df_pre['Fecha'].max().strftime('%Ym%m')})",  t5_pre),
    (df_post, f"Post-pandemia ({df_post['Fecha'].min().strftime('%Ym%m')} – {df_post['Fecha'].max().strftime('%Ym%m')})", t5_post),
]):
    ax = axes[ax_i]
    sub = sub_data.dropna(subset=['revision','error'])
    ax.scatter(sub['revision'], sub['error'], alpha=0.55, color=COLOR_EXP, s=35, edgecolor='white', linewidth=0.5)
    xr = np.linspace(sub['revision'].min()-0.1, sub['revision'].max()+0.1, 50)
    sm_p = '***' if t_dict['p_lambda_hodrick']<0.01 else ('**' if t_dict['p_lambda_hodrick']<0.05 else ('*' if t_dict['p_lambda_hodrick']<0.10 else 'n.s.'))
    psi_str = f"ψ={1/(1+t_dict['lambda']):.2f}" if t_dict['lambda']>-1 else "ψ=n.a."
    ax.plot(xr, t_dict['alpha'] + t_dict['lambda']*xr, color=COLOR_OBS, linewidth=2,
            label=f"λ={t_dict['lambda']:.2f} ({sm_p}), {psi_str}")
    ax.axhline(0, color='grey', linewidth=0.4, linestyle='--')
    ax.axvline(0, color='grey', linewidth=0.4, linestyle='--')
    ax.set_xlabel('Revisión de expectativa  rev$_t$ (p.p.)')
    ax.set_ylabel('Error de pronóstico  e$_t$ (p.p.)')
    ax.set_title(etiq, fontweight='bold')
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(alpha=0.25)
fig.suptitle('Test de rigidez informacional de Coibion-Gorodnichenko', fontsize=13, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(FIGURES + 'fig3_cg_subperiodos.png', bbox_inches='tight')
plt.close()

# Figura 4 - rolling lambda
def lambda_rolling(d, ventana=36):
    out = []
    d = d.dropna(subset=['error','revision']).reset_index(drop=True)
    for i in range(ventana, len(d)):
        sub = d.iloc[i-ventana:i]
        try:
            X = sm.add_constant(sub['revision'])
            m = OLS(sub['error'], X).fit()
            lam = m.params.iloc[1]
            psi = 1/(1+lam) if lam>-1 else np.nan
            out.append({'Fecha':sub['Fecha'].iloc[-1],'lambda':lam,'psi':psi})
        except: pass
    return pd.DataFrame(out)

df_roll = lambda_rolling(df_an, ventana=36)
fig, ax1 = plt.subplots(figsize=(11, 4.5))
ax1.axvspan(break_date, df_an['Fecha'].max(), alpha=0.10, color='grey', zorder=0)
ax1.plot(df_roll['Fecha'], df_roll['lambda'], color=COLOR_OBS, linewidth=1.8, label='λ (rigidez)')
ax1.set_ylabel('λ - rigidez informacional', color=COLOR_OBS)
ax1.tick_params(axis='y', labelcolor=COLOR_OBS)
ax1.axhline(0, color='grey', linewidth=0.4)
ax1.grid(alpha=0.25)
ax2 = ax1.twinx()
ax2.plot(df_roll['Fecha'], df_roll['psi'], color=COLOR_EXP, linewidth=1.8, linestyle='--', label='ψ = 1/(1+λ)')
ax2.set_ylabel('ψ - probabilidad de actualización', color=COLOR_EXP)
ax2.tick_params(axis='y', labelcolor=COLOR_EXP)
ax1.set_title('Evolución de la rigidez informacional — ventana móvil de 36 meses', fontweight='bold')
ax1.xaxis.set_major_locator(mdates.YearLocator(2))
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
plt.savefig(FIGURES + 'fig4_lambda_rolling.png', bbox_inches='tight')
plt.close()

# Figura 5 - OOS
fig, ax = plt.subplots(figsize=(11, 4.8))
ax.plot(oos_clean['Fecha'], oos_clean['pi_t'], color=COLOR_OBS, linewidth=1.8, label='Inflación realizada')
ax.plot(oos_clean['Fecha'], oos_clean['E_pi_t_dado_t12'], color=COLOR_EXP, linewidth=1.5, label=f"EEM consenso (RMSE={m_eem['RMSE']:.2f})")
ax.plot(oos_clean['Fecha'], oos_clean['rw_forecast'], color='#666666', linewidth=1.2, linestyle='--', label=f"Random walk (RMSE={m_rw['RMSE']:.2f})")
ax.plot(oos_clean['Fecha'], oos_clean['ar1_forecast'], color='#2E8B57', linewidth=1.2, linestyle=':', label=f"AR(1) recursivo (RMSE={m_ar1['RMSE']:.2f})")
ax.axhline(4.0, color='#FFB81C', linewidth=1.2, linestyle='-.', label=f"Ancla 4% (RMSE={m_ancla['RMSE']:.2f})", alpha=0.7)
ax.axvline(break_date, color='black', linestyle='--', linewidth=1, alpha=0.5)
ax.set_ylabel('Inflación interanual (%)')
ax.set_title('Comparación de pronósticos out-of-sample (2019m1 – 2026m3)', fontweight='bold')
ax.legend(loc='upper left', fontsize=9)
ax.grid(alpha=0.25)
ax.xaxis.set_major_locator(mdates.YearLocator(1))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
plt.savefig(FIGURES + 'fig5_oos_comparacion.png', bbox_inches='tight')
plt.close()

print("\n\nANÁLISIS COMPLETO. Resultados en (RESULTS)resultados_econometricos.json")
