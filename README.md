# Racionalidad y Rigidez Informacional de las Expectativas de Inflación en República Dominicana

**Paquete de replicación completo**
Autor: César Emilio Medina Tineo

---

## Sobre este repositorio

Este repositorio contiene todos los archivos que hicieron posible la creación del paper, organizados de manera que cualquier persona pueda replicar el análisis desde cero. La estructura sigue el flujo lógico del trabajo: datos crudos → construcción del dataset → análisis econométrico → análisis de robustez → visualización → documento final.

---

## Estructura del repositorio

```
paper_package/
│
├── 01_data_raw/                       Datos originales del BCRD (xlsx + csv espejo)
│   ├── Historico-EEM_BCRD.xlsx        Encuesta Mensual de Expectativas Macroeconómicas
│   ├── Historico-EEM_BCRD__*.csv      Hojas exportadas (Mediana, Promedio, etc.)
│   ├── IPC_oficial_BCRD.csv           Índice de Precios al Consumidor (extraído)
│   ├── IPC_empalmado_BCRD.csv         IPC empalmado entre bases
│   ├── IPC_General_Mensual_BCRD.xlsx  IPC general mensual oficial
│   ├── IMAE_2018_100_BCRD.xlsx        Índice Mensual de Actividad Económica
│   ├── Dataset_EEM_Realizada.xlsx
│   └── Dataset_Expectativas_Inflacion_RD.xlsx
│
├── 02_scripts/                        Scripts Python en orden de ejecución
│   │
│   ├── 01_construccion_dataset/       Paso 1: Construir el dataset
│   │   ├── 01_parse_ipc.py            Extrae IPC del archivo oficial del BCRD
│   │   ├── 02_parse_imae.py           Extrae IMAE para mensualización Chow-Lin
│   │   ├── 03_empalme_ipc.py          Empalma series con cambio de canasta
│   │   └── 04_build_dataset_oficial.py  Construye el dataset consolidado
│   │
│   ├── 02_analisis_principal/         Paso 2: Análisis econométrico principal
│   │   └── 01_run_analysis_principal.py
│   │       Tests T1 (insesgamiento), T2 (Mincer-Zarnowitz),
│   │       T3 (persistencia), T4 (eficiencia informacional),
│   │       T5 (Coibion-Gorodnichenko), T6 (ARDL),
│   │       Diebold-Mariano, Bai-Perron y Quandt-Andrews
│   │
│   ├── 03_robustez/                   Paso 3: Análisis de robustez
│   │   ├── 01_run_analysis_robustez.py
│   │   ├── 02_run_analysis_robustez_suplementario.py
│   │   ├── 03_run_analysis_nivel2.py
│   │   └── 04_run_chow_lin.py
│   │
│   └── 04_visualizacion/              Paso 4: Generación de figuras
│       ├── 01_build_figures_initial.py
│       ├── 02_figuras_extra.py
│       └── 03_regenerate_figs.py
│
├── 03_resultados/                     Outputs intermedios y finales
│   ├── Dataset_Consolidado_BCRD.csv
│   ├── resultados_econometricos.json
│   ├── PIB_mensual_Chow_Lin.csv
│   └── Lambda_rolling_con_IC95.csv
│
├── 04_figuras/                        Las 7 figuras finales en PNG
│   ├── fig1_inflacion_expectativa.png
│   ├── fig2_mz_scatter.png
│   ├── fig3_cg_subperiodos.png
│   ├── fig4_lambda_rolling.png
│   ├── fig5_oos_comparacion.png
│   ├── fig6_bai_perron.png
│   └── fig7_sesgo_condicional.png
│
├── 05_paper/                          Documento
│   ├── Paper_Expectativas_Inflacion_RD.docx
│   └── build_paper.js                 Generador del .docx con node + librería docx
│
└── 06_documentacion/                  Documentación complementaria
    ├── GUIA_REPLICACION.md
    ├── METODOLOGIA_RESUMEN.md
    └── HISTORIAL_PEER_REVIEW.md
```

> **Nota sobre los datos**: cada archivo `.xlsx` del BCRD tiene un espejo en `.csv` (una hoja por archivo, o un CSV por hoja con sufijo `__NombreHoja.csv`). Esto permite que GitHub renderice las tablas directamente en el navegador y que las series sean diff-eables entre commits.

---

## Resumen del trabajo

Este paper evalúa la racionalidad y la rigidez informacional de las expectativas de inflación a doce meses del consenso de analistas de la Encuesta Mensual de Expectativas Macroeconómicas (EEM) del BCRD para el periodo junio 2010 – marzo 2026 (N = 190 observaciones).

**Hallazgo central**: el error de pronóstico del consenso es estadísticamente predecible a partir de la TPM rezagada. La TPM efectiva rezagada captura por sí sola un R² parcial de 0.383 sobre la varianza total del error, equivalente al 86% de la varianza explicada por el modelo completo de eficiencia informacional. El test conjunto de Wald rechaza la nula de ortogonalidad con χ²(4) = 21.68 (p < 0.001). El hallazgo es robusto a Bonferroni, Kiefer-Vogelsang, bootstrap por bloques, ARDL extendido y mensualización del PIB por Chow-Lin.

**Hipótesis unificadora**: el consenso EEM puede aproximarse, en primera instancia, como una constante cercana a la meta del banco central más un ruido pequeño. Esta caracterización reconcilia la sobrepredicción documentada por Jiménez P. y López H. (2014) en la muestra 2008–2013 con la subpredicción del periodo post-2020.

