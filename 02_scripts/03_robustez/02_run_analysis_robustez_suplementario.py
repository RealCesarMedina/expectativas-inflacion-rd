"""
Análisis suplementario:

1. Bai-Perron extendido a m=4 y m=5 para confirmar que BIC tiene mínimo en el rango.
2. Re-estimación con tres regímenes (2010-2016, 2017-2020m2, 2020m3-2026) para
   neutralizar el Chow 2017.
3. Threshold-MZ con meta del 4% como umbral, dado que RESET rechaza linealidad.
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
df['pi_lag13']  = df['pi_t'].shift(13)
df['tpm_obs_lag13'] = df['TPM_obs'].shift(13)
df['vtc_obs_lag13'] = df['var_tc'].shift(13)
df['vpib_obs_lag13'] = df['var_pib'].shift(13)
df_an = df[df['error'].notna()].copy().reset_index(drop=True)

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
# 1. BAI-PERRON EXTENDIDO m=4, m=5
# ============================================================================
print("=== BAI-PERRON EXTENDIDO ===")
def bai_perron_extendido(serie, fechas, m_max=5, trim=0.10):
    s = serie.dropna().reset_index(drop=True)
    f = fechas.reset_index(drop=True)
    n = len(s)
    h = max(int(n*trim), 5)
    
    def ssr_segmento(i, j):
        if j - i < 2: return 1e10
        seg = s.iloc[i:j]
        return np.sum((seg - seg.mean())**2)
    
    resultados = []
    
    # m=0
    ssr_0 = ssr_segmento(0, n)
    bic = lambda ssr, k: n * np.log(ssr/n) + (2*k+1) * np.log(n)
    resultados.append({'m':0, 'ssr':float(ssr_0), 'bic':float(bic(ssr_0, 0)), 'fechas':[]})
    
    # Procedimiento secuencial: encontrar m=1 óptimo, luego dividir el segmento mayor para m=2, etc.
    quiebres = []
    for m_actual in range(1, m_max+1):
        # Definir segmentos actuales
        if not quiebres:
            segmentos = [(0, n)]
        else:
            puntos = [0] + sorted(quiebres) + [n]
            segmentos = [(puntos[i], puntos[i+1]) for i in range(len(puntos)-1)]
        
        # Buscar el mejor quiebre adicional dentro de cada segmento existente
        mejor_global = (1e10, None, None)  # (ssr, posición, segmento_índice)
        for seg_idx, (a, b) in enumerate(segmentos):
            if b - a < 2*h: continue
            for tau in range(a + h, b - h):
                # SSR si añadimos quiebre en tau
                # Calculamos SSR total con tau como quiebre adicional
                quiebres_test = sorted(quiebres + [tau])
                puntos_test = [0] + quiebres_test + [n]
                ssr_test = sum(ssr_segmento(puntos_test[i], puntos_test[i+1]) 
                              for i in range(len(puntos_test)-1))
                if ssr_test < mejor_global[0]:
                    mejor_global = (ssr_test, tau, seg_idx)
        
        if mejor_global[1] is None: break
        quiebres.append(mejor_global[1])
        ssr_m = mejor_global[0]
        bic_m = bic(ssr_m, m_actual)
        fechas_quiebres = sorted([f.iloc[t].strftime('%Y-%m') for t in quiebres])
        resultados.append({'m':m_actual, 'ssr':float(ssr_m), 'bic':float(bic_m),
                          'fechas': fechas_quiebres})
    
    bp_optimo = min(resultados, key=lambda x: x['bic'])
    return resultados, bp_optimo

bp_resultados, bp_optimo = bai_perron_extendido(df_an['error'], df_an['Fecha'], m_max=5, trim=0.10)
for r in bp_resultados:
    print(f"  m={r['m']}: SSR={r['ssr']:.1f}, BIC={r['bic']:.1f}, fechas={r['fechas']}")
print(f"  >>> Óptimo BIC: m={bp_optimo['m']}, fechas={bp_optimo['fechas']}")

# Análisis: ¿el BIC tiene mínimo claro?
bics = [r['bic'] for r in bp_resultados]
m_min = bics.index(min(bics))
print(f"  >>> mínimo absoluto BIC en m={m_min}")
if m_min == len(bics) - 1:
    print(f"  >>> ATENCIÓN: BIC sigue cayendo en m_max, considerar m mayor")

# ============================================================================
# 2. THREE-RÉGIMEN: 2010-2016, 2017-2020m2, 2020m3-2026
# ============================================================================
print("\n=== TRES REGÍMENES (2010-2016 vs 2017-2020m2 vs 2020m3-2026) ===")
fecha_2017 = pd.Timestamp('2017-01-01')
fecha_2020 = pd.Timestamp('2020-03-01')

reg_pre2017 = df_an[df_an['Fecha'] < fecha_2017].copy()
reg_2017_2020 = df_an[(df_an['Fecha'] >= fecha_2017) & (df_an['Fecha'] < fecha_2020)].copy()
reg_post2020 = df_an[df_an['Fecha'] >= fecha_2020].copy()

def test_ins(d):
    y = d['error']
    X = pd.DataFrame({'const':1.0}, index=y.index)
    m = OLS(y, X, missing='drop').fit()
    V = hac_cov(m); se = float(np.sqrt(V[0,0]))
    t = m.params.iloc[0] / se
    p = 2*(1 - stats.norm.cdf(abs(t)))
    return {'alpha':float(m.params.iloc[0]), 'se':se, 'p':float(p), 'n':int(m.nobs)}

def test_mz(d):
    y = d['pi_t']
    X = pd.DataFrame({'const':1.0,'E_pi':d['E_pi_t_dado_t12']}, index=y.index)
    mask = y.notna() & X['E_pi'].notna()
    y, X = y[mask], X[mask]
    m = OLS(y, X).fit()
    V = hac_cov_hodrick(m, h=12)
    R_mat = np.array([[1,0],[0,1]]); q = np.array([0,1])
    chi2, _, p_h = wald_test_hac(m, V, R_mat, q)
    return {'alpha':float(m.params.iloc[0]),'beta':float(m.params.iloc[1]),
            'wald_chi2_h':float(chi2),'wald_p_h':float(p_h),
            'r2':float(m.rsquared),'n':int(m.nobs)}

def test_cg(d):
    y = d['error']
    X = pd.DataFrame({'const':1.0,'revision':d['revision']}, index=y.index)
    mask = y.notna() & X['revision'].notna()
    y, X = y[mask], X[mask]
    m = OLS(y, X).fit()
    V = hac_cov_hodrick(m, h=12); se = np.sqrt(np.diag(V))
    p_h = 2*(1 - stats.norm.cdf(abs(m.params.iloc[1]/se[1])))
    lam = float(m.params.iloc[1])
    psi = 1/(1+lam) if lam > -1 else None
    return {'lambda':lam, 'p_h':float(p_h), 'psi':float(psi) if psi else None,
            'r2':float(m.rsquared), 'n':int(m.nobs)}

three_reg = {}
for nombre, sub in [('pre2017', reg_pre2017), ('2017_2020m2', reg_2017_2020), ('post2020', reg_post2020)]:
    ins = test_ins(sub)
    mz = test_mz(sub)
    cg = test_cg(sub)
    three_reg[nombre] = {'insesgamiento':ins, 'mz':mz, 'cg':cg}
    print(f"  {nombre} (N={ins['n']}):")
    print(f"     Insesgamiento: α={ins['alpha']:.3f} (p={ins['p']:.4f})")
    print(f"     MZ: α={mz['alpha']:.3f}, β={mz['beta']:.3f}, Wald_H={mz['wald_chi2_h']:.2f} (p_H={mz['wald_p_h']:.4f}), R²={mz['r2']:.3f}")
    psi_str = f"{cg['psi']:.3f}" if cg['psi'] else 'na'
    print(f"     CG: λ={cg['lambda']:.3f} (p_H={cg['p_h']:.4f}), ψ={psi_str}, R²={cg['r2']:.3f}")

# Test conjunto: ¿se mantiene la dicotomía pre/post-2020 controlando por 2017?
# Modelo de tres regímenes vs modelo de dos regímenes para CG
print("\n  Test conjunto de cambio entre los tres regímenes (CG):")
y_all = df_an['error']
X_all = pd.DataFrame({
    'const': 1.0,
    'revision': df_an['revision'],
    'd_2017': ((df_an['Fecha'] >= fecha_2017) & (df_an['Fecha'] < fecha_2020)).astype(float),
    'd_2020': (df_an['Fecha'] >= fecha_2020).astype(float),
    'rev_x_2017': df_an['revision'] * ((df_an['Fecha'] >= fecha_2017) & (df_an['Fecha'] < fecha_2020)).astype(float),
    'rev_x_2020': df_an['revision'] * (df_an['Fecha'] >= fecha_2020).astype(float),
}, index=y_all.index)
mask_all = y_all.notna() & X_all['revision'].notna()
y_all, X_all = y_all[mask_all], X_all[mask_all]
m_3r = OLS(y_all, X_all).fit()
V_3r = hac_cov(m_3r)

# Test: ¿el coeficiente sobre rev_x_2020 es significativo CONTROLANDO por rev_x_2017?
# Y ¿es significativo conjuntamente todo el bloque post-2020?
R_post = np.zeros((2, 6))
R_post[0, 3] = 1  # d_2020
R_post[1, 5] = 1  # rev_x_2020
chi2_post, _, p_post = wald_test_hac(m_3r, V_3r, R_post, np.zeros(2))
print(f"     Wald cambio post-2020 (controlando 2017): χ²(2) = {chi2_post:.2f}, p = {p_post:.4f}")

# Test: ¿hay también cambio en 2017?
R_2017 = np.zeros((2, 6))
R_2017[0, 2] = 1  # d_2017
R_2017[1, 4] = 1  # rev_x_2017
chi2_2017, _, p_2017 = wald_test_hac(m_3r, V_3r, R_2017, np.zeros(2))
print(f"     Wald cambio 2017 (controlando post-2020): χ²(2) = {chi2_2017:.2f}, p = {p_2017:.4f}")

# ============================================================================
# 3. THRESHOLD-MZ con umbral en la meta del 4%
# ============================================================================
print("\n=== THRESHOLD-MZ con meta 4% como umbral ===")
# Régimen "bajo": E[π_{t+12}] < 4%; Régimen "alto": >= 4%
df_an['regimen_meta'] = (df_an['E_pi_t_dado_t12'] >= 4.0).astype(int)
print(f"  Observaciones con E[π] < 4%: {(df_an['regimen_meta']==0).sum()}")
print(f"  Observaciones con E[π] >= 4%: {(df_an['regimen_meta']==1).sum()}")

# Estimar MZ separadamente en cada régimen
threshold_mz = {}
for reg, etiq in [(0, 'expectativa_baja'), (1, 'expectativa_alta')]:
    sub = df_an[df_an['regimen_meta'] == reg].dropna(subset=['pi_t','E_pi_t_dado_t12'])
    if len(sub) < 20: continue
    y = sub['pi_t']
    X = pd.DataFrame({'const':1.0,'E_pi':sub['E_pi_t_dado_t12']}, index=y.index)
    m = OLS(y, X).fit()
    V = hac_cov_hodrick(m, h=12); se = np.sqrt(np.diag(V))
    R_mat = np.array([[1,0],[0,1]]); q = np.array([0,1])
    chi2, _, p_h = wald_test_hac(m, V, R_mat, q)
    threshold_mz[etiq] = {
        'alpha': float(m.params.iloc[0]), 'beta': float(m.params.iloc[1]),
        'wald_chi2_h': float(chi2), 'wald_p_h': float(p_h),
        'r2': float(m.rsquared), 'n': int(m.nobs)
    }
    print(f"  {etiq} (N={int(m.nobs)}): α={m.params.iloc[0]:.3f}, β={m.params.iloc[1]:.3f}, Wald_H={chi2:.2f} (p={p_h:.4f}), R²={m.rsquared:.3f}")

# Test formal de igualdad de coeficientes entre regímenes (interacción)
y_t = df_an['pi_t']
X_t = pd.DataFrame({
    'const':1.0,
    'E_pi':df_an['E_pi_t_dado_t12'],
    'd_alta':df_an['regimen_meta'].astype(float),
    'E_pi_x_alta':df_an['E_pi_t_dado_t12']*df_an['regimen_meta'].astype(float),
}, index=y_t.index)
mask_t = y_t.notna() & X_t['E_pi'].notna()
y_t, X_t = y_t[mask_t], X_t[mask_t]
m_thr = OLS(y_t, X_t).fit()
V_thr = hac_cov_hodrick(m_thr, h=12)
R_thr = np.array([[0,0,1,0],[0,0,0,1]])
chi2_thr, _, p_thr = wald_test_hac(m_thr, V_thr, R_thr, np.zeros(2))
print(f"  Test conjunto de igualdad de regímenes: χ²(2) = {chi2_thr:.2f}, p = {p_thr:.4f}")

# Bajo regímenes alto vs bajo: ¿se cumple α+α_d=0 ∧ β+β_d=1?
# Eso es el test MZ para el régimen alto
R_alto = np.array([
    [1, 0, 1, 0],   # α + α_d = 0
    [0, 1, 0, 1],   # β + β_d = 1
])
q_alto = np.array([0, 1])
chi2_alto, _, p_alto = wald_test_hac(m_thr, V_thr, R_alto, q_alto)
print(f"  MZ bajo régimen alto (interacción): χ²(2) = {chi2_alto:.2f}, p = {p_alto:.4f}")

# ============================================================================
# CONSOLIDAR Y AGREGAR AL JSON
# ============================================================================
adicional_v2 = {
    'bai_perron_extendido': {
        'resultados': bp_resultados,
        'optimo_bic': bp_optimo,
    },
    'tres_regimenes': three_reg,
    'tres_regimenes_test_conjunto': {
        'wald_post2020_controlando_2017': {'chi2': float(chi2_post), 'p': float(p_post)},
        'wald_2017_controlando_post2020': {'chi2': float(chi2_2017), 'p': float(p_2017)},
    },
    'threshold_mz_meta_4': {
        'expectativa_baja': threshold_mz.get('expectativa_baja'),
        'expectativa_alta': threshold_mz.get('expectativa_alta'),
        'test_igualdad': {'chi2': float(chi2_thr), 'p': float(p_thr)},
        'mz_alto_regimen': {'chi2': float(chi2_alto), 'p': float(p_alto)},
    },
}

def san(o):
    if isinstance(o, dict): return {k:san(v) for k,v in o.items()}
    if isinstance(o, list): return [san(x) for x in o]
    if isinstance(o, float) and (np.isnan(o) or np.isinf(o)): return None
    return o
adicional_v2 = san(adicional_v2)

# Cargar JSON principal y agregar
with open(RESULTS + 'resultados_econometricos.json') as f:
    res_principal = json.load(f)
res_principal.update(adicional_v2)

with open(RESULTS + 'resultados_econometricos.json', 'w') as f:
    json.dump(res_principal, f, indent=2, default=str)

print("\n\nANÁLISIS SUPLEMENTARIO V2 COMPLETO. JSON enriquecido.")
