"""
Parsea el archivo oficial del IPC del BCRD y calcula la inflación interanual
mes a mes para el periodo 2010m1 - 2026m3.
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

# Leer archivo
raw = pd.read_excel(DATA_RAW + 'IPC_General_Mensual_BCRD.xlsx',
                    sheet_name=0, header=None)

meses = {'Enero':1, 'Febrero':2, 'Marzo':3, 'Abril':4, 'Mayo':5, 'Junio':6,
         'Julio':7, 'Agosto':8, 'Septiembre':9, 'Octubre':10, 'Noviembre':11, 'Diciembre':12}

# Recorrer filas: año-fila marca el año actual; meses tienen el índice
data = []
año_actual = None
for i in range(10, len(raw)):
    val0 = raw.iloc[i, 0]
    val1 = raw.iloc[i, 1]
    if pd.isna(val0):
        continue
    s = str(val0).strip()
    # Detectar año (4 dígitos como integer)
    try:
        ano_int = int(float(s))
        if 2009 <= ano_int <= 2030:
            año_actual = ano_int
            continue
    except (ValueError, TypeError):
        pass
    # Detectar mes
    mes_clean = s.strip()
    if mes_clean in meses and año_actual is not None and not pd.isna(val1):
        data.append({
            'Año': año_actual,
            'Mes': meses[mes_clean],
            'IPC': float(val1),
            'Var_Mensual': float(raw.iloc[i, 2]) if not pd.isna(raw.iloc[i, 2]) else None
        })

ipc = pd.DataFrame(data).sort_values(['Año','Mes']).reset_index(drop=True)
ipc['Fecha'] = pd.to_datetime(dict(year=ipc['Año'], month=ipc['Mes'], day=1))

# Calcular inflación interanual
ipc['pi_t'] = (ipc['IPC'] / ipc['IPC'].shift(12) - 1) * 100

print(f"Total filas: {len(ipc)}")
print(f"Periodo: {ipc['Fecha'].min().strftime('%Y-%m')} a {ipc['Fecha'].max().strftime('%Y-%m')}")
print(f"\nPrimeros datos con interanual disponible (desde 2011):")
print(ipc[ipc['pi_t'].notna()].head(15)[['Año','Mes','IPC','pi_t']].to_string(index=False))
print(f"\nÚltimos 10 datos:")
print(ipc.tail(10)[['Año','Mes','IPC','pi_t']].to_string(index=False))

# Verificar puntos de control conocidos
print("\n=== VERIFICACIÓN CON PUNTOS CONOCIDOS ===")
checks = [(2011,5,9.01,'pico pre-EMI'), (2015,3,0.04,'mínimo histórico'),
          (2022,4,9.64,'pico post-pandemia'), (2024,8,3.42,'agosto 2024'),
          (2024,4,3.03,'abril 2024'), (2025,8,3.71,'agosto 2025')]
for ano,mes,esperado,desc in checks:
    obs = ipc[(ipc['Año']==ano) & (ipc['Mes']==mes)]['pi_t'].values
    if len(obs) > 0:
        diff = obs[0] - esperado
        marker = '✓' if abs(diff)<0.10 else ('~' if abs(diff)<0.30 else '✗')
        print(f"  {marker} {ano}-{mes:02d} ({desc}): oficial={obs[0]:.2f}%, esperado={esperado:.2f}%, dif={diff:+.2f}")

# Guardar
ipc[['Año','Mes','Fecha','IPC','Var_Mensual','pi_t']].to_csv(
    DATA_RAW + 'IPC_oficial_BCRD.csv', index=False)
print("\nGuardado en (RESULTS)IPC_oficial.csv")
