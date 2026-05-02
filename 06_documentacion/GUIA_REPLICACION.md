# Guía detallada de replicación

Esta guía explica paso a paso cómo reproducir todos los resultados del paper desde los datos originales del BCRD.

---

## Requerimientos previos

### Software

- **Python ≥ 3.10** con los siguientes paquetes:
  - `pandas` ≥ 2.0
  - `numpy` ≥ 1.24
  - `statsmodels` ≥ 0.14
  - `scipy` ≥ 1.10
  - `matplotlib` ≥ 3.7
  - `openpyxl` (para leer archivos Excel del BCRD)

  Instalación:
  ```bash
  pip install pandas numpy statsmodels scipy matplotlib openpyxl
  ```

- **Node.js ≥ 18** con la librería `docx`:
  ```bash
  npm install docx
  ```

### Datos

Los archivos en `01_data_raw/` deben estar disponibles. Si se desea descargar versiones más recientes, las fuentes públicas son:

- EEM (Encuesta Mensual de Expectativas Macroeconómicas): https://www.bancentral.gov.do/a/d/2549-encuesta-de-expectativas-macroeconomicas
- IPC (serie empalmada): https://www.bancentral.gov.do/a/d/2530-precios
- TPM, tipo de cambio, PIB: portal estadístico del BCRD

---

## Paso 1 — Construcción del dataset

**Directorio**: `02_scripts/01_construccion_dataset/`

Este paso transforma los archivos crudos del BCRD en un dataset consolidado listo para el análisis econométrico.

### 1.1 Extracción del IPC

```bash
python 01_parse_ipc.py
```

Lee el archivo del IPC oficial del BCRD y produce `ipc_oficial.csv` con la serie limpia. La verificación contra valores oficiales conocidos coincide al centésimo en siete puntos de control distribuidos a lo largo de la muestra.

### 1.2 Extracción del IMAE

```bash
python 02_parse_imae.py
```

Procesa el Índice Mensual de Actividad Económica del BCRD. Necesario para la mensualización del PIB por Chow-Lin en el paso de robustez.

### 1.3 Empalme del IPC

```bash
python 03_empalme_ipc.py
```

Reconcilia las distintas bases de canasta del IPC dominicano (canasta 2010, canasta ENGIH 2018) en una serie homogénea desde 1984. Output: `ipc_empalmado.csv`.

### 1.4 Construcción del dataset consolidado

```bash
python 04_build_dataset_oficial.py
```

Une todas las series (IPC empalmado, EEM, TPM, tipo de cambio, PIB) en un único dataset mensual. Output: `dataset_oficial.csv` con todas las variables y sus rezagos requeridos por el análisis.

---

## Paso 2 — Análisis econométrico principal

**Directorio**: `02_scripts/02_analisis_principal/`

```bash
python 01_run_analysis_principal.py
```

Este es el script central del paper. Ejecuta:

- **T1 Insesgamiento**: e_t = α + u_t con HAC Newey-West (full, pre, post)
- **T2 Mincer-Zarnowitz**: π_t = α + β·E_{t−12}[π_t] + u_t, prueba Wald de α=0 ∧ β=1
- **T3 Persistencia**: e_t = α + ρ·e_{t−12} + u_t
- **T4 Eficiencia informacional**: e_t = α + γ'·X_{t−13} + u_t con X = (π, TPM, Δe, Δy)
- **T5 Coibion-Gorodnichenko**: e_t = α + λ·rev_t + u_t por subperíodo
- **Diebold-Mariano**: comparación contra random walk, AR(1) recursivo y ancla a meta 4%
- **Bai-Perron**: detección de quiebres estructurales (m=0 a m=5)
- **Quandt-Andrews**: con valores críticos de Andrews (1993)
- **Diagnósticos**: BP, BG, LB, RESET, JB para cada especificación

Output principal: `output/resultados.json` con todos los resultados numéricos.

---

## Paso 3 — Análisis de robustez

**Directorio**: `02_scripts/03_robustez/`

### 3.1 Sesgo asimétrico y tres regímenes

```bash
python 01_run_analysis_robustez.py
```

- **Sesgo asimétrico estado-dependiente**: condicional al régimen de inflación (alta vs baja respecto a la mediana muestral), con prueba formal de igualdad de regímenes
- **Tres regímenes con cortes exógenos**: pre-2017, 2017-2020m2, post-2020 basados en cambios metodológicos documentados de la EEM
- **Bai-Perron extendido**: hasta m=5 con verificación de BIC monótonamente decreciente

### 3.2 Threshold-MZ y ARDL extendido

```bash
python 02_run_analysis_robustez_suplementario.py
```

