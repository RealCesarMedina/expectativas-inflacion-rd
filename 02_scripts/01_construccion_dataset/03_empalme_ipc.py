"""
Empalme correcto del IPC del BCRD a base única "Diciembre 2010 = 100".

PROBLEMA DETECTADO:
El archivo oficial del calculador del BCRD entrega el IPC en dos bases distintas:
- Pre-octubre 2020: base "Diciembre 2010 = 100"
- Octubre 2020 en adelante: base "Octubre 2019 - Septiembre 2020 = 100"

El cambio de base se manifiesta como un salto del IPC de 139.40 (sep 2020)
a 103.276 (oct 2020), pero la columna "Variación porcentual mensual" del archivo
indica que la variación real fue +0.66% en oct 2020. Esto permite reconstruir
el factor de empalme.
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

raw = pd.read_excel(DATA_RAW + 'IPC_General_Mensual_BCRD.xlsx',
                    sheet_name=0, header=None)

meses = {'Enero':1,'Febrero':2,'Marzo':3,'Abril':4,'Mayo':5,'Junio':6,
         'Julio':7,'Agosto':8,'Septiembre':9,'Octubre':10,'Noviembre':11,'Diciembre':12}

ipc_data = []
ano = None
for i in range(10, len(raw)):
    v0, v1, v2 = raw.iloc[i, 0], raw.iloc[i, 1], raw.iloc[i, 2]
    if pd.isna(v0): continue
    s = str(v0).strip()
    try:
        ai = int(float(s))
        if 2009 <= ai <= 2030:
            ano = ai; continue
    except: pass
    if s in meses and ano is not None and not pd.isna(v1):
        ipc_data.append({'Año': ano, 'Mes': meses[s],
                         'IPC_archivo': float(v1),
                         'Var_Mens_archivo': float(v2) if not pd.isna(v2) else None})

df = pd.DataFrame(ipc_data).sort_values(['Año','Mes']).reset_index(drop=True)
df['Fecha'] = pd.to_datetime(dict(year=df['Año'], month=df['Mes'], day=1))

# Calcular el factor de empalme en oct 2020
ipc_sep20 = df[(df['Año']==2020) & (df['Mes']==9)]['IPC_archivo'].values[0]
ipc_oct20_archivo = df[(df['Año']==2020) & (df['Mes']==10)]['IPC_archivo'].values[0]
var_oct20 = df[(df['Año']==2020) & (df['Mes']==10)]['Var_Mens_archivo'].values[0]
ipc_oct20_real = ipc_sep20 * (1 + var_oct20/100)
factor = ipc_oct20_real / ipc_oct20_archivo

print(f"=== EMPALME ===")
print(f"IPC sep-2020 (base vieja):  {ipc_sep20}")
print(f"IPC oct-2020 (archivo, base nueva): {ipc_oct20_archivo}")
print(f"Var. mensual oct-2020 (archivo): {var_oct20:.4f}%")
print(f"IPC oct-2020 reconstruido (base vieja): {ipc_oct20_real:.4f}")
print(f"Factor de empalme: {factor:.6f}")

# Aplicar empalme: meses post-oct 2020 multiplicados por factor
df['IPC'] = np.where(
    (df['Fecha'] >= '2020-10-01'),
    df['IPC_archivo'] * factor,
    df['IPC_archivo']
)

# Reindexar para incluir 2012 vacío
todas_fechas = pd.date_range('2010-01-01', '2026-03-01', freq='MS')
df_full = df.set_index('Fecha').reindex(todas_fechas).rename_axis('Fecha').reset_index()
df_full['Año'] = df_full['Fecha'].dt.year
df_full['Mes'] = df_full['Fecha'].dt.month

# Calcular interanual con la serie empalmada
df_full['pi_t_oficial'] = (df_full['IPC'] / df_full['IPC'].shift(12) - 1) * 100

# Patches 2012-2013 desde Informes Mensuales
patches = {
    (2012,1):7.31,(2012,2):6.73,(2012,3):5.39,(2012,4):4.46,(2012,5):3.61,
    (2012,6):3.67,(2012,7):4.20,(2012,8):3.48,(2012,9):3.54,(2012,10):3.78,
    (2012,11):3.91,(2012,12):3.91,
    (2013,1):4.66,(2013,2):4.85,(2013,3):5.22,(2013,4):4.91,(2013,5):5.58,
    (2013,6):5.42,(2013,7):4.45,(2013,8):4.66,(2013,9):4.85,(2013,10):4.61,
    (2013,11):3.96,(2013,12):3.88,
}
df_full['pi_t'] = df_full['pi_t_oficial'].copy()
df_full['fuente_pi'] = 'IPC oficial empalmado (base Dic 2010 = 100)'
for (a,m), val in patches.items():
    mask = (df_full['Año']==a) & (df_full['Mes']==m)
    df_full.loc[mask, 'pi_t'] = val
    df_full.loc[mask, 'fuente_pi'] = 'Informe Mensual IPC del BCRD (gap 2012 en archivo)'

# VERIFICACIÓN contra valores oficiales conocidos
print(f"\n=== VERIFICACIÓN CONTRA INFLACIÓN INTERANUAL OFICIAL CONOCIDA ===")
checks = [
    (2020,4,1.04,'shock COVID'),
    (2020,12,5.55,'cierre 2020'),
    (2021,4,9.64,'pico mid-2021 (no, es mar 2022 actually)'),
    (2021,12,8.50,'cierre 2021'),
    (2022,4,9.64,'pico shock global'),
    (2022,12,7.83,'cierre 2022'),
    (2023,8,3.99,'normalización'),
    (2024,4,3.03,'2024'),
    (2024,8,3.42,'agosto 2024'),
    (2025,8,3.72,'agosto 2025'),
]
print(f"{'Mes':<10}{'Oficial':>10}{'Calculado':>12}{'Dif':>10}  Descripción")
for a,m,esp,desc in checks:
    obs = df_full[(df_full['Año']==a)&(df_full['Mes']==m)]['pi_t'].values
    if len(obs)>0 and not pd.isna(obs[0]):
        d = obs[0]-esp
        marker = '✓' if abs(d)<0.30 else ('~' if abs(d)<0.60 else '✗')
        print(f"  {marker} {a}-{m:02d}  {esp:>8.2f}%  {obs[0]:>9.2f}%  {d:>+7.2f}  {desc}")

# Estadísticos básicos del nuevo pi_t
pi_2011 = df_full[df_full['Año']>=2011]['pi_t'].dropna()
print(f"\n=== ESTADÍSTICOS pi_t POST-EMPALME (2011-2026) ===")
print(f"  N: {len(pi_2011)}")
print(f"  Media: {pi_2011.mean():.2f}%, Mediana: {pi_2011.median():.2f}%")
print(f"  Min: {pi_2011.min():.2f}%, Max: {pi_2011.max():.2f}%")
print(f"  DesvEst: {pi_2011.std():.2f}")

# Guardar
df_full[['Año','Mes','Fecha','IPC','pi_t','fuente_pi']].to_csv(
    DATA_RAW + 'IPC_empalmado_BCRD.csv', index=False)
print("\nGuardado en (RESULTS)IPC_empalmado.csv")
