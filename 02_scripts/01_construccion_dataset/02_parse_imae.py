"""
Construcción IMAE mensual y aplicación de Chow-Lin para mensualización del PIB.

Reemplaza la serie de PIB obtenida por asignación constante en build_dataset_oficial.py
con la serie obtenida por Chow-Lin con IMAE como indicador relacionado.

Verifica también si el coeficiente sobre el PIB en el test de eficiencia informacional
cambia con la nueva mensualización.
"""
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
# 1. PARSE IMAE
# ============================================================================
print("=== PARSE DEL IMAE ===\n")
raw = pd.read_excel(DATA_RAW + 'IMAE_2018_100_BCRD.xlsx', sheet_name='IMAE', header=None)

# Estructura: filas 0-7 son metadatos. Los datos empiezan en fila 8 (enero año 1).
# La columna 0 contiene el año (cada 12 filas), la columna 1 el mes, la 2 el índice original.
# Vamos a descubrir el primer año

# Buscar el primer año (entero) en columna 0
primer_ano = None
for i in range(len(raw)):
    val = raw.iloc[i, 0]
    if pd.notna(val) and isinstance(val, (int, float)) and 1990 <= val <= 2030:
        primer_ano = int(val)
        primer_idx = i
        break
print(f"Primer año detectado: {primer_ano} en fila {primer_idx}")

# Recorrer filas: cada año tiene 12 meses + posible fila vacía
# Construir DataFrame con columnas Año, Mes, IMAE_original
meses_es = ['Enero','Febrero','Marzo','Abril','Mayo','Junio',
            'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
mes_a_num = {m: i+1 for i, m in enumerate(meses_es)}

# Recorrer y extraer
filas = []
ano_actual = None
for i in range(len(raw)):
    v0 = raw.iloc[i, 0]
    v1 = raw.iloc[i, 1]
    v2 = raw.iloc[i, 2]
    if pd.notna(v0) and isinstance(v0, (int, float)) and 1990 <= v0 <= 2030:
        ano_actual = int(v0)
    if ano_actual is not None and pd.notna(v1) and isinstance(v1, str) and v1.strip() in mes_a_num:
        if pd.notna(v2):
            filas.append({
                'Año': ano_actual,
                'Mes': mes_a_num[v1.strip()],
                'IMAE': float(v2)
            })

imae = pd.DataFrame(filas)
imae['Fecha'] = pd.to_datetime(dict(year=imae['Año'], month=imae['Mes'], day=1))
imae = imae.sort_values('Fecha').reset_index(drop=True)
print(f"IMAE construido: {len(imae)} obs")
print(f"Primer registro: {imae['Fecha'].min().strftime('%Y-%m')} = {imae.iloc[0]['IMAE']:.3f}")
print(f"Último registro: {imae['Fecha'].max().strftime('%Y-%m')} = {imae.iloc[-1]['IMAE']:.3f}")
print(f"Tabla muestra primeros y últimos:")
print(imae.head(3).to_string())
print(imae.tail(3).to_string())

# ============================================================================
# 2. CARGAR PIB TRIMESTRAL
# ============================================================================
print("\n=== CARGAR PIB TRIMESTRAL ===\n")
# Usar el archivo PIB existente
pib_xl = pd.read_excel(DATA_RAW + 'PIB_BCRD.xlsx', sheet_name=0, header=None)
print(f"Forma: {pib_xl.shape}")
print(pib_xl.head(15).to_string())
EOF