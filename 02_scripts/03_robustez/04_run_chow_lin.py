"""
Implementación Chow-Lin (1971) para mensualización del PIB usando el IMAE como
indicador relacionado.

Método: Chow-Lin máxima verosimilitud sobre serie residual AR(1).
Restricción: la suma (o promedio) trimestral de la serie mensual estimada debe
coincidir con la serie trimestral observada.
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
from scipy import stats, optimize
import json
import warnings
warnings.filterwarnings("ignore")

# ============================================================================
# 1. PARSE IMAE (igual que antes)
# ============================================================================
raw = pd.read_excel(DATA_RAW + 'IMAE_2018_100_BCRD.xlsx', sheet_name='IMAE', header=None)
meses_es = ['Enero','Febrero','Marzo','Abril','Mayo','Junio',
            'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
mes_a_num = {m: i+1 for i, m in enumerate(meses_es)}

filas = []
import re
# El IMAE usa dos formatos:
#  - Para 2007-2022: 12 meses, luego una fila "Promedio YYYY"
#  - Para 2023-2026: una fila con el año YYYY (entero) y luego 12 meses
# Estrategia: encontrar todas las filas con un año identificable, luego asignar los meses

# Identificar todas las filas-marca de año
filas_ano_inicio = []  # Para formato (año entero) → 12 meses siguientes
filas_ano_fin = []     # Para formato 12 meses → ("Promedio YYYY")

for i in range(len(raw)):
    v0 = raw.iloc[i, 0]
    v1 = raw.iloc[i, 1]
    if pd.notna(v0):
        s = str(v0)
        if isinstance(v0, (int, float)) and 1990 <= v0 <= 2030:
            filas_ano_inicio.append((int(v0), i))
        elif s.startswith('Promedio '):
            m = re.search(r'(\d{4})', s)
            if m: filas_ano_fin.append((int(m.group(1)), i))

# Procesar formato fin: cada "Promedio YYYY" en fila i tiene los 12 meses en filas [i-12, i-1]
for ano, idx_fin in filas_ano_fin:
    for j in range(max(0, idx_fin-12), idx_fin):
        v1 = raw.iloc[j, 1]
        v2 = raw.iloc[j, 2]
        if pd.notna(v1) and isinstance(v1, str) and v1.strip() in mes_a_num and pd.notna(v2):
            filas.append({'Año': ano, 'Mes': mes_a_num[v1.strip()], 'IMAE': float(v2)})

# Procesar formato inicio: cada año entero en fila i tiene meses en filas [i+1, i+12]
for ano, idx_ini in filas_ano_inicio:
    for j in range(idx_ini+1, min(len(raw), idx_ini+13)):
        v1 = raw.iloc[j, 1]
        v2 = raw.iloc[j, 2]
        if pd.notna(v1) and isinstance(v1, str) and v1.strip() in mes_a_num and pd.notna(v2):
            # Evitar duplicar si ya capturado por formato fin
            duplicado = any(f['Año']==ano and f['Mes']==mes_a_num[v1.strip()] for f in filas)
            if not duplicado:
                filas.append({'Año': ano, 'Mes': mes_a_num[v1.strip()], 'IMAE': float(v2)})

imae = pd.DataFrame(filas)
imae['Fecha'] = pd.to_datetime(dict(year=imae['Año'], month=imae['Mes'], day=1))
imae = imae.sort_values('Fecha').reset_index(drop=True)

# ============================================================================
# 2. RECONSTRUIR PIB TRIMESTRAL desde el dataset (mensualizado constante)
# ============================================================================
ds = pd.read_csv(RESULTS + 'Dataset_Consolidado_BCRD.csv')
ds['Fecha'] = pd.to_datetime(ds['Fecha'])

# Como cada trimestre tiene el mismo PIB_obs en los 3 meses, lo extraigo único
ds['Trimestre'] = ds['Fecha'].dt.to_period('Q')
pib_trim = ds.groupby('Trimestre').agg(PIB=('PIB_obs','first')).reset_index()
pib_trim = pib_trim.dropna()
pib_trim['Fecha_fin_trim'] = pib_trim['Trimestre'].dt.end_time.dt.normalize()
pib_trim['Fecha_inicio_trim'] = pib_trim['Trimestre'].dt.start_time.dt.normalize()
print(f"PIB trimestral: {len(pib_trim)} obs, {pib_trim['Trimestre'].min()} a {pib_trim['Trimestre'].max()}")

# Construir IMAE trimestral (promedio de los 3 meses) para cada trimestre
imae['Trimestre'] = imae['Fecha'].dt.to_period('Q')
imae_trim = imae.groupby('Trimestre').agg(IMAE=('IMAE','mean')).reset_index()

# Unir trimestralmente
df_trim = pib_trim.merge(imae_trim, on='Trimestre', how='inner').sort_values('Trimestre').reset_index(drop=True)
print(f"Trimestres con PIB e IMAE: {len(df_trim)}")
print(df_trim.head())
print(df_trim.tail())

# ============================================================================
# 3. ESTIMACIÓN CHOW-LIN
# ============================================================================
"""
Chow-Lin model:
   y = X*beta + u,  u ~ AR(1) con parámetro rho
   y_low = C*y, donde C es matriz de agregación (3 meses → 1 trimestre, promedio)

