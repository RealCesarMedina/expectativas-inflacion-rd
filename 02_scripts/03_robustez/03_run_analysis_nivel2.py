"""
Análisis suplementario nivel 2:
- ARDL de TPM en eficiencia informacional con rezagos t-12 a t-18
- Bootstrap por bloques para inferencia en muestras pequeñas
- Kiefer-Vogelsang (2005) con valores críticos no estándar
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
import statsmodels.api as sm
from statsmodels.regression.linear_model import OLS
from statsmodels.stats.sandwich_covariance import cov_hac
from scipy import stats
import json
import warnings
warnings.filterwarnings("ignore")

# ============================================================================
# Reconstruir muestra
# ============================================================================
ds = pd.read_csv(RESULTS + 'Dataset_Consolidado_BCRD.csv')
ds['Fecha'] = pd.to_datetime(ds['Fecha'])
eem = pd.read_excel(DATA_RAW + 'Historico-EEM_BCRD.xlsx', sheet_name='Mediana', header=[7,8])
eem.columns = [' '.join(c).replace('Unnamed: 0_level_1','').replace('Unnamed: 1_level_1','').strip() for c in eem.columns]
eem = eem.dropna(subset=['Año','Mes']).copy()
eem['Año'] = eem['Año'].astype(int); eem['Mes'] = eem['Mes'].astype(int)
eem['Fecha'] = pd.to_datetime(dict(year=eem['Año'], month=eem['Mes'], day=1))
eem = eem.sort_values('Fecha').reset_index(drop=True)
eem.rename(columns={'Inflación En 12 meses': 'E_pi_12m'}, inplace=True)
df = eem.merge(ds[['Fecha','pi_t','TPM_obs','var_tc','var_pib']], on='Fecha', how='left')
df['E_pi_t_dado_t12'] = df['E_pi_12m'].shift(12)
df['error'] = df['pi_t'] - df['E_pi_t_dado_t12']
df['revision'] = df['E_pi_12m'] - df['E_pi_12m'].shift(1)
df_an = df[df['error'].notna()].copy().reset_index(drop=True)
fecha_corte = pd.Timestamp('2020-03-01')

def hac_cov(m, lag_min=11):
    nlags = max(lag_min, int(np.ceil(4*(m.nobs/100)**(2/9))))
    return cov_hac(m, nlags=nlags)

def hac_cov_hodrick(m, h=12):
    return cov_hac(m, nlags=2*h-1)

# ============================================================================
# 2.1. ARDL de TPM en test de eficiencia informacional
# ============================================================================
print("=== 2.1. ARDL DE TPM (rezagos 12-18) EN EFICIENCIA INFORMACIONAL ===\n")

# Construir variables rezagadas
for j in range(12, 19):
    df_an[f'tpm_lag{j}'] = df['TPM_obs'].reindex(df_an.index).shift(j-1)  # ya rezaga 1 desde el merge

# Mejor: construir desde pi_t las series limpiamente
df_full = ds.copy().sort_values('Fecha').reset_index(drop=True)
df_full = df_full.merge(eem[['Fecha','E_pi_12m']], on='Fecha', how='left')
df_full['E_pi_t_dado_t12'] = df_full['E_pi_12m'].shift(12)
df_full['error'] = df_full['pi_t'] - df_full['E_pi_t_dado_t12']
for j in range(12, 19):
    df_full[f'tpm_lag{j}'] = df_full['TPM_obs'].shift(j)
df_full['pi_lag13'] = df_full['pi_t'].shift(13)
df_full['vtc_lag13'] = df_full['var_tc'].shift(13)
df_full['vpib_lag13'] = df_full['var_pib'].shift(13)

# Subset analítico: error no nulo + todos los rezagos disponibles
cols_ardl = ['error'] + [f'tpm_lag{j}' for j in range(12,19)] + ['pi_lag13','vtc_lag13','vpib_lag13']
ardl_data = df_full[['Fecha'] + cols_ardl].dropna().reset_index(drop=True)
print(f"  N efectivo ARDL: {len(ardl_data)}")

# Estimar modelo completo con todos los rezagos
y = ardl_data['error']
X_ardl = pd.DataFrame({
    'const': 1.0,
    **{f'tpm_lag{j}': ardl_data[f'tpm_lag{j}'] for j in range(12, 19)},
    'pi_lag13': ardl_data['pi_lag13'],
    'vtc_lag13': ardl_data['vtc_lag13'],
    'vpib_lag13': ardl_data['vpib_lag13'],
}, index=y.index)
m_ardl = OLS(y, X_ardl).fit()
V_ardl = hac_cov(m_ardl)
se_ardl = np.sqrt(np.diag(V_ardl))

print(f"\n  Coeficientes y p-valores HAC:")
nombres = X_ardl.columns.tolist()
for nom, b, s in zip(nombres, m_ardl.params.values, se_ardl):
    z = b/s if s>0 else 0
    p = 2*(1-stats.norm.cdf(abs(z)))
    sig = '***' if p<0.01 else '**' if p<0.05 else '*' if p<0.10 else ''
    print(f"    {nom:15s} = {b:8.3f} (SE={s:.3f}, p={p:.4f}) {sig}")

# Test conjunto sobre TPM(t-12 a t-18)
indices_tpm = [i for i, n in enumerate(nombres) if n.startswith('tpm_lag')]
R_mat = np.zeros((len(indices_tpm), len(nombres)))
for i, idx in enumerate(indices_tpm): R_mat[i, idx] = 1
beta = m_ardl.params.values
diff = R_mat @ beta
M = R_mat @ V_ardl @ R_mat.T
chi2_tpm = float(diff @ np.linalg.inv(M) @ diff)
p_tpm = 1 - stats.chi2.cdf(chi2_tpm, len(indices_tpm))
print(f"\n  Test conjunto H₀: γ_{{j=12,...,18}} = 0:  χ²(7) = {chi2_tpm:.2f}, p = {p_tpm:.4f}")
print(f"  R² del modelo ARDL: {m_ardl.rsquared:.4f}")

# Comparar con modelo simple (solo TPM_lag13)
X_simple = pd.DataFrame({
    'const': 1.0, 'tpm_lag13': ardl_data['tpm_lag13'],
    'pi_lag13': ardl_data['pi_lag13'], 'vtc_lag13': ardl_data['vtc_lag13'],
    'vpib_lag13': ardl_data['vpib_lag13'],
}, index=y.index)
m_simple = OLS(y, X_simple).fit()
print(f"  R² del modelo simple (solo lag 13): {m_simple.rsquared:.4f}")
print(f"  Incremento de R²: {m_ardl.rsquared - m_simple.rsquared:.4f}")

# Selección por BIC
print(f"\n  BIC modelo ARDL: {m_ardl.bic:.2f}")
print(f"  BIC modelo simple: {m_simple.bic:.2f}")

# Identificar el rezago dominante
print(f"\n  Rezago dominante (mayor |coef|):")
coefs_tpm = {f'tpm_lag{j}': m_ardl.params[f'tpm_lag{j}'] for j in range(12,19)}
dominante = max(coefs_tpm.items(), key=lambda x: abs(x[1]))
print(f"    {dominante[0]} = {dominante[1]:.3f}")

ardl_resultados = {
    'n_efectivo': int(len(ardl_data)),
    'wald_conjunto_tpm_chi2': float(chi2_tpm),
    'wald_conjunto_tpm_df': len(indices_tpm),
    'wald_conjunto_tpm_p': float(p_tpm),
    'r2_ardl': float(m_ardl.rsquared),
    'r2_simple': float(m_simple.rsquared),
    'r2_incremento': float(m_ardl.rsquared - m_simple.rsquared),
    'bic_ardl': float(m_ardl.bic),
    'bic_simple': float(m_simple.bic),
    'rezago_dominante': dominante[0],
    'rezago_dominante_coef': float(dominante[1]),
    'coeficientes_tpm': {f'tpm_lag{j}': float(m_ardl.params[f'tpm_lag{j}']) for j in range(12,19)},
    'p_tpm_individuales': {f'tpm_lag{j}': float(2*(1-stats.norm.cdf(abs(m_ardl.params[f'tpm_lag{j}']/se_ardl[nombres.index(f'tpm_lag{j}')])))) for j in range(12,19)},
}

# ============================================================================
# 2.3. BOOTSTRAP POR BLOQUES — CG post-pandemia y TPM_lag13 en eficiencia
# ============================================================================
print("\n=== 2.3. BOOTSTRAP POR BLOQUES (Politis-Romano) ===\n")

def block_bootstrap_coef(y, X, regresor_idx, n_boot=5000, block_len=18, seed=123):
    """Bootstrap estacionario sobre el coeficiente de un regresor específico."""
    rng = np.random.RandomState(seed)
    n = len(y)
    coefs = np.empty(n_boot)
    for b in range(n_boot):
        # Bootstrap por bloques fijos (overlap permitido)
        n_blocks = int(np.ceil(n / block_len))
        starts = rng.randint(0, n - block_len + 1, n_blocks)
        idx = np.concatenate([np.arange(s, s+block_len) for s in starts])[:n]
        X_b = X.iloc[idx].reset_index(drop=True)
        y_b = y.iloc[idx].reset_index(drop=True)
        try:
            m_b = OLS(y_b, X_b).fit()
            coefs[b] = m_b.params.iloc[regresor_idx]
        except:
            coefs[b] = np.nan
    coefs = coefs[~np.isnan(coefs)]
    return coefs

# CG post-pandemia
print("  CG post-pandemia (λ):")
post = df_an[df_an['Fecha'] >= fecha_corte].dropna(subset=['error','revision']).reset_index(drop=True)
y_post = post['error']
X_post = pd.DataFrame({'const': 1.0, 'rev': post['revision']}, index=y_post.index)
m_post = OLS(y_post, X_post).fit()
lam_post = m_post.params['rev']
print(f"    Estimación puntual: λ = {lam_post:.3f}")

coefs_boot_cg = block_bootstrap_coef(y_post, X_post, 1, n_boot=5000, block_len=18, seed=123)
ic_95_cg = (np.percentile(coefs_boot_cg, 2.5), np.percentile(coefs_boot_cg, 97.5))
ic_99_cg = (np.percentile(coefs_boot_cg, 0.5), np.percentile(coefs_boot_cg, 99.5))
p_boot_cg_2tailed = 2 * min((coefs_boot_cg <= 0).mean(), (coefs_boot_cg >= 0).mean())
print(f"    IC 95% bootstrap: [{ic_95_cg[0]:.3f}, {ic_95_cg[1]:.3f}]")
print(f"    IC 99% bootstrap: [{ic_99_cg[0]:.3f}, {ic_99_cg[1]:.3f}]")
print(f"    p-valor bootstrap (H₀: λ=0): {p_boot_cg_2tailed:.4f}")

# TPM_lag13 en eficiencia informacional
print("\n  TPM rezagada en eficiencia informacional (γ):")
ef_data = df_full[['Fecha','error','pi_lag13','tpm_lag13','vtc_lag13','vpib_lag13']].dropna().reset_index(drop=True)
y_ef = ef_data['error']
X_ef = pd.DataFrame({
    'const': 1.0, 'pi_lag13': ef_data['pi_lag13'],
    'tpm_lag13': ef_data['tpm_lag13'], 'vtc_lag13': ef_data['vtc_lag13'],
    'vpib_lag13': ef_data['vpib_lag13'],
}, index=y_ef.index)
m_ef = OLS(y_ef, X_ef).fit()
print(f"    Estimación puntual: γ_TPM = {m_ef.params['tpm_lag13']:.3f}")

coefs_boot_tpm = block_bootstrap_coef(y_ef, X_ef, 2, n_boot=5000, block_len=18, seed=123)  # idx 2 = tpm_lag13
ic_95_tpm = (np.percentile(coefs_boot_tpm, 2.5), np.percentile(coefs_boot_tpm, 97.5))
ic_99_tpm = (np.percentile(coefs_boot_tpm, 0.5), np.percentile(coefs_boot_tpm, 99.5))
p_boot_tpm = 2 * min((coefs_boot_tpm <= 0).mean(), (coefs_boot_tpm >= 0).mean())
print(f"    IC 95% bootstrap: [{ic_95_tpm[0]:.3f}, {ic_95_tpm[1]:.3f}]")
print(f"    IC 99% bootstrap: [{ic_99_tpm[0]:.3f}, {ic_99_tpm[1]:.3f}]")
print(f"    p-valor bootstrap (H₀: γ=0): {p_boot_tpm:.4f}")

bootstrap_resultados = {
    'metodo': 'block bootstrap, fixed length b=18 (=1.5*h)',
    'n_replicas': 5000,
    'cg_post_pandemia': {
        'lambda_punto': float(lam_post),
        'IC_95': [float(ic_95_cg[0]), float(ic_95_cg[1])],
        'IC_99': [float(ic_99_cg[0]), float(ic_99_cg[1])],
        'p_bootstrap': float(p_boot_cg_2tailed),
    },
    'tpm_eficiencia': {
        'gamma_punto': float(m_ef.params['tpm_lag13']),
        'IC_95': [float(ic_95_tpm[0]), float(ic_95_tpm[1])],
        'IC_99': [float(ic_99_tpm[0]), float(ic_99_tpm[1])],
        'p_bootstrap': float(p_boot_tpm),
    }
}

# ============================================================================
# 2.5. KIEFER-VOGELSANG (KV) con valores críticos no estándar
# ============================================================================
print("\n=== 2.5. KIEFER-VOGELSANG (b=0.5) ===\n")

def kv_t_test(y, X, b=0.5, kernel='bartlett'):
    """
    Test KV con bandwidth fijo M = b*N.
    Devuelve t-stat y SE para cada coeficiente.
    Valores críticos no estándar de Kiefer-Vogelsang (2005) para Bartlett con b=0.5:
      cv_5pct = 6.811 (tablas de KV 2005, tabla 3, B=0.5)  -- t² (F-test 1-d.o.f.)
    Para 2 colas y t (no F): t_5pct ≈ √6.811 ≈ 2.610.
    """
    n = len(y)
    M = max(2, int(b * n))
    m_ols = OLS(y, X).fit()
    u = m_ols.resid.values
    XX = X.values
    G = np.zeros((XX.shape[1], XX.shape[1]))
    for h_lag in range(-M+1, M):
        if kernel == 'bartlett':
            w = 1 - abs(h_lag)/M
        else:
            w = 1.0
        if w < 0: continue
        if h_lag == 0:
            uu = u * u
            G += np.einsum('i,ij,ik->jk', uu, XX, XX)
        elif h_lag > 0:
            uu = u[h_lag:] * u[:-h_lag]
            G += w * (np.einsum('i,ij,ik->jk', uu, XX[h_lag:], XX[:-h_lag])
                      + np.einsum('i,ij,ik->jk', uu, XX[:-h_lag], XX[h_lag:]))
    # Var-cov KV: (X'X)^-1 G (X'X)^-1
    XtX_inv = np.linalg.inv(XX.T @ XX)
    V_kv = XtX_inv @ G @ XtX_inv
    se_kv = np.sqrt(np.diag(V_kv))
    t_kv = m_ols.params.values / se_kv
    return m_ols.params, se_kv, t_kv, V_kv

# Aplicar KV al CG post-pandemia
print("  CG post-pandemia con KV b=0.5:")
beta_kv, se_kv, t_kv, V_kv = kv_t_test(y_post, X_post, b=0.5)
nombres_post = ['const', 'rev']
for nom, b, s, t in zip(nombres_post, beta_kv.values, se_kv, t_kv):
    print(f"    {nom:10s}: β={b:.3f}, SE_KV={s:.3f}, t_KV={t:.3f}")

# Valor crítico KV-Bartlett con b=0.5: para 2 colas el valor t aproximado al 5% es ~2.61
# (de Kiefer-Vogelsang 2005, tabla 3: F=t² al 5%=6.811 → t=±2.610)
cv_5_kv = 2.610
cv_1_kv = 3.484  # F=12.140 → t=±3.484 (aproximado)
print(f"\n  Valores críticos KV-Bartlett con b=0.5:")
print(f"    5% (2 colas): |t| > {cv_5_kv}")
print(f"    1% (2 colas): |t| > {cv_1_kv}")
t_lambda_kv = t_kv[1]
print(f"  λ post-pandemia: t_KV = {t_lambda_kv:.3f}")
print(f"    {'rechaza' if abs(t_lambda_kv) > cv_5_kv else 'NO rechaza'} al 5%")
print(f"    {'rechaza' if abs(t_lambda_kv) > cv_1_kv else 'NO rechaza'} al 1%")

# Aplicar KV al test de eficiencia informacional
print("\n  Eficiencia informacional con KV b=0.5:")
beta_ef_kv, se_ef_kv, t_ef_kv, V_ef_kv = kv_t_test(y_ef, X_ef, b=0.5)
nombres_ef = ['const','pi_lag13','tpm_lag13','vtc_lag13','vpib_lag13']
for nom, b, s, t in zip(nombres_ef, beta_ef_kv.values, se_ef_kv, t_ef_kv):
    print(f"    {nom:14s}: β={b:.3f}, SE_KV={s:.3f}, t_KV={t:.3f}")

# Test conjunto KV (sólo regresores no-constante: pi_lag13, tpm, vtc, vpib)
R_kv = np.zeros((4, 5))
for i in range(4): R_kv[i, i+1] = 1
beta_v = beta_ef_kv.values
diff_kv = R_kv @ beta_v
M_mat = R_kv @ V_ef_kv @ R_kv.T
chi2_kv = float(diff_kv @ np.linalg.inv(M_mat) @ diff_kv)
# Valor crítico Wald KV (q=4, b=0.5, Bartlett): 31.69 (Kiefer-Vogelsang 2005, tabla 3)
cv_wald_5_kv = 31.69
print(f"\n  Wald conjunto eficiencia KV: χ²(4) = {chi2_kv:.2f}")
print(f"    Valor crítico KV al 5% (q=4, b=0.5): {cv_wald_5_kv}")
print(f"    {'rechaza' if chi2_kv > cv_wald_5_kv else 'NO rechaza'} al 5% bajo KV")

kv_resultados = {
    'metodo': 'Kiefer-Vogelsang (2005), kernel Bartlett, b=0.5',
    'cg_post_pandemia': {
        'lambda': float(beta_kv['rev']),
        'se_kv': float(se_kv[1]),
        't_kv': float(t_kv[1]),
        'cv_5pct': cv_5_kv,
        'cv_1pct': cv_1_kv,
        'rechaza_5pct': bool(abs(t_kv[1]) > cv_5_kv),
        'rechaza_1pct': bool(abs(t_kv[1]) > cv_1_kv),
    },
    'eficiencia_informacional': {
        'wald_chi2_kv': float(chi2_kv),
        'cv_wald_5pct': cv_wald_5_kv,
        'rechaza_5pct': bool(chi2_kv > cv_wald_5_kv),
        'tpm_lag13': {
            'coef': float(beta_ef_kv['tpm_lag13']),
            'se_kv': float(se_ef_kv[2]),
            't_kv': float(t_ef_kv[2]),
            'rechaza_5pct': bool(abs(t_ef_kv[2]) > cv_5_kv),
        }
    }
}

# ============================================================================
# Consolidar al JSON
# ============================================================================
nivel2 = {
    'ardl_tpm_eficiencia': ardl_resultados,
    'bootstrap_bloques': bootstrap_resultados,
    'kiefer_vogelsang': kv_resultados,
}

def san(o):
    if isinstance(o, dict): return {k:san(v) for k,v in o.items()}
    if isinstance(o, list): return [san(x) for x in o]
    if isinstance(o, float) and (np.isnan(o) or np.isinf(o)): return None
    if isinstance(o, (np.bool_,)): return bool(o)
    return o
nivel2 = san(nivel2)

with open(RESULTS + 'resultados_econometricos.json') as f:
    res = json.load(f)
res.update(nivel2)
with open(RESULTS + 'resultados_econometricos.json','w') as f:
    json.dump(res, f, indent=2, default=str)

print("\n\n=== RESUMEN NIVEL 2 ===")
print(f"  ARDL: Wald χ²(7) = {chi2_tpm:.2f}, p = {p_tpm:.4f} (rezago dominante: {dominante[0]} = {dominante[1]:.3f})")
print(f"  R² ARDL = {m_ardl.rsquared:.4f} vs R² simple = {m_simple.rsquared:.4f}")
print(f"  CG post bootstrap: λ = {lam_post:.3f}, IC 95% = [{ic_95_cg[0]:.3f}, {ic_95_cg[1]:.3f}], p = {p_boot_cg_2tailed:.4f}")
print(f"  TPM eficiencia bootstrap: γ = {m_ef.params['tpm_lag13']:.3f}, IC 95% = [{ic_95_tpm[0]:.3f}, {ic_95_tpm[1]:.3f}], p = {p_boot_tpm:.4f}")
print(f"  KV CG post: t = {t_kv[1]:.3f}, {'RECHAZA' if abs(t_kv[1])>cv_5_kv else 'NO rechaza'} al 5%")
print(f"  KV eficiencia: Wald = {chi2_kv:.2f}, {'RECHAZA' if chi2_kv>cv_wald_5_kv else 'NO rechaza'} al 5%")
