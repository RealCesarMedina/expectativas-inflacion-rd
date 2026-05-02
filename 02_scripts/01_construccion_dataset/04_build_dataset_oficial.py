"""
Construcción del dataset definitivo con series OFICIALES OBSERVADAS del BCRD:
- IPC: serie empalmada oficial del BCRD (base oct 2019 - sep 2020 = 100)
- TPM: tasa de política monetaria efectiva (mensual)
- TC: tipo de cambio nominal (compra) — agregado a mensual desde el histórico diario
- PIB: índice de volumen del PIB real (trimestral, mensualizado)
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


import pandas as pd
import numpy as np

# ============================================================================
# 1. IPC OFICIAL EMPALMADO (BCRD)
# ============================================================================
ipc_raw = pd.read_excel(DATA_RAW + 'IPC_General_Mensual_BCRD.xlsx',
                         sheet_name='IPC base 2019-2020', header=None)
meses = {'Enero':1,'Febrero':2,'Marzo':3,'Abril':4,'Mayo':5,'Junio':6,
         'Julio':7,'Agosto':8,'Septiembre':9,'Octubre':10,'Noviembre':11,'Diciembre':12}

ipc_data = []
ano = None
for i in range(7, len(ipc_raw)):
    v0, v1, v2 = ipc_raw.iloc[i,0], ipc_raw.iloc[i,1], ipc_raw.iloc[i,2]
    if not pd.isna(v0):
        try:
            ai = int(float(v0))
            if 1980 <= ai <= 2030: ano = ai
        except: pass
    if not pd.isna(v1):
        s = str(v1).strip()
        if s in meses and ano is not None and not pd.isna(v2):
            ipc_data.append({'Año':ano,'Mes':meses[s],'IPC':float(v2)})

ipc = pd.DataFrame(ipc_data).sort_values(['Año','Mes']).reset_index(drop=True)
ipc['Fecha'] = pd.to_datetime(dict(year=ipc['Año'], month=ipc['Mes'], day=1))
ipc = ipc[ipc['Año'] >= 2009].reset_index(drop=True)
ipc['pi_t'] = (ipc['IPC'] / ipc['IPC'].shift(12) - 1) * 100

print(f"IPC oficial empalmado: {len(ipc)} obs ({ipc['Fecha'].min().strftime('%Y-%m')} a {ipc['Fecha'].max().strftime('%Y-%m')})")

# Verificación contra valores oficiales conocidos
checks = [(2020,4,1.04),(2020,12,5.55),(2021,12,8.50),(2022,4,9.64),
          (2024,8,3.42),(2025,8,3.72),(2026,3,4.63)]
print("\nVerificación contra valores oficiales conocidos:")
ok_count = 0
for a,m,esp in checks:
    obs = ipc[(ipc['Año']==a)&(ipc['Mes']==m)]['pi_t']
    if len(obs)>0:
        v = obs.values[0]
        ok = abs(v-esp)<0.10
        if ok: ok_count += 1
        print(f"  {'✓' if ok else '~'} {a}-{m:02d}: oficial≈{esp}%, calculado={v:.2f}% (dif {v-esp:+.2f})")
print(f"  >>> {ok_count}/{len(checks)} coinciden al centésimo")

# Verificar 2012 que antes estaba como gap
print("\n2012 (antes era gap, ahora oficial):")
print(ipc[ipc['Año']==2012][['Año','Mes','IPC','pi_t']].to_string(index=False))

# ============================================================================
# 2. TPM OFICIAL
# ============================================================================
tpm_raw = pd.read_excel(DATA_RAW + 'Serie_TPM_BCRD.xlsx', sheet_name='Tasas', header=None)
meses_abr = {'Ene':1,'Feb':2,'Mar':3,'Abr':4,'May':5,'Jun':6,'Jul':7,'Ago':8,'Sep':9,'Oct':10,'Nov':11,'Dic':12}
tpm_data = []
ano_t = None
for i in range(6, len(tpm_raw)):
    v0, v1, v2 = tpm_raw.iloc[i,0], tpm_raw.iloc[i,1], tpm_raw.iloc[i,2]
    if not pd.isna(v0):
        try:
            ai = int(float(v0))
            if 2004 <= ai <= 2030: ano_t = ai
        except: pass
    if not pd.isna(v1):
        s = str(v1).strip()
        if s in meses_abr and ano_t is not None and not pd.isna(v2):
            tpm_data.append({'Año':ano_t,'Mes':meses_abr[s],'TPM_obs':float(v2)*100})

tpm = pd.DataFrame(tpm_data).sort_values(['Año','Mes']).reset_index(drop=True)
tpm['Fecha'] = pd.to_datetime(dict(year=tpm['Año'], month=tpm['Mes'], day=1))
print(f"\nTPM oficial: {len(tpm)} obs")
print("Muestra TPM 2020-2023:")
print(tpm[(tpm['Año']>=2020)&(tpm['Año']<=2023)].head(10).to_string(index=False))

# ============================================================================
# 3. TIPO DE CAMBIO — agregar a mensual desde diario
# ============================================================================
tc_raw = pd.read_excel(DATA_RAW + 'BCRD_TC_diario.xlsx',
                       sheet_name='Histórico', header=None)
tc_data = []
for i in range(9, len(tc_raw)):
    v = tc_raw.iloc[i].tolist()
    try:
        ano = int(v[0]); mes = int(v[1]); dia = int(v[2])
        compra = float(v[3])
        if 2003 <= ano <= 2030 and 1 <= mes <= 12 and 1 <= dia <= 31:
            tc_data.append({'Año':ano,'Mes':mes,'Día':dia,'Compra':compra})
    except (ValueError, TypeError):
        continue

tc_diario = pd.DataFrame(tc_data)
tc_mensual = tc_diario.groupby(['Año','Mes'])['Compra'].mean().reset_index()
tc_mensual['Fecha'] = pd.to_datetime(dict(year=tc_mensual['Año'], month=tc_mensual['Mes'], day=1))
tc_mensual['TC_obs'] = tc_mensual['Compra']
tc_mensual['var_tc'] = (tc_mensual['Compra']/tc_mensual['Compra'].shift(12) - 1) * 100
print(f"\nTC mensual: {len(tc_mensual)} obs")
print("Muestra TC variación interanual 2020-2023:")
print(tc_mensual[(tc_mensual['Año']>=2020)&(tc_mensual['Año']<=2023)].head(8)[['Año','Mes','Compra','var_tc']].to_string(index=False))

# ============================================================================
# 4. PIB — trimestral, mensualizar
# ============================================================================
pib_raw = pd.read_excel(DATA_RAW + 'PIB_BCRD.xlsx', sheet_name='PIB_Trimestral', header=None)
pib_data = []
ano_p = None
trim_map = {'I':1,'II':2,'III':3,'IV':4}
# Encontrar primero el año inicial (busca "Promedio AAAA")
for i in range(7, len(pib_raw)):
    v0 = pib_raw.iloc[i,0]
    if pd.isna(v0): continue
    s = str(v0).strip()
    if s.startswith('Promedio'):
        try: ano_p = int(s.split()[-1])
        except: pass
        break

# Re-parsear desde el inicio. Estrategia: el primer bloque sin año previo es el primer año.
# Por estructura, aparece I, II, III, IV (4 trimestres) seguidos por "Promedio AAAA".
ano_actual = None
trims_acumulados = []
for i in range(7, len(pib_raw)):
    v0, v1, v2 = pib_raw.iloc[i,0], pib_raw.iloc[i,1], pib_raw.iloc[i,2]
    if pd.isna(v0): continue
    s = str(v0).strip()
    if s.startswith('Promedio'):
        # Tomar el primer token que parezca año entre los siguientes
        toks = s.replace('Promedio','').replace('(p)','').split()
        ano_actual = None
        for tk in toks:
            try:
                yr = int(tk.strip())
                if 2000 <= yr <= 2030:
                    ano_actual = yr; break
            except: pass
        if ano_actual is None: continue
        # Asignar este año a los 4 trimestres acumulados
        for k, (idx_v1, idx_v2) in enumerate(trims_acumulados):
            pib_data.append({'Año':ano_actual,'Trim':k+1,
                              'PIB_idx':float(idx_v1),
                              'var_pib':float(idx_v2) if not pd.isna(idx_v2) else None})
        trims_acumulados = []
    elif s in trim_map and not pd.isna(v1):
        trims_acumulados.append((v1, v2))

pib_t = pd.DataFrame(pib_data).sort_values(['Año','Trim']).reset_index(drop=True)
print(f"\nPIB trimestral: {len(pib_t)} obs (años {pib_t['Año'].min()}-{pib_t['Año'].max()})")
print("Muestra PIB 2020-2023:")
print(pib_t[(pib_t['Año']>=2020)&(pib_t['Año']<=2023)].to_string(index=False))

# Mensualizar PIB
pib_m_rows = []
for _, r in pib_t.iterrows():
    a, t = int(r['Año']), int(r['Trim'])
    meses_t = [(t-1)*3 + 1, (t-1)*3 + 2, (t-1)*3 + 3]
    for m in meses_t:
        pib_m_rows.append({'Año': a, 'Mes': m,
                            'PIB_obs': r['PIB_idx'],
                            'var_pib': r['var_pib']})
pib_m = pd.DataFrame(pib_m_rows)
pib_m['Fecha'] = pd.to_datetime(dict(year=pib_m['Año'], month=pib_m['Mes'], day=1))

# ============================================================================
# 5. CONSOLIDAR
# ============================================================================
ds = ipc[['Fecha','Año','Mes','IPC','pi_t']].copy()
ds = ds.merge(tpm[['Fecha','TPM_obs']], on='Fecha', how='left')
ds = ds.merge(tc_mensual[['Fecha','TC_obs','var_tc']], on='Fecha', how='left')
ds = ds.merge(pib_m[['Fecha','PIB_obs','var_pib']], on='Fecha', how='left')

print(f"\n=== DATASET CONSOLIDADO ===")
print(f"Forma: {ds.shape}, periodo: {ds['Fecha'].min().strftime('%Y-%m')} a {ds['Fecha'].max().strftime('%Y-%m')}")
print(f"No nulos por columna:")
print(ds[['pi_t','TPM_obs','var_tc','var_pib']].notna().sum())
print(f"\nUltimos 6 meses:")
print(ds[['Año','Mes','pi_t','TPM_obs','var_tc','var_pib']].tail(6).to_string(index=False))

ds.to_csv(RESULTS + 'Dataset_Consolidado_BCRD.csv', index=False)
print("\nGuardado en (RESULTS)Dataset_Consolidado_BCRD.csv")