- **Threshold-MZ con meta 4%**: especificación con la meta del BCRD como umbral exógeno
- **ARDL con rezagos 12-18 de la TPM**: especificación general que descarta dependencia del rezago específico (Wald χ²(7) = 35.13, p < 0.001)

### 3.3 Inferencia de robustez nivel 2

```bash
python 03_run_analysis_nivel2.py
```

- **Bootstrap por bloques** tipo Politis-Romano (1994) con b = 18, 5,000 réplicas
- **Kiefer-Vogelsang (2005)** con bandwidth fijo b = 0.5
- **Descomposición R²** entre revisión sola, TPM sola y modelo combinado (Cuadro 8)
- **Bandas IC95% para lambda rolling** punto-a-punto (HAC Newey-West)

### 3.4 Mensualización del PIB

```bash
python 04_run_chow_lin.py
```

Implementa Chow y Lin (1971) con el IMAE como indicador relacionado para mensualizar el PIB trimestral. El parámetro AR(1) de los residuales mensuales colapsa a ρ̂ ≈ 0, lo que indica que el IMAE captura prácticamente toda la variación trimestral del PIB. La conclusión central del test de eficiencia informacional es robusta a este cambio de método.

---

## Paso 4 — Generación de figuras

**Directorio**: `02_scripts/04_visualizacion/`

```bash
python 01_build_figures_initial.py
python 02_figuras_extra.py
python 03_regenerate_figs.py
```

Produce las 7 figuras finales en `figures/` (PNG a 250 dpi):

1. **Figura 1**: inflación realizada vs expectativa formada 12 meses antes, con sombreado post-marzo 2020
2. **Figura 2**: scatter de Mincer-Zarnowitz con leyenda explícita pre/post-pandemia
3. **Figura 3**: test de Coibion-Gorodnichenko por subperíodo
4. **Figura 4**: lambda rolling con bandas de confianza IC95% punto-a-punto, sin eje ψ secundario, con zona endpoint sensible marcada (corrección PR#7)
5. **Figura 5**: comparación OOS de pronósticos
6. **Figura 6**: quiebres estructurales Bai-Perron con m=3 y BIC decreciente hasta m=5
7. **Figura 7**: sesgo condicional al estado de inflación

El script `03_regenerate_figs.py` regenera las Figuras 2, 4 y 6 con las correcciones finales de estilo y bandas de confianza IC95%.

---

## Paso 5 — Compilación del paper

**Directorio**: `05_paper/`

```bash
node build_paper.js
```

Produce el documento `.docx` final con:

- 17,084 palabras
- 8 cuadros con datos del JSON de resultados
- 7 figuras embebidas
- 49 referencias bibliográficas
- Estructura completa de 9 secciones

---

## Verificación de resultados

Los resultados clave que se deben reproducir exactamente son:

| Test | Estadístico | p-valor |
|---|---|---|
| Eficiencia informacional T4 | Wald χ²(4) = 21.68 | < 0.001 |
| ARDL conjunto rezagos 12-18 TPM | Wald χ²(7) = 35.13 | < 0.001 |
| Coibion-Gorodnichenko post | λ = 1.19 | < 0.001 |
| Sesgo asimétrico (igualdad) | Wald χ² = 17.85 | < 0.001 |
| Mincer-Zarnowitz post (Hodrick) | χ²(2) = 10.13 | 0.006 |

R² parcial de la TPM rezagada sobre varianza total del error: **0.383** (≈ 38%, equivalente al 86% de la varianza explicada).

---

## Tiempo aproximado de ejecución

En una máquina estándar (8GB RAM, procesador moderno):

- Paso 1 (construcción dataset): ~30 segundos
- Paso 2 (análisis principal): ~2 minutos
- Paso 3 (robustez):
  - 3.1 + 3.2: ~1 minuto
  - 3.3 (bootstrap 5,000 réplicas): ~10-15 minutos
  - 3.4 (Chow-Lin): ~30 segundos
- Paso 4 (figuras): ~1 minuto
- Paso 5 (compilación paper): ~15 segundos

**Total**: aproximadamente 15-20 minutos.

---

## Solución de problemas comunes

### "ModuleNotFoundError: No module named 'docx'"

En el paso 5, el módulo `docx` se refiere a la librería de **Node.js**, no a Python. Instalación:
```bash
npm install docx
```

### "FileNotFoundError: Historico-EEM.xlsx"

Los scripts esperan los archivos del BCRD en `01_data_raw/`. Verificar que los nombres exactos coincidan o ajustar las rutas en los scripts.

### "Bootstrap por bloques tarda más de 30 minutos"

Reducir el número de réplicas en `03_run_analysis_nivel2.py` de 5,000 a 1,000 para una verificación rápida. Los IC bootstrap se reportarán con menor precisión pero el rechazo cualitativo se mantiene.