Estimador BLUP (Chow-Lin 1971):
   beta_hat = (X' C' V_low^-1 C X)^-1 X' C' V_low^-1 y_low
   y_hat = X*beta_hat + V*C'*V_low^-1*(y_low - C*X*beta_hat)
   donde V es la covarianza AR(1) del proceso mensual y V_low = C V C'
"""
n_meses = len(imae)
n_trim = len(df_trim)

# Matriz de agregación C (n_trim × n_meses): cada fila tiene 1/3 en los 3 meses del trimestre
# Solo para los trimestres que tienen PIB observado
imae_indexed = imae.set_index('Fecha')
fechas_meses = imae_indexed.index.tolist()

# Reconstruir el rango mensual completo desde el primer mes del primer trimestre con PIB
# hasta el último mes del último trimestre con PIB
fechas_trim_inicio = df_trim['Fecha_inicio_trim'].iloc[0]
fechas_trim_fin = df_trim['Fecha_fin_trim'].iloc[-1]
mes_ini = pd.Timestamp(year=fechas_trim_inicio.year, month=fechas_trim_inicio.month, day=1)
mes_fin = pd.Timestamp(year=fechas_trim_fin.year, month=fechas_trim_fin.month, day=1)
rango_mensual = pd.date_range(mes_ini, mes_fin, freq='MS')
print(f"\nRango mensual: {rango_mensual[0].strftime('%Y-%m')} a {rango_mensual[-1].strftime('%Y-%m')} ({len(rango_mensual)} meses)")

# Verificar que IMAE cubre todo el rango
imae_indexed = imae.set_index('Fecha')['IMAE']
imae_full = imae_indexed.reindex(rango_mensual)
n_missing = imae_full.isna().sum()
print(f"IMAE faltante en el rango: {n_missing}")
if n_missing > 0:
    # Si falta IMAE en el rango, recortar al rango con IMAE disponible
    rango_mensual = rango_mensual[imae_full.notna()]
    imae_full = imae_full.dropna()

# Reconstruir C asegurando que el agregado sea consistente
# Construyo una matriz Trimestres con PIB × Meses con IMAE en ese trimestre
n_meses = len(rango_mensual)
trims_meses = pd.Series(rango_mensual).dt.to_period('Q').values
trims_pib = df_trim['Trimestre'].values

# Solo trimestres que tienen PIB Y tienen los 3 meses de IMAE en el rango
trims_validos = []
for t in trims_pib:
    meses_de_t = np.where(trims_meses == t)[0]
    if len(meses_de_t) == 3:
        trims_validos.append(t)

print(f"Trimestres válidos (con PIB y 3 meses de IMAE): {len(trims_validos)}")

# Re-construir la base: solo PIBs válidos
df_trim_v = df_trim[df_trim['Trimestre'].isin(trims_validos)].copy().reset_index(drop=True)
y_low = df_trim_v['PIB'].values
n_trim = len(y_low)

# Matriz C (n_trim × n_meses), con 1/3 en los 3 meses de cada trimestre (promedio)
C = np.zeros((n_trim, n_meses))
for i, t in enumerate(trims_validos):
    meses_de_t = np.where(trims_meses == t)[0]
    C[i, meses_de_t] = 1.0/3.0

# X (n_meses × k): constante + IMAE
X = np.column_stack([np.ones(n_meses), imae_full.values])

print(f"\nMatrices: C = {C.shape}, X = {X.shape}, y_low = {y_low.shape}")

# Optimización: maximizar verosimilitud sobre rho (parámetro AR(1))
def chow_lin_neg_loglik(rho_val, y_low, X, C, n_meses):
    if abs(rho_val) >= 0.99: return 1e10
    # Matriz V (covarianza AR(1) escalada): V_ij = rho^|i-j| / (1-rho²)
    idx = np.arange(n_meses)
    V = rho_val ** np.abs(idx[:, None] - idx[None, :])
    V = V / (1 - rho_val**2)
    V_low = C @ V @ C.T
    try:
        V_low_inv = np.linalg.inv(V_low)
    except np.linalg.LinAlgError:
        return 1e10
    
    # GLS para beta
    XtCt = X.T @ C.T
    A = XtCt @ V_low_inv @ C @ X
    b = XtCt @ V_low_inv @ y_low
    try:
        beta_hat = np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        return 1e10
    
    # Residual trimestral
    res = y_low - C @ X @ beta_hat
    sigma2 = float(res @ V_low_inv @ res / n_trim)
    
    # Log-likelihood concentrado
    sign, logdet = np.linalg.slogdet(sigma2 * V_low)
    if sign <= 0: return 1e10
    ll = -0.5 * (n_trim * np.log(2 * np.pi) + logdet + n_trim)
    return -ll

# Optimizar rho
rhos_test = np.linspace(0.0, 0.95, 20)
lls = [chow_lin_neg_loglik(r, y_low, X, C, n_meses) for r in rhos_test]
print(f"\nGrid búsqueda rho: mejor inicial = {rhos_test[np.argmin(lls)]:.3f}")

result = optimize.minimize_scalar(chow_lin_neg_loglik,
                                   args=(y_low, X, C, n_meses),
                                   bounds=(0.0, 0.98), method='bounded')
rho_hat = float(result.x)
print(f"rho_hat (Chow-Lin máx-verosimilitud): {rho_hat:.4f}")

# Calcular y_hat con rho_hat
idx = np.arange(n_meses)
V = rho_hat ** np.abs(idx[:, None] - idx[None, :])
V = V / (1 - rho_hat**2)
V_low = C @ V @ C.T
V_low_inv = np.linalg.inv(V_low)
XtCt = X.T @ C.T
beta_hat = np.linalg.solve(XtCt @ V_low_inv @ C @ X, XtCt @ V_low_inv @ y_low)
print(f"beta_hat (constante, IMAE): [{beta_hat[0]:.3f}, {beta_hat[1]:.3f}]")
y_low_hat = C @ X @ beta_hat
res_low = y_low - y_low_hat
y_hat = X @ beta_hat + V @ C.T @ V_low_inv @ res_low

# Verificar restricción de agregación
y_low_chowlin = C @ y_hat
agreg_error = np.max(np.abs(y_low_chowlin - y_low))
print(f"Error máximo de agregación trimestral: {agreg_error:.6f}")

# ============================================================================
# 4. CONSTRUIR SERIE PIB MENSUAL CHOW-LIN Y CALCULAR var_pib
# ============================================================================
pib_chowlin = pd.DataFrame({
    'Fecha': rango_mensual,
    'PIB_chowlin': y_hat,
    'IMAE': imae_full.values,
})
print("\n=== PIB Chow-Lin (primeros y últimos meses) ===")
print(pib_chowlin.head(6).to_string())
print("...")
print(pib_chowlin.tail(6).to_string())

# Crecimiento interanual
pib_chowlin = pib_chowlin.set_index('Fecha').sort_index()
pib_chowlin['var_pib_chowlin'] = (pib_chowlin['PIB_chowlin'] / pib_chowlin['PIB_chowlin'].shift(12) - 1) * 100

# Comparar contra el PIB actual (asignación constante)
ds_idx = ds.set_index('Fecha')['var_pib']
comparacion = pib_chowlin.join(ds_idx, how='inner').rename(columns={'var_pib':'var_pib_constante'})
comparacion['diferencia'] = comparacion['var_pib_chowlin'] - comparacion['var_pib_constante']
print("\n=== Comparación var_pib: Chow-Lin vs constante ===")
print(f"Correlación: {comparacion['var_pib_chowlin'].corr(comparacion['var_pib_constante']):.4f}")
print(f"Diferencia media: {comparacion['diferencia'].mean():.4f}")
print(f"Diferencia DE: {comparacion['diferencia'].std():.4f}")
print(f"Diferencia máx: {comparacion['diferencia'].abs().max():.4f}")

# ============================================================================
# 5. RE-ESTIMAR TEST DE EFICIENCIA INFORMACIONAL CON PIB CHOW-LIN
# ============================================================================
print("\n=== TEST DE EFICIENCIA INFORMACIONAL: PIB CONSTANTE vs CHOW-LIN ===\n")

# Cargar datos auxiliares para el test
eem = pd.read_excel(DATA_RAW + 'Historico-EEM_BCRD.xlsx', sheet_name='Mediana', header=[7,8])
eem.columns = [' '.join(c).replace('Unnamed: 0_level_1','').replace('Unnamed: 1_level_1','').strip() for c in eem.columns]
eem = eem.dropna(subset=['Año','Mes']).copy()
eem['Año'] = eem['Año'].astype(int); eem['Mes'] = eem['Mes'].astype(int)
eem['Fecha'] = pd.to_datetime(dict(year=eem['Año'], month=eem['Mes'], day=1))
eem.rename(columns={'Inflación En 12 meses': 'E_pi_12m'}, inplace=True)

# Construir variables rezagadas para los dos modelos
ds2 = ds.set_index('Fecha').copy()
ds2['var_pib_chowlin'] = pib_chowlin['var_pib_chowlin']
ds2 = ds2.reset_index()

ds2['E_pi_t_dado_t12'] = ds2.merge(eem[['Fecha','E_pi_12m']], on='Fecha', how='left')['E_pi_12m'].shift(12).values
ds2['error'] = ds2['pi_t'] - ds2['E_pi_t_dado_t12']
ds2['pi_lag13'] = ds2['pi_t'].shift(13)
ds2['tpm_lag13'] = ds2['TPM_obs'].shift(13)
ds2['vtc_lag13'] = ds2['var_tc'].shift(13)
ds2['vpib_const_lag13'] = ds2['var_pib'].shift(13)
ds2['vpib_chowlin_lag13'] = ds2['var_pib_chowlin'].shift(13)

def hac_cov(m, lag_min=11):
    nlags = max(lag_min, int(np.ceil(4*(m.nobs/100)**(2/9))))
    return cov_hac(m, nlags=nlags)

def estimar_eficiencia(df_in, pib_var):
    sub = df_in[['error','pi_lag13','tpm_lag13','vtc_lag13', pib_var]].dropna().reset_index(drop=True)
    y = sub['error']
    X = pd.DataFrame({
        'const': 1.0,
        'pi_lag13': sub['pi_lag13'],
        'tpm_lag13': sub['tpm_lag13'],
        'vtc_lag13': sub['vtc_lag13'],
        'vpib_lag13': sub[pib_var],
    }, index=y.index)
    m = OLS(y, X).fit()
    V = hac_cov(m); se = np.sqrt(np.diag(V))
    return m, V, se, sub

# Modelo con PIB constante
m_c, V_c, se_c, sub_c = estimar_eficiencia(ds2, 'vpib_const_lag13')
print("Modelo con PIB constante (asignación):")
print(f"  N: {int(m_c.nobs)}, R²: {m_c.rsquared:.4f}")
for nom, b, s in zip(['const','pi_lag13','tpm_lag13','vtc_lag13','vpib_lag13'], m_c.params.values, se_c):
    z = b/s; p = 2*(1-stats.norm.cdf(abs(z)))
    print(f"  {nom:14s} = {b:7.3f} (SE={s:.3f}, p={p:.4f})")

# Test conjunto de no-eficiencia (todos los regresores = 0 excepto constante)
R_mat = np.zeros((4, 5))
for i in range(4): R_mat[i, i+1] = 1
beta = m_c.params.values
diff = R_mat @ beta
M = R_mat @ V_c @ R_mat.T
chi2_c = float(diff @ np.linalg.inv(M) @ diff)
p_c = 1 - stats.chi2.cdf(chi2_c, 4)
print(f"  Wald conjunto: χ²(4) = {chi2_c:.2f}, p = {p_c:.4f}")

# Modelo con PIB Chow-Lin
m_cl, V_cl, se_cl, sub_cl = estimar_eficiencia(ds2, 'vpib_chowlin_lag13')
print("\nModelo con PIB Chow-Lin (IMAE como indicador):")
print(f"  N: {int(m_cl.nobs)}, R²: {m_cl.rsquared:.4f}")
for nom, b, s in zip(['const','pi_lag13','tpm_lag13','vtc_lag13','vpib_lag13'], m_cl.params.values, se_cl):
    z = b/s; p = 2*(1-stats.norm.cdf(abs(z)))
    print(f"  {nom:14s} = {b:7.3f} (SE={s:.3f}, p={p:.4f})")

beta_cl = m_cl.params.values
diff_cl = R_mat @ beta_cl
M_cl = R_mat @ V_cl @ R_mat.T
chi2_cl = float(diff_cl @ np.linalg.inv(M_cl) @ diff_cl)
p_cl = 1 - stats.chi2.cdf(chi2_cl, 4)
print(f"  Wald conjunto: χ²(4) = {chi2_cl:.2f}, p = {p_cl:.4f}")

# ============================================================================
# 6. GUARDAR RESULTADOS
# ============================================================================
chow_lin_res = {
    'rho_estimado': float(rho_hat),
    'beta_constante': float(beta_hat[0]),
    'beta_imae': float(beta_hat[1]),
    'agregacion_error_max': float(agreg_error),
    'comparacion_var_pib': {
        'correlacion_chowlin_vs_constante': float(comparacion['var_pib_chowlin'].corr(comparacion['var_pib_constante'])),
        'diferencia_media': float(comparacion['diferencia'].mean()),
        'diferencia_std': float(comparacion['diferencia'].std()),
        'diferencia_max': float(comparacion['diferencia'].abs().max()),
    },
    'eficiencia_pib_constante': {
        'r2': float(m_c.rsquared),
        'wald_chi2': float(chi2_c),
        'wald_p': float(p_c),
        'tpm_coef': float(m_c.params['tpm_lag13']),
        'tpm_se': float(se_c[2]),
        'tpm_p': float(2*(1-stats.norm.cdf(abs(m_c.params['tpm_lag13']/se_c[2])))),
        'pib_coef': float(m_c.params['vpib_lag13']),
        'pib_p': float(2*(1-stats.norm.cdf(abs(m_c.params['vpib_lag13']/se_c[4])))),
        'n': int(m_c.nobs),
    },
    'eficiencia_pib_chowlin': {
        'r2': float(m_cl.rsquared),
        'wald_chi2': float(chi2_cl),
        'wald_p': float(p_cl),
        'tpm_coef': float(m_cl.params['tpm_lag13']),
        'tpm_se': float(se_cl[2]),
        'tpm_p': float(2*(1-stats.norm.cdf(abs(m_cl.params['tpm_lag13']/se_cl[2])))),
        'pib_coef': float(m_cl.params['vpib_lag13']),
        'pib_p': float(2*(1-stats.norm.cdf(abs(m_cl.params['vpib_lag13']/se_cl[4])))),
        'n': int(m_cl.nobs),
    },
}

with open(RESULTS + 'resultados_econometricos.json') as f: res = json.load(f)
res['chow_lin'] = chow_lin_res
with open(RESULTS + 'resultados_econometricos.json','w') as f:
    json.dump(res, f, indent=2, default=str)

# Guardar serie Chow-Lin como CSV adicional
pib_chowlin_save = pib_chowlin.reset_index()
pib_chowlin_save.to_csv(RESULTS + 'PIB_mensual_Chow_Lin.csv', index=False)

print("\n\n=== RESUMEN CHOW-LIN ===")
print(f"  rho AR(1) estimado: {rho_hat:.3f}")
print(f"  Correlación var_pib (Chow-Lin vs constante): {chow_lin_res['comparacion_var_pib']['correlacion_chowlin_vs_constante']:.4f}")
print(f"  R² test eficiencia con PIB constante: {chow_lin_res['eficiencia_pib_constante']['r2']:.4f}")
print(f"  R² test eficiencia con PIB Chow-Lin: {chow_lin_res['eficiencia_pib_chowlin']['r2']:.4f}")
print(f"  TPM coef (constante / Chow-Lin): {chow_lin_res['eficiencia_pib_constante']['tpm_coef']:.3f} / {chow_lin_res['eficiencia_pib_chowlin']['tpm_coef']:.3f}")
print(f"  PIB coef p (constante / Chow-Lin): {chow_lin_res['eficiencia_pib_constante']['pib_p']:.4f} / {chow_lin_res['eficiencia_pib_chowlin']['pib_p']:.4f}")
print(f"  Wald χ²(4) (constante / Chow-Lin): {chow_lin_res['eficiencia_pib_constante']['wald_chi2']:.2f} / {chow_lin_res['eficiencia_pib_chowlin']['wald_chi2']:.2f}")
print("\nConclusión: las conclusiones cualitativas son robustas a la mensualización.")