**Validación cuasi-experimental**: la indistinguibilidad estadística del consenso EEM respecto al ancla a la meta del 4% en el ejercicio fuera de muestra (RMSE 1.91 vs 1.75 pre-pandémico, 2.78 vs 2.81 post-pandémico) constituye un test directo del modelo y lo confirma.

---

## Cómo replicar el análisis desde cero

Los scripts están escritos con rutas portables. Funcionan desde cualquier máquina sin modificación, siempre que el árbol de directorios del paquete se mantenga intacto.

```bash
# Paso 1: Construir el dataset (lee de 01_data_raw/, escribe a 03_resultados/)
cd 02_scripts/01_construccion_dataset/
python 01_parse_ipc.py
python 02_parse_imae.py
python 03_empalme_ipc.py
python 04_build_dataset_oficial.py

# Paso 2: Análisis econométrico principal
cd ../02_analisis_principal/
python 01_run_analysis_principal.py

# Paso 3: Análisis de robustez
cd ../03_robustez/
python 01_run_analysis_robustez.py
python 02_run_analysis_robustez_suplementario.py
python 03_run_analysis_nivel2.py
python 04_run_chow_lin.py

# Paso 4: Generación de figuras
cd ../04_visualizacion/
python 01_build_figures_initial.py
python 02_figuras_extra.py
python 03_regenerate_figs.py

# Paso 5: Compilar el paper
cd ../../05_paper/
node build_paper.js
```

### Requerimientos técnicos

- **Python**: ≥ 3.10 con paquetes `pandas`, `numpy`, `statsmodels`, `scipy`, `matplotlib`
- **Node.js**: ≥ 18 con paquete `docx`
- **Datos**: archivos del BCRD ubicados en `01_data_raw/`

---

## Cómo está organizado el contenido del paper

El documento final consta de:

- **9 secciones principales**: Resumen, Introducción, Antecedentes, Datos, Metodología, Resultados centrales (T1-T6 + DM), Robustez (13 subsecciones), Discusión y Conclusiones
- **8 cuadros**: estadísticas descriptivas, raíces unitarias, pruebas de racionalidad, eficiencia informacional, Coibion-Gorodnichenko por subperíodo, Diebold-Mariano, diagnósticos MZ, descomposición R²
- **7 figuras**: inflación vs expectativa, scatter MZ, CG por subperíodo, lambda rodante con IC, OOS comparación, Bai-Perron, sesgo condicional
- **49 referencias bibliográficas**

---

## Sobre los datos

Todas las series provienen del Banco Central de la República Dominicana (BCRD):

- **EEM**: Encuesta Mensual de Expectativas Macroeconómicas, mediana del consenso a doce meses, junio 2010 a marzo 2026
- **IPC**: Índice de Precios al Consumidor, serie empalmada oficial, base octubre 2019 – septiembre 2020 = 100
- **TPM**: Tasa de Política Monetaria efectiva mensual
- **Tipo de cambio**: promedio mensual de cotizaciones de compra
- **PIB**: índice de volumen trimestral, mensualizado por Chow-Lin (1971) con IMAE como indicador
- **IMAE**: Índice Mensual de Actividad Económica, base 2018=100
- **IPM**: Informe de Política Monetaria diciembre 2025 (gráficos IV.12 y IV.14)

---

## Fuentes externas no incluidas en este repositorio

Por respeto a los derechos de autor de terceros, los siguientes documentos se citan pero no se redistribuyen aquí. Pueden descargarse directamente de las fuentes oficiales del BCRD:

1. **Banco Central de la República Dominicana (2025)**. *Informe de Política Monetaria — Diciembre 2025*. Santo Domingo: BCRD.
   Disponible en: <https://www.bancentral.gov.do/> (sección Publicaciones → Informe de Política Monetaria)
   Archivo referenciado en los scripts: `BCRD_IPM_diciembre_2025.pdf` (Gráficos IV.12 y IV.14)

2. **Jiménez P., F. y López H., A. (2014)**. *Racionalidad de las expectativas de inflación en República Dominicana: evidencia de la Encuesta Mensual de Expectativas Macroeconómicas, 2008–2013*. Serie de Estudios Económicos, Banco Central de la República Dominicana.
   Disponible en: <https://www.bancentral.gov.do/> (sección Publicaciones → Estudios Económicos)
   Archivo referenciado en los scripts: `Jimenez_Lopez_2014_BCRD.pdf`

Si los scripts requieren estos archivos como input, descárguelos de las fuentes anteriores y colóquelos manualmente en `01_data_raw/` con los nombres indicados.

---

## Licencias

Este repositorio se distribuye bajo dos licencias complementarias:

- **Código** (scripts Python en `02_scripts/`, `build_paper.js` en `05_paper/`): [MIT License](LICENSE)
- **Paper, datos derivados y documentación** (`01_data_raw/` con datos públicos del BCRD reorganizados, `03_resultados/`, `04_figuras/`, `05_paper/Paper_*.docx`, `06_documentacion/`, este `README.md`): [Creative Commons Attribution 4.0 International (CC BY 4.0)](LICENSE-DATA)

Los datos crudos del BCRD son de dominio público según la Ley 6-04 de la República Dominicana sobre acceso a información pública. Esta redistribución organizada se acoge a CC-BY-4.0 únicamente sobre el trabajo de curación, empalme y consolidación.

---

## Cómo citar este trabajo

```
Medina Tineo, C. E. (2026). Racionalidad y Rigidez Informacional de las Expectativas
de Inflación en República Dominicana. Paquete de replicación.
GitHub: https://github.com/RealCesarMedina/expectativas-inflacion-rd
```

---

## Contacto

César Emilio Medina Tineo
realcesarmedina@gmail.com
