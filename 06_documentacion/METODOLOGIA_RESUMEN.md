# Resumen metodológico

Esta nota técnica describe los métodos econométricos aplicados en el paper, con referencias específicas a las secciones del documento donde cada uno se implementa.

---

## 1. Pruebas estándar de racionalidad

### T1 — Insesgamiento (§6.2)

Especificación: `e_t = α + u_t`

Bajo la hipótesis nula de pronóstico insesgado, α = 0. Se reporta α con HAC Newey-West (bandwidth automático ≥ 11) sobre la muestra completa, pre-pandemia y post-pandemia. El rechazo en pre-pandemia (α = −1.32, p < 0.001) es la firma de sobrepredicción documentada por Jiménez-López (2014); el no-rechazo en muestra completa refleja compensación de sobrepredicción pre-pandémica con subpredicción post-pandémica.

### T2 — Mincer-Zarnowitz (§6.3)

Especificación: `π_t = α + β · E_{t−12}[π_t] + u_t`

Bajo racionalidad, conjuntamente α = 0 y β = 1. Se reporta el estadístico Wald con dos bandwidths de inferencia HAC: Newey-West automático y Hodrick (2h−1 = 23) apropiado para datos solapados con horizonte h = 12. El rechazo en post-pandemia bajo Hodrick (χ²(2) = 10.13, p = 0.006) es robusto; el no-rechazo bajo NW es artefacto del bandwidth.

### T3 — Persistencia del error (§6.5)

Especificación: `e_t = α + ρ · e_{t−12} + u_t`

Bajo racionalidad estricta, ρ = 0. La estimación produce ρ̂ = 0.190 con p = 0.213 (no rechaza), consistente con que el componente sistemático del error es bajo en magnitud aunque la asimetría estado-dependiente sí se rechaza.

### T4 — Eficiencia informacional (§6.4)

Especificación: `e_t = α + γ' · X_{t−13} + u_t` con `X = (π, TPM, Δe, Δy)`

Bajo eficiencia informacional, γ = 0 conjuntamente. **Este es el test que produce el hallazgo central del paper**: Wald χ²(4) = 21.68 (p < 0.001), con la TPM rezagada como predictor dominante (coeficiente = −1.25, R² parcial = 0.383). Las series usadas son oficiales del BCRD, no medianas reportadas por el panel EEM, para evitar circularidad informacional.

### T5 — Coibion-Gorodnichenko (§6.5)

Especificación: `e_t = α + λ · rev_t + u_t` donde `rev_t = E_t[π_{t+12}] − E_{t−1}[π_{t+12}]`

Bajo FIRE, λ = 0. Bajo rigidez à la Mankiw-Reis, λ > 0 con interpretación estructural ψ = 1/(1+λ) como probabilidad de actualización. La estimación produce λ post-pandemia = 1.187 (p < 0.001 bajo HAC NW) pero el bootstrap por bloques arroja IC 95% [−0.79, 2.09] (no rechaza al 5%). Esta sensibilidad inferencial es importante: el hallazgo CG es menos robusto que el hallazgo T4.

### T6 — ARDL extendido (§7.12)

Especificación: `e_t = α + Σ_{j=12}^{18} γ_j · TPM_{t-j} + ρ · π_{t-13} + δ · Δe_{t-13} + θ · Δy_{t-13} + u_t`

La nula H₀: γ_12 = γ_13 = ... = γ_18 = 0 se rechaza con Wald χ²(7) = 35.13 (p < 0.001), descartando que el rechazo de eficiencia dependa del rezago específico de la TPM elegido.

---

## 2. Cambio estructural

### Quandt-Andrews (§7.2)

Test supF de Quandt (1960) con valores críticos de Andrews (1993), con trimming del 10% en cada extremo. Detecta un quiebre endógeno con F máximo significativo al 1%.

### Chow exógeno en cambios metodológicos (§7.3)

Test Chow estándar en fechas exógenas correspondientes a rediseños documentados de la EEM (2014, 2017). El quiebre de 2017 produce F = 33.08 (p < 0.001), lo que confirma que la dicotomía pre/post-2017 documentada en el coeficiente CG bajo horizonte rodante coincide con el cambio metodológico de la encuesta y por tanto no permite separar limpiamente cambio de comportamiento económico de artefacto de medición.

### Bai-Perron (§7.7)

Procedimiento secuencial de Bai y Perron (1998) hasta m=5 quiebres. BIC monótonamente decreciente:

- m=0: BIC = 345.67
- m=1: BIC = 299.94 (añade 2020-07)
- m=2: BIC = 213.83 (añade 2023-02)
- m=3: BIC = 168.58 (añade 2012-02) — solución reportada en Figura 6
- m=4: BIC = 143.94 (añade 2017-01)
- m=5: BIC = 124.90 (añade 2018-11)

Trimming del 10%. El óptimo BIC global es m=5; se reporta m=3 por claridad visual con caveat explícito.

---

## 3. Evaluación predictiva fuera de muestra

### Diebold-Mariano (§6.6)

Test de Diebold-Mariano (1995) con corrección Harvey-Leybourne-Newbold (1997) para muestras pequeñas. Bandwidth h−1 = 11 sobre ventana OOS enero 2019 – marzo 2026 (N = 87).

