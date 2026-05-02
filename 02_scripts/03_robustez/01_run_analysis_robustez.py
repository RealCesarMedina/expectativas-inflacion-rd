"""
Análisis de robustez. Genera resultados suplementarios que se integran al
JSON principal:

1. Bai-Perron multi-quiebre
2. Sesgo condicional al estado
3. Pre-pandemia desagregada en sub-regímenes
4. Análisis de magnitud económica del CG
5. Test de robustez del CG bajo construcción de revisión a horizonte fijo
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
# CARGAR DATOS Y RECONSTRUIR MUESTRA
# ============================================================================
ds = pd.read_csv(RESULTS + 'Dataset_Consolidado_BCRD.csv')
ds['Fecha'] = pd.to_datetime(ds['Fecha'])

eem = pd.read_excel(DATA_RAW + 'Historico-EEM_BCRD.xlsx', sheet_name='Mediana', header=[7,8])
eem.columns = [' '.join(c).replace('Unnamed: 0_level_1','').replace('Unnamed: 1_level_1','').strip() for c in eem.columns]
eem = eem.dropna(subset=['Año','Mes']).copy()
eem['Año'] = eem['Año'].astype(int); eem['Mes'] = eem['Mes'].astype(int)
eem['Fecha'] = pd.to_datetime(dict(year=eem['Año'], month=eem['Mes'], day=1))
eem = eem.sort_values('Fecha').reset_index(drop=True)
eem.rename(columns={
    'Inflación En 12 meses': 'E_pi_12m',
    'Inflación Año actual': 'E_pi_cierre_actual',
    'Inflación Año siguiente': 'E_pi_cierre_proximo',
}, inplace=True)

df = eem.merge(ds[['Fecha','pi_t','TPM_obs','var_tc','var_pib']], on='Fecha', how='left')
df['E_pi_t_dado_t12'] = df['E_pi_12m'].shift(12)
df['error'] = df['pi_t'] - df['E_pi_t_dado_t12']
df['revision'] = df['E_pi_12m'] - df['E_pi_12m'].shift(1)
df_an = df[df['error'].notna()].copy().reset_index(drop=True)
fecha_corte = pd.Timestamp('2020-03-01')

# ============================================================================
# 1. BAI-PERRON MULTI-QUIEBRE
# ============================================================================
def bai_perron_quiebres(serie, fechas, m_max=4, trim=0.15):
    """
    Implementación práctica de Bai-Perron: encuentra hasta m_max quiebres
    minimizando la suma de cuadrados residuales global, sujeto a una
    distancia mínima entre quiebres (trim*N).
    
    Para cada cantidad m de quiebres en {0, 1, 2, ..., m_max}, busca la
    partición óptima por programación dinámica simplificada (búsqueda
    sobre rejilla) y selecciona m por BIC.
    """
    s = serie.dropna().reset_index(drop=True)
    f = fechas.reset_index(drop=True)
    n = len(s)
    h = max(int(n*trim), 5)
    
    def ssr_segmento(i, j):
        if j - i < 2: return 1e10
        seg = s.iloc[i:j]
        return np.sum((seg - seg.mean())**2)
    
    # m=0: SSR base
    ssr_total = ssr_segmento(0, n)
    bic_0 = n * np.log(ssr_total/n) + 1 * np.log(n)
    resultados = [{'m':0, 'ssr':float(ssr_total), 'bic':float(bic_0), 'fechas':[]}]
    
    # m=1: 1 quiebre, búsqueda por rejilla
    best_1 = (1e10, None)
    for tau in range(h, n-h):
        ssr = ssr_segmento(0, tau) + ssr_segmento(tau, n)
        if ssr < best_1[0]: best_1 = (ssr, tau)
    bic_1 = n * np.log(best_1[0]/n) + 3 * np.log(n)  # 1 quiebre = 3 parámetros (2 medias + 1 fecha)
    resultados.append({'m':1, 'ssr':float(best_1[0]), 'bic':float(bic_1),
                        'fechas':[f.iloc[best_1[1]].strftime('%Y-%m')]})
    
    # m=2: 2 quiebres
    best_2 = (1e10, None, None)
    for tau1 in range(h, n-2*h):
        for tau2 in range(tau1+h, n-h):
            ssr = ssr_segmento(0, tau1) + ssr_segmento(tau1, tau2) + ssr_segmento(tau2, n)
            if ssr < best_2[0]: best_2 = (ssr, tau1, tau2)
    bic_2 = n * np.log(best_2[0]/n) + 5 * np.log(n)
    resultados.append({'m':2, 'ssr':float(best_2[0]), 'bic':float(bic_2),
                        'fechas':[f.iloc[best_2[1]].strftime('%Y-%m'),
                                   f.iloc[best_2[2]].strftime('%Y-%m')]})
    
    # m=3: 3 quiebres - búsqueda secuencial sobre la mejor partición de m=2
    # Para evitar O(N³), partimos del óptimo de m=2 y buscamos un quiebre adicional
    # en cada uno de los 3 segmentos resultantes.
    tau1_opt, tau2_opt = best_2[1], best_2[2]
    candidatos_seg = []
    # Buscar mejor 3er quiebre en segmento [0, tau1_opt]
    for tau_new in range(h, tau1_opt - h):
        ssr = (ssr_segmento(0, tau_new) + ssr_segmento(tau_new, tau1_opt) +
               ssr_segmento(tau1_opt, tau2_opt) + ssr_segmento(tau2_opt, n))
        candidatos_seg.append((ssr, tuple(sorted([tau_new, tau1_opt, tau2_opt]))))
    # En segmento [tau1_opt, tau2_opt]
    for tau_new in range(tau1_opt + h, tau2_opt - h):
        ssr = (ssr_segmento(0, tau1_opt) + ssr_segmento(tau1_opt, tau_new) +
               ssr_segmento(tau_new, tau2_opt) + ssr_segmento(tau2_opt, n))
        candidatos_seg.append((ssr, tuple(sorted([tau1_opt, tau_new, tau2_opt]))))
    # En segmento [tau2_opt, n]
    for tau_new in range(tau2_opt + h, n - h):
        ssr = (ssr_segmento(0, tau1_opt) + ssr_segmento(tau1_opt, tau2_opt) +
               ssr_segmento(tau2_opt, tau_new) + ssr_segmento(tau_new, n))
        candidatos_seg.append((ssr, tuple(sorted([tau1_opt, tau2_opt, tau_new]))))
    
    if candidatos_seg:
        best_3_ssr, best_3_taus = min(candidatos_seg, key=lambda x: x[0])
        bic_3 = n * np.log(best_3_ssr/n) + 7 * np.log(n)
        resultados.append({'m':3, 'ssr':float(best_3_ssr), 'bic':float(bic_3),
                            'fechas':[f.iloc[t].strftime('%Y-%m') for t in best_3_taus]})
    
    # m óptimo por BIC
    m_optimo = min(resultados, key=lambda x: x['bic'])
    return resultados, m_optimo

print("=== BAI-PERRON MULTI-QUIEBRE ===")
bp_resultados, bp_optimo = bai_perron_quiebres(df_an['error'], df_an['Fecha'], m_max=3, trim=0.12)
for r in bp_resultados:
    print(f"  m={r['m']}: SSR={r['ssr']:.1f}, BIC={r['bic']:.1f}, fechas={r['fechas']}")
print(f"  >>> Óptimo por BIC: m={bp_optimo['m']}, fechas={bp_optimo['fechas']}")

# ============================================================================
# 2. SESGO CONDICIONAL AL ESTADO
# ============================================================================
print("\n=== SESGO CONDICIONAL AL ESTADO ===")
# Definir estados de inflación: alta vs baja respecto a la mediana
mediana_pi = df_an['pi_t'].median()
df_an['estado_alta'] = (df_an['pi_t'] > mediana_pi).astype(int)
volatilidad_alta = df_an.groupby(df_an['Fecha'].dt.year)['pi_t'].std()
df_an['vol_alta'] = df_an['Fecha'].dt.year.map(volatilidad_alta) > volatilidad_alta.median()

def hac_cov(m, lag_min=11):
    nlags = max(lag_min, int(np.ceil(4*(m.nobs/100)**(2/9))))
    return cov_hac(m, nlags=nlags)

# Test de sesgo condicional al nivel de inflación
res_cond = {}
for est, etiq in [(0, 'inflacion_baja'), (1, 'inflacion_alta')]:
    sub = df_an[df_an['estado_alta'] == est]
    if len(sub) < 20: continue
    y = sub['error']
    X = pd.DataFrame({'const': 1.0}, index=y.index)
    m = OLS(y, X).fit()
    V = hac_cov(m); se = float(np.sqrt(V[0,0]))
    p = 2*(1 - stats.norm.cdf(abs(m.params.iloc[0]/se)))
    res_cond[etiq] = {'alpha': float(m.params.iloc[0]), 'se': se, 'p': float(p), 'n': int(m.nobs)}
    print(f"  {etiq} (N={int(m.nobs)}): α={m.params.iloc[0]:.3f}, SE={se:.3f}, p={p:.4f}")

# Test formal de igualdad de sesgos: regresión con interacción
y = df_an['error']
X = pd.DataFrame({'const': 1.0,
                  'estado_alta': df_an['estado_alta'].astype(float)}, index=y.index)
m_test = OLS(y, X).fit()
V_test = hac_cov(m_test); se_test = np.sqrt(np.diag(V_test))
p_test = 2*(1 - stats.norm.cdf(np.abs(m_test.params.values/se_test)))
res_cond['test_igualdad'] = {
    'coef_dummy': float(m_test.params.iloc[1]),
    'p_dummy': float(p_test[1]),
    'interpretacion': 'Diferencia de sesgo entre regimen alto y bajo de inflación'
}
print(f"  Test igualdad: dif={m_test.params.iloc[1]:.3f}, p={p_test[1]:.4f}")

# ============================================================================
# 3. PRE-PANDEMIA DESAGREGADA EN SUB-REGÍMENES
# ============================================================================
print("\n=== PRE-PANDEMIA POR SUB-REGÍMENES ===")
# 2011-2014: inflación moderada-alta
# 2015-2017: inflación baja (cerca de 0%)
# 2018-2020m2: estabilización en torno a meta
sub_reg = {
    '2010m6_2014': (pd.Timestamp('2010-06-01'), pd.Timestamp('2014-12-31')),
    '2015_2017': (pd.Timestamp('2015-01-01'), pd.Timestamp('2017-12-31')),
    '2018_2020m2': (pd.Timestamp('2018-01-01'), pd.Timestamp('2020-02-29')),
}
res_subreg = {}
for nombre, (ini, fin) in sub_reg.items():
    sub = df_an[(df_an['Fecha'] >= ini) & (df_an['Fecha'] <= fin)]
    if len(sub) < 12: continue
    # Sesgo en este subperíodo
    y = sub['error']
    X = pd.DataFrame({'const': 1.0}, index=y.index)
    m = OLS(y, X).fit()
    V = hac_cov(m); se = float(np.sqrt(V[0,0]))
    p_alpha = 2*(1 - stats.norm.cdf(abs(m.params.iloc[0]/se)))
    
    # CG en este subperíodo
    sub_cg = sub.dropna(subset=['error', 'revision'])
    if len(sub_cg) >= 12:
        X_cg = pd.DataFrame({'const': 1.0, 'revision': sub_cg['revision']}, index=sub_cg.index)
        m_cg = OLS(sub_cg['error'], X_cg).fit()
        V_cg = hac_cov(m_cg); se_cg = np.sqrt(np.diag(V_cg))
        p_lambda = 2*(1 - stats.norm.cdf(abs(m_cg.params.iloc[1]/se_cg[1])))
        lambda_v = float(m_cg.params.iloc[1])
        psi_v = 1/(1+lambda_v) if lambda_v > -1 else None
        cg_dict = {'lambda': lambda_v, 'p_lambda': float(p_lambda),
                   'psi': float(psi_v) if psi_v is not None else None, 'n_cg': int(m_cg.nobs)}
    else:
        cg_dict = None
    
    res_subreg[nombre] = {
        'alpha': float(m.params.iloc[0]), 'p_alpha': float(p_alpha),
        'media_pi': float(sub['pi_t'].mean()), 'media_E': float(sub['E_pi_t_dado_t12'].mean()),
        'n': int(m.nobs), 'cg': cg_dict
    }
    print(f"  {nombre} (N={int(m.nobs)}): π̄={sub['pi_t'].mean():.2f}%, Ē={sub['E_pi_t_dado_t12'].mean():.2f}%, α={m.params.iloc[0]:.3f} (p={p_alpha:.3f})")
    if cg_dict:
        print(f"     CG: λ={cg_dict['lambda']:.3f} (p={cg_dict['p_lambda']:.3f}), ψ={cg_dict.get('psi','—')}")

# ============================================================================
# 4. MAGNITUD ECONÓMICA DEL CG: descomposición de varianza del error
# ============================================================================
print("\n=== MAGNITUD ECONÓMICA: DESCOMPOSICIÓN DE LA VARIANZA DEL ERROR ===")
# Pre-pandemia
pre = df_an[df_an['Fecha'] < fecha_corte].dropna(subset=['error','revision'])
post = df_an[df_an['Fecha'] >= fecha_corte].dropna(subset=['error','revision'])

magnitud = {}
for etiq, sub in [('pre', pre), ('post', post), ('full', df_an.dropna(subset=['error','revision']))]:
    var_total = float(sub['error'].var())
    # CG sólo
    X = pd.DataFrame({'const':1.0, 'revision': sub['revision']}, index=sub.index)
    m = OLS(sub['error'], X).fit()
    var_cg = float(var_total * m.rsquared)
    var_no_cg = float(var_total - var_cg)
    
    # Modelo combinado: revision + TPM rezagada
    sub2 = sub.copy()
    sub2['tpm_lag13'] = df_an['TPM_obs'].shift(13).reindex(sub.index)
    sub2 = sub2.dropna(subset=['error','revision','tpm_lag13'])
    if len(sub2) > 20:
        X2 = pd.DataFrame({'const':1.0, 'revision': sub2['revision'], 'tpm_lag13': sub2['tpm_lag13']}, index=sub2.index)
        m2 = OLS(sub2['error'], X2).fit()
        var_total2 = float(sub2['error'].var())
        var_combinado = float(var_total2 * m2.rsquared)
    else:
        var_combinado = None
    
    desv_estd = float(np.sqrt(var_total))
    magnitud[etiq] = {
        'var_total': var_total, 'desv_total': desv_estd,
        'var_explicada_cg': var_cg, 'pct_cg': float(m.rsquared*100),
        'var_explicada_combinado_cg_tpm': var_combinado,
        'n': len(sub)
    }
    print(f"  {etiq}: σ²(error)={var_total:.2f}, σ(error)={desv_estd:.2f} p.p.")
    print(f"     CG sólo explica {m.rsquared*100:.1f}% de la varianza ({var_cg:.2f} p.p.²)")
    if var_combinado:
        print(f"     CG + TPM rezagada explican {m2.rsquared*100:.1f}% ({var_combinado:.2f} p.p.²)")

# ============================================================================
# 5. ROBUSTEZ DEL CG BAJO HORIZONTE FIJO (caveat metodológico)
# ============================================================================
print("\n=== ROBUSTEZ CG: HORIZONTE FIJO usando 'cierre del año actual' ===")
# Construir revisión a horizonte fijo: E_t[π_dic_año] - E_{t-1}[π_dic_año]
# Solo entre meses del mismo año calendario (para que el target sea el mismo)
df_an['mismo_ano'] = df_an['Fecha'].dt.year == df_an['Fecha'].shift(1).dt.year
df_an['rev_fijo'] = np.where(df_an['mismo_ano'],
                              df_an['E_pi_cierre_actual'] - df_an['E_pi_cierre_actual'].shift(1),
                              np.nan)
# Para el error con target fijo, necesitamos π de diciembre de cada año
pi_dic = df_an[df_an['Fecha'].dt.month == 12][['Fecha','pi_t']].copy()
pi_dic['ano'] = pi_dic['Fecha'].dt.year
pi_dic_dict = dict(zip(pi_dic['ano'], pi_dic['pi_t']))
df_an['pi_cierre'] = df_an['Fecha'].dt.year.map(pi_dic_dict)
df_an['error_fijo'] = df_an['pi_cierre'] - df_an['E_pi_cierre_actual']

# CG con revisión a horizonte fijo
print("  Revisión sobre 'cierre del año actual' (horizonte que se acorta hacia diciembre):")
for etiq, mascara in [('full', np.ones(len(df_an), dtype=bool)),
                       ('pre', df_an['Fecha'] < fecha_corte),
                       ('post', df_an['Fecha'] >= fecha_corte)]:
    sub = df_an[mascara].dropna(subset=['error_fijo','rev_fijo'])
    if len(sub) < 20: continue
    X = pd.DataFrame({'const':1.0, 'rev_fijo': sub['rev_fijo']}, index=sub.index)
    m = OLS(sub['error_fijo'], X).fit()
    V = hac_cov(m); se = np.sqrt(np.diag(V))
    p_lambda = 2*(1 - stats.norm.cdf(abs(m.params.iloc[1]/se[1])))
    print(f"  [{etiq}] λ_fijo={m.params.iloc[1]:.3f}, p={p_lambda:.4f}, R²={m.rsquared:.3f}, N={int(m.nobs)}")

cg_robustez = {}
for etiq, mascara in [('full', np.ones(len(df_an), dtype=bool)),
                       ('pre', df_an['Fecha'] < fecha_corte),
                       ('post', df_an['Fecha'] >= fecha_corte)]:
    sub = df_an[mascara].dropna(subset=['error_fijo','rev_fijo'])
    if len(sub) < 20: continue
    X = pd.DataFrame({'const':1.0, 'rev_fijo': sub['rev_fijo']}, index=sub.index)
    m = OLS(sub['error_fijo'], X).fit()
    V = hac_cov(m); se = np.sqrt(np.diag(V))
    p_lambda = 2*(1 - stats.norm.cdf(abs(m.params.iloc[1]/se[1])))
    cg_robustez[etiq] = {
        'lambda_fijo': float(m.params.iloc[1]),
        'p_lambda_fijo': float(p_lambda),
        'r2': float(m.rsquared),
        'n': int(m.nobs)
    }

# ============================================================================
# CONSOLIDAR Y AGREGAR AL JSON PRINCIPAL
# ============================================================================
adicional = {
    'bai_perron': {
        'resultados': bp_resultados,
        'optimo_bic': bp_optimo,
    },
    'sesgo_condicional': res_cond,
    'pre_pandemia_desagregada': res_subreg,
    'magnitud_economica': magnitud,
    'cg_robustez_horizonte_fijo': cg_robustez,
}

# Sanear y guardar
def san(o):
    if isinstance(o, dict): return {k:san(v) for k,v in o.items()}
    if isinstance(o, list): return [san(x) for x in o]
    if isinstance(o, float) and (np.isnan(o) or np.isinf(o)): return None
    return o
adicional = san(adicional)

# Cargar JSON principal y agregar
with open(RESULTS + 'resultados_econometricos.json') as f:
    res_principal = json.load(f)
res_principal.update(adicional)

with open(RESULTS + 'resultados_econometricos.json', 'w') as f:
    json.dump(res_principal, f, indent=2, default=str)

print("\n\nANÁLISIS ADICIONAL COMPLETO. JSON enriquecido en (RESULTS)resultados_econometricos.json")