Benchmarks:
- **Random walk a 12m**: π̂_t = π_{t−12}
- **AR(1) recursivo**: estimado con datos hasta t−12, predicción para t
- **Ancla a meta**: π̂_t = 4.0% constante

RMSE: EEM 2.72, RW 2.89, AR(1) 2.79, Ancla 2.72. DM no rechaza superioridad de ninguna especificación al 5%.

### Predicción ex ante condicional al subperíodo (§8.2.1)

Si "consenso ≈ meta + ruido" es la caracterización correcta, el ancla constante debe ser indistinguible del consenso EEM en ambos regímenes. Datos:

- Pre-pandémico (Ene 2018 – Feb 2020, N = 26, π promedio = 2.79%): RMSE consenso 1.91 vs ancla 1.75
- Post-pandémico (Mar 2020 – Mar 2026, N = 73, π promedio = 5.48%): RMSE consenso 2.78 vs ancla 2.81

Diferencia de orden de magnitud menor que la varianza muestral; predicción confirmada.

---

## 4. Robustez

### Bandwidth de Hodrick (§6.3, §A.3)

Para datos solapados con horizonte h = 12, Hodrick (1992) recomienda bandwidth 2h−1 = 23 en lugar del bandwidth automático Newey-West (que tiende a ser menor en muestras moderadas). Se reporta como verificación complementaria; en general endurece la inferencia.

### Bootstrap por bloques (§7.5)

Politis y Romano (1994) con b = 18 (cubre el horizonte h = 12 con margen), 5,000 réplicas. Apropiado para datos con autocorrelación de horizonte largo. Los IC 95% bootstrap son típicamente más anchos que los HAC, lo que es honesto frente a muestras finitas.

### Kiefer-Vogelsang (2005) (§7.5)

Teoría de muestra fija con b = 0.5 (bandwidth proporcional al tamaño de muestra). Produce valores críticos no estándar que reflejan la incertidumbre en la estimación de la matriz de covarianza misma. El rechazo del test T4 sobrevive bajo KV con holgura.

### Multiplicidad (§7.4)

Familia de 14 contrastes. Bonferroni define α = 0.05/14 ≈ 0.0036. Tres tests sobreviven al 5%: Chow 2017, eficiencia informacional T4, dicotomía CG. Tres adicionales sobreviven al 10%: sesgo pre-pandemia, MZ post-pandemia bajo Hodrick, λ post-pandemia. La cota 1 − 0.95^14 ≈ 51% es cota superior porque los contrastes comparten datos.

### Threshold-MZ con meta exógena (§7.11)

Especificación con la meta del 4% del BCRD como umbral exógeno (en lugar de la mediana muestral, que es endógena). Resultado: β_alto = 0.71, β_bajo = −0.06; ninguno rechaza β = 1 al 5% por baja potencia (N efectivo pequeño y σ(E) angosta dentro de cada régimen). Los puntos cualitativamente extraños son consistentes con el modelo "consenso ≈ meta + ruido".

### Mensualización del PIB por Chow-Lin (§7.13)

Chow y Lin (1971) con el IMAE como indicador relacionado, periodo común enero 2009 – diciembre 2025. ρ̂ ≈ 0 en el AR(1) de residuales mensuales. Re-estimación del test T4 con PIB-Chow-Lin: TPM coef cambia de −1.25 a −1.21, Wald χ²(4) cambia de 21.68 a 17.94 (ambos rechazan al 1%). Conclusión robusta.

---

## 5. Notación y convenciones

- **e_t**: error de pronóstico = π_t − E_{t−12}[π_t]
- **π_t**: inflación interanual realizada en t = (IPC_t / IPC_{t−12} − 1) × 100
- **E_{t−12}[π_t]**: expectativa formada en t−12 sobre la inflación a 12 meses
- **rev_t**: revisión del consenso entre encuestas consecutivas = E_t[π_{t+12}] − E_{t−1}[π_{t+12}]
- **TPM_t**: tasa de política monetaria efectiva mensual del BCRD
- **HAC**: heteroskedasticity- and autocorrelation-consistent (errores estándar)
- **N = 190**: tamaño muestral total con datos completos (junio 2010 – marzo 2026)
- **N pre = 117**: junio 2010 – febrero 2020
- **N post = 73**: marzo 2020 – marzo 2026

---

## 6. Limitaciones reconocidas

1. **Disagreement vs rigidez**: usar la mediana del consenso impide separar rigidez agente-individual de heterogeneidad; requiere datos de panel.
2. **Identificación causal**: el rechazo del test de eficiencia es predictivo, no estructural.
3. **Saliencia vs rigidez cognitiva**: identificacionalmente equivalentes con datos agregados.
4. **N post pequeño**: 73 observaciones reducen la potencia.
5. **Threshold-MZ baja potencia**: el no-rechazo no es evidencia de FIRE.
6. **Curva de Phillips ausente**: implicaciones de potencia de política fuera de alcance.
7. **Horizonte rodante**: la EEM es de objetivo rodante, no fijo; la interpretación ψ = 1/(1+λ) es estricta solo bajo objetivo fijo.
8. **Pass-through del tipo de cambio**: especificación con un único Δe_{t-13} puede ser inadecuada.

Items deferidos legítimamente por requerir trabajo sustantivo adicional:
- DM con Giacomini-White
- Hansen (2000) umbral endógeno
- Horizonte fijo decreciente con microdatos individuales
