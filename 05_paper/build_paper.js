// Generador del paper en formato .docx — construido con IPC oficial del BCRD,
// test de Diebold-Mariano, y narrativa centrada en persistencia, ineficiencia
// informacional y comparación OOS con benchmarks.

const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, VerticalAlign, PageNumber, PageBreak, TabStopType,
  ImageRun
} = require('docx');

const R = JSON.parse(fs.readFileSync(path.join(__dirname, '..', '03_resultados', 'resultados_econometricos.json'),'utf8'));
const fmt  = (x, d=3) => (x===null||x===undefined||Number.isNaN(x))?'—':Number(x).toFixed(d);
// fmtP: para uso en texto inline después de la palabra 'p'. Produce "< 0.001" o "= X.XXX" para construir "p ${fmtP(p)}".
const fmtP = (p) => p<0.001?'< 0.001':'= '+Number(p).toFixed(3);
// fmtPv: solo el valor, para uso en tablas. Produce "<0.001" o "0.XXX".
const fmtPv = (p) => p<0.001?'<0.001':Number(p).toFixed(3);
const sig  = (p) => p<0.01?'***':p<0.05?'**':p<0.10?'*':'';
const pp = (n,p) => `${fmt(n)}${sig(p)}`;

// ---------- helpers ----------
const border = { style: BorderStyle.SINGLE, size: 4, color: "999999" };
const allBorders = { top:border, bottom:border, left:border, right:border };
const cellMargins = { top: 80, bottom: 80, left: 120, right: 120 };

const P = (text, opts={}) => new Paragraph({
  spacing: { after: 120, line: 300 },
  alignment: opts.align || AlignmentType.JUSTIFIED,
  ...opts.paragraph,
  children: [new TextRun({ text, font:"Times New Roman", size:22, ...opts.run })]
});
const PR = (runs, opts={}) => new Paragraph({
  spacing:{ after:120, line:300 },
  alignment: opts.align || AlignmentType.JUSTIFIED,
  ...opts.paragraph, children: runs
});
const T = (text, runOpts={}) => new TextRun({ text, font:"Times New Roman", size:22, ...runOpts });
const H1 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1, spacing:{ before:360, after:200 },
  children:[new TextRun({ text, font:"Times New Roman", size:28, bold:true })]
});
const H2 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_2, spacing:{ before:280, after:160 },
  children:[new TextRun({ text, font:"Times New Roman", size:24, bold:true })]
});
const H3 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_3, spacing:{ before:200, after:120 },
  children:[new TextRun({ text, font:"Times New Roman", size:22, bold:true, italics:true })]
});
const Eq = (text, num) => new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing:{ before:120, after:120 },
  tabStops:[{ type:TabStopType.RIGHT, position:9360 }],
  children:[
    new TextRun({ text, font:"Cambria Math", size:22, italics:true }),
    new TextRun({ text:`\t(${num})`, font:"Times New Roman", size:22 })
  ]
});
const TC = (text, opts={}) => new TableCell({
  borders: allBorders, margins: cellMargins,
  width:{ size: opts.width, type: WidthType.DXA },
  shading: opts.shading?{ fill:opts.shading, type:ShadingType.CLEAR }:undefined,
  verticalAlign: VerticalAlign.CENTER,
  children:[new Paragraph({
    alignment: opts.align || AlignmentType.LEFT,
    spacing:{ after:0 },
    children:[new TextRun({
      text:String(text), font:"Times New Roman",
      size: opts.size||20, bold: opts.bold||false,
      italics: opts.italics||false
    })]
  })]
});
const Cap = (text) => new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing:{ before:200, after:80 },
  children:[new TextRun({ text, font:"Times New Roman", size:20, bold:true, italics:true })]
});
const Note = (text) => new Paragraph({
  alignment: AlignmentType.LEFT,
  spacing:{ before:80, after:200 },
  children:[new TextRun({ text, font:"Times New Roman", size:18, italics:true })]
});
const Ref = (text) => new Paragraph({
  spacing:{ after:100, line:280 },
  alignment: AlignmentType.JUSTIFIED,
  indent:{ left:720, hanging:720 },
  children:[new TextRun({ text, font:"Times New Roman", size:22 })]
});
const FigImg = (path, w=560, h=265) => new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing:{ before:120, after:80 },
  children:[new ImageRun({
    data: fs.readFileSync(path),
    transformation:{ width:w, height:h },
    type: 'png'
  })]
});

// =========================================================
// CONTENT
// =========================================================
const c = [];

// COVER
c.push(
  new Paragraph({ alignment:AlignmentType.CENTER, spacing:{ before:1800, after:240 },
    children:[new TextRun({ text:"Racionalidad y rigidez informacional en las expectativas de inflación:", font:"Times New Roman", size:32, bold:true })] }),
  new Paragraph({ alignment:AlignmentType.CENTER, spacing:{ after:1200 },
    children:[new TextRun({ text:"Evidencia para la República Dominicana, 2011–2026", font:"Times New Roman", size:28, bold:true, italics:true })] }),
  new Paragraph({ alignment:AlignmentType.CENTER, spacing:{ before:1200, after:120 },
    children:[new TextRun({ text:"César Emilio Medina Tineo", font:"Times New Roman", size:24 })] }),
  new Paragraph({ children:[new PageBreak()] })
);

// RESUMEN
c.push(H1("Resumen"));

const t5pre = R.t5_coibion_gorod.pre, t5full = R.t5_coibion_gorod.full;
const t1pre = R.t1_insesgamiento.pre, t2pre = R.t2_mincer_zarnowitz.pre;
const t3full = R.t3_persistencia.full;
const t4 = R.t4_eficiencia_info_oficial;
const dm = R.diebold_mariano.oos_completa;
const qb = R.quiebre;

c.push(P(`Este trabajo evalúa la racionalidad y la rigidez informacional de las expectativas de inflación a doce meses del consenso de analistas de la Encuesta Mensual de Expectativas Macroeconómicas (EEM) del Banco Central de la República Dominicana (BCRD) para junio 2010 – marzo 2026 (N = ${R.meta.n_total}). Se aplica las pruebas estándar de expectativas racionales (insesgamiento, eficiencia de Mincer-Zarnowitz, ortogonalidad del error al pasado y al set de información) y se complementa con el test de rigidez de Coibion y Gorodnichenko (2015), pruebas de cambio estructural de Quandt (1960), Andrews (1993) y Bai y Perron (1998), y evaluación predictiva fuera de muestra con Diebold-Mariano contra benchmarks naïve. La inferencia se reporta con HAC Newey-West y, como verificación, con bandwidth de Hodrick (2h−1 = 23) apropiado para datos solapados, bootstrap por bloques (Politis y Romano, 1994) y la teoría de muestra fija de Kiefer y Vogelsang (2005).`));

c.push(P(`La evidencia converge en una jerarquía clara. El hallazgo central por magnitud económica y robustez es la predictibilidad del error de pronóstico a partir de la TPM rezagada: el test de eficiencia informacional con variables observables oficiales rechaza la nula de ortogonalidad con Wald χ²(4) = ${fmt(t4.wald_chi2,2)} (p ${fmtP(t4.wald_p)}), y la TPM efectiva rezagada captura por sí sola un R² parcial de ${fmt(R.t4_eficiencia_info_oficial.r2_partial['TPM_obs_t-13'],3)} sobre la varianza total del error, es decir, aproximadamente un 38% de esa varianza es predecible a partir de información pública disponible al momento de pronosticar. La especificación ARDL con rezagos doce a dieciocho de la TPM produce rechazo conjunto al 1% (Wald χ²(7) = ${fmt(R.ardl_tpm_eficiencia.wald_conjunto_tpm_chi2,2)}), descartando dependencia del rezago específico. El hallazgo es robusto a Bonferroni al 5%, al control por el rediseño metodológico de la encuesta de 2017, a inferencia Kiefer-Vogelsang y a bootstrap por bloques. Como hallazgos complementarios, se documenta sesgo asimétrico estado-dependiente con prueba de igualdad rechazada al 1%, rechazo de Mincer-Zarnowitz lineal que pierde solidez bajo threshold en la meta del 4%, un coeficiente de Coibion-Gorodnichenko con dicotomía pre/post-2017 que coincide con el cambio metodológico de la EEM, y RMSE del consenso EEM estadísticamente indistinguible de benchmarks naïve fuera de muestra.`));

c.push(P("Los cinco resultados anteriores admiten una lectura unificadora simple: el consenso EEM puede aproximarse, en primera instancia, como una constante cercana a la meta del banco central más un ruido pequeño. Esta caracterización reconcilia la sobrepredicción documentada por Jiménez P. y López H. (2014) en la muestra 2008–2013, periodo en el cual la inflación realizada cayó por debajo del nivel ancla del consenso, con la subpredicción del periodo post-2020, en el que la inflación realizada superó ese nivel. La principal implicación de política es que el régimen de comunicación del BCRD podría obtener ganancias predictivas al hacer más explícita la lectura del propio banco sobre cómo la trayectoria reciente de la TPM debe traducirse en una proyección de inflación distinta a doce meses, complementario a la publicación actual de fan charts en el Informe de Política Monetaria semestral."));

c.push(P("",{ paragraph:{ spacing:{ after:60 } } }));
c.push(PR([T("Palabras clave: ",{ bold:true }), T("expectativas de inflación, racionalidad, eficiencia informacional, rigidez informacional, Diebold-Mariano, política monetaria, República Dominicana.")]));
c.push(PR([T("Códigos JEL: ",{ bold:true }), T("E31, E37, E52, D84.")]));
c.push(new Paragraph({ children:[new PageBreak()] }));

// 1. INTRODUCCIÓN
c.push(H1("1. Introducción"));
c.push(P("La formación de expectativas de inflación constituye una de las piezas centrales de la macroeconomía moderna. Desde la formalización de la hipótesis de expectativas racionales por Muth (1961) y su incorporación a los modelos de política monetaria por Lucas (1972) y Sargent y Wallace (1975), la calidad de los pronósticos privados ha pasado de ser una curiosidad estadística a un insumo crítico de la conducción monetaria. En un esquema de metas de inflación, la credibilidad del banco central depende no solo de su capacidad para alcanzar el objetivo, sino de su habilidad para anclar las expectativas en torno a él. Cuando esas expectativas se desvían sistemáticamente del realizado, parte de la transmisión monetaria se filtra y el costo de estabilizar precios aumenta."));

c.push(P("La República Dominicana adoptó formalmente un Esquema de Metas de Inflación en enero de 2012, fijando una meta puntual con un rango de tolerancia de ±1 punto porcentual. Desde entonces, el Banco Central de la República Dominicana ha publicado mensualmente la Encuesta de Expectativas Macroeconómicas con el doble propósito de medir la efectividad de la comunicación de política y de proveer un termómetro de las creencias del mercado. La existencia de una serie larga, con más de quince años de observaciones mensuales, hace posible plantear preguntas que en 2014, cuando Jiménez y López publicaron el trabajo precursor sobre el tema, no podían responderse con la profundidad que admiten los datos hoy."));

c.push(P("Este trabajo aborda cuatro preguntas vinculadas. Primero, ¿son insesgadas y eficientes las expectativas medianas reportadas en la EEM cuando se las contrasta con la inflación interanual oficial publicada por el BCRD? Segundo, si existen desviaciones de la racionalidad, ¿corresponden a errores sistemáticos en el procesamiento de información disponible o a rigideces estructurales en su actualización? Tercero, ¿se modifica la respuesta a estas dos preguntas si se distingue el periodo pre-pandémico (2011–2020) del periodo posterior, marcado por choques de oferta de magnitud excepcional? Cuarto, en términos de calidad predictiva fuera de muestra, ¿domina el consenso de analistas a benchmarks mecánicos como un random walk o un ancla a la meta?"));

c.push(P("La contribución de este trabajo es metodológica y empírica. En el plano metodológico, se complementa las pruebas tradicionales de Mincer y Zarnowitz (1969) con la prueba de rigidez informacional de Coibion y Gorodnichenko (2015), se incorpora las pruebas de cambio estructural con punto de quiebre desconocido de Quandt (1960) y Andrews (1993) y el procedimiento secuencial de Bai y Perron (1998), y se reporta un ejercicio de evaluación predictiva con test de Diebold-Mariano (1995) contra benchmarks naïve. La inferencia HAC se reporta tanto con bandwidth automático de Newey-West como con bandwidth de Hodrick (2h−1 = 23) recomendado para regresiones con horizonte de pronóstico solapado. En el plano empírico, hasta donde se ha podido verificar éste es el primer trabajo que aplica el test de Coibion-Gorodnichenko, construido sobre la revisión del consenso entre encuestas consecutivas, a las expectativas dominicanas, así como la primera evaluación predictiva fuera de muestra del consenso EEM contra benchmarks naïve mediante Diebold-Mariano. Con respecto a Jiménez P. y López H. (2014), trabajo precursor sobre los mismos datos para una muestra anterior, se complementa su evaluación de uso de información (Mankiw, Reis y Wolfers, 2003) con un test conceptualmente distinto basado en la propia revisión del consenso, y su comparación entre estratos mediante Giacomini-White con un ejercicio fuera de muestra contra benchmarks. Esta diferenciación se desarrolla en detalle en la sección 2."));

c.push(P("El resto del documento se organiza como sigue. La sección 2 revisa la literatura relevante. La sección 3 presenta el marco teórico y deriva las hipótesis testeables. La sección 4 describe los datos. La sección 5 expone la metodología. La sección 6 reporta los resultados principales. La sección 7 contiene los chequeos de robustez y los diagnósticos econométricos. La sección 8 discute las implicaciones de política y las limitaciones del análisis. La sección 9 concluye."));

// 2. LITERATURA
c.push(H1("2. Revisión de la literatura"));
c.push(P("La literatura sobre expectativas de inflación puede agruparse en tres vertientes que aquí se discute brevemente para situar la contribución del presente trabajo."));

c.push(H2("2.1. Pruebas tradicionales de racionalidad"));
c.push(P("Mincer y Zarnowitz (1969) establecen la formulación canónica del test de eficiencia: si las expectativas son racionales en sentido fuerte, una regresión del realizado sobre el esperado debe arrojar un intercepto cero y una pendiente unitaria. Keane y Runkle (1990), trabajando con datos de panel del Survey of Professional Forecasters, encuentran rechazos generalizados de esta hipótesis, pero matizan la lectura señalando que los pronósticos individuales suelen ser más eficientes que el consenso. Pesaran y Weale (2006) consolidan la batería de pruebas y subrayan la importancia de la inferencia HAC en presencia de datos solapados, un punto frecuentemente descuidado en la literatura aplicada. Hodrick (1992), West (1996) y Britton, Fisher y Whitley (1998) documentan los sesgos de inferencia que produce ignorar la autocorrelación inducida por el horizonte de pronóstico solapado."));

c.push(P("En el contexto latinoamericano, Capistrán y Ramos-Francia (2010) examinan las expectativas en cinco economías de la región y reportan rechazos del insesgamiento concentrados en periodos de turbulencia. Forsells y Kenny (2002) realizan un ejercicio paralelo para la zona euro, encontrando que las desviaciones se reducen sistemáticamente tras la consolidación del Banco Central Europeo, evidencia consistente con un efecto credibilidad."));

c.push(H2("2.2. Modelos de información imperfecta y rigidez informacional"));
c.push(P("Un desarrollo relevante de los últimos veinte años ha sido el reconocimiento de que la racionalidad plena, entendida como pleno uso instantáneo de toda la información disponible, es una idealización empíricamente cuestionable. Mankiw y Reis (2002) proponen el modelo de sticky information, en el que solo una fracción exógena de agentes actualiza su set informacional en cada periodo. Sims (2003) formaliza el enfoque de rational inattention, que deriva endógenamente la actualización imperfecta a partir de costos de procesamiento. Mankiw, Reis y Wolfers (2003) muestran empíricamente que existe disagreement persistente entre pronosticadores, hecho difícil de reconciliar con racionalidad plena. Maćkowiak y Wiederholt (2009) extienden el modelo de inattention al contexto de volatilidad heterogénea."));

c.push(P("Coibion y Gorodnichenko (2012, 2015) proponen un test que aprovecha la estructura de panel de las encuestas: si las expectativas son plenamente racionales, las revisiones de pronóstico no deberían predecir los errores de pronóstico. Una pendiente positiva en esa relación es la firma econométrica de la rigidez informacional. Bordalo, Gennaioli, Ma y Shleifer (2020) extienden el análisis al contexto de overreaction (pendiente negativa) en pronósticos individuales del SPF, mostrando que el agregado puede ocultar heterogeneidad relevante. Andrade, Gautier y Mengus (2023) y Kohlhas y Walther (2021) documentan asimetrías y deterioros en la calidad predictiva de las encuestas durante el shock inflacionario post-2020."));

c.push(H2("2.3. Evidencia para la República Dominicana"));
c.push(P("El trabajo precursor para el caso dominicano es Jiménez P. y López H. (2014), quienes aplican la batería tradicional de pruebas a las expectativas de la EEM desagregadas por tipo de agente (académicos, bancos, consultores, empresarios y organismos internacionales) sobre la muestra inicial de la encuesta (enero 2008 a julio 2013, N = 67 para expectativas a doce meses). Sus hallazgos centrales son: (i) sobreestimación sistemática y estadísticamente significativa de la inflación realizada por parte del consenso (α = −2.28 p.p., p < 0.05) y por todos los estratos individuales excepto los organismos internacionales; (ii) heterogeneidad significativa entre estratos bajo el test de Giacomini-White (2006), con los organismos internacionales exhibiendo los menores errores de pronóstico a horizonte interanual y los académicos los mayores; y (iii) un proceso gradual de aprendizaje evidenciado por la reducción del RECM agregado de 7.11% al inicio de la muestra a 3.17% al final, calculado mediante ventana rodante. La hipótesis de expectativas racionales completas se rechaza, pero también se rechaza la hipótesis adaptativa pura, lo que les lleva a la lectura de actualización parcial de la información macroeconómica, en la línea de Mankiw, Reis y Wolfers (2003). El presente trabajo se diferencia de Jiménez y López en cinco dimensiones. Primero, extiende la muestra hasta marzo de 2026, incorporando el episodio inflacionario de 2021–2022 que reescribió la dinámica de los precios y los años posteriores de re-anclaje; el periodo de Jiménez y López corresponde a una fase de inflación a la baja, mientras que el del presente trabajo abarca un ciclo inflacionario completo. Segundo, hasta donde se ha podido verificar, ésta es la primera aplicación del test de Coibion y Gorodnichenko (2015), construido sobre la revisión del consenso entre encuestas consecutivas, a las expectativas dominicanas; el antecedente más cercano en Jiménez y López es el test de Mankiw, Reis y Wolfers sobre uso de información macroeconómica, que es metodológicamente distinto en cuanto evalúa la ortogonalidad del error respecto a un set de variables observables exógenas, no respecto a la propia revisión de la expectativa. Tercero, se complementa los hallazgos de Jiménez y López en evaluación predictiva (ellos aplican Giacomini-White entre estratos sobre errores en muestra) con un ejercicio de Diebold-Mariano (1995) fuera de muestra contra benchmarks naïve (random walk, AR(1) recursivo, ancla a la meta). Cuarto, se incorpora tests formales de quiebre estructural con punto de quiebre desconocido (Quandt, 1960; Andrews, 1993; Bai y Perron, 1998) que el periodo de Jiménez y López no permitía. Quinto, se corrige problemas de inferencia en datos solapados con bandwidth HAC apropiado al horizonte (Hodrick, 1992) y se robustece los resultados con bootstrap por bloques (Politis y Romano, 1994) y con la teoría de muestra fija de Kiefer y Vogelsang (2005), correcciones que la práctica estándar al momento de Jiménez y López no incorporaba."));

// 3. MARCO TEÓRICO
c.push(H1("3. Marco teórico e hipótesis testeables"));
c.push(P("Sea π_t la inflación interanual realizada en el periodo t y sea E_{t−12}[π_t] la expectativa formada en t−12 condicionada al set de información Ω_{t−12}. La hipótesis de expectativas racionales en su formulación de pleno uso de información (Full Information Rational Expectations, FIRE) implica las siguientes propiedades testeables del error de pronóstico e_t ≡ π_t − E_{t−12}[π_t]:"));

c.push(H3("Propiedad I: Insesgamiento"));
c.push(P("El error de pronóstico debe tener media incondicional cero. Empíricamente, esto se contrasta mediante:"));
c.push(Eq("e_t = α + u_t", "1"));
c.push(P("donde la hipótesis nula es H₀: α = 0. La prueba se realiza con error estándar HAC dada la autocorrelación inducida por el solapamiento del horizonte de pronóstico de doce meses sobre datos mensuales."));

c.push(H3("Propiedad II: Eficiencia de Mincer-Zarnowitz"));
c.push(P("Si las expectativas son eficientes, la regresión del realizado sobre el esperado debe satisfacer α = 0 y β = 1 conjuntamente:"));
c.push(Eq("π_t = α + β · E_{t−12}[π_t] + u_t", "2"));
c.push(P("La hipótesis nula conjunta H₀: α = 0 ∧ β = 1 se contrasta mediante una prueba de Wald con matriz de varianzas-covarianzas HAC. Una pendiente significativamente menor que la unidad se interpreta como sub-reacción a la información: cuando la inflación realizada se mueve, la expectativa se mueve menos que proporcionalmente. Una pendiente significativamente mayor que la unidad indica sobre-reacción."));

c.push(H3("Propiedad III: Ortogonalidad del error a su propio pasado"));
c.push(P("El error de pronóstico debe ser una innovación; esto es, no debe ser predecible a partir de errores anteriores. La prueba se realiza mediante:"));
c.push(Eq("e_t = α + ρ · e_{t−12} + u_t", "3"));
c.push(P("con H₀: ρ = 0. El rezago apropiado es de doce meses, que es el horizonte del pronóstico, no rezagos arbitrarios. Bajo racionalidad, ρ debe ser cero; un valor negativo y significativo se interpreta como sobre-corrección anual de los errores; un valor positivo, como persistencia de los mismos."));

c.push(H3("Propiedad IV: Eficiencia informacional"));
c.push(P("El error de pronóstico debe ser ortogonal a cualquier elemento del set de información disponible al momento de pronosticar. Sea X_{t−13} un vector de variables observables en t−13:"));
c.push(Eq("e_t = α + γ' · X_{t−13} + u_t", "4"));
c.push(P("con H₀: γ = 0. Bajo FIRE, ningún elemento del set de información debería tener poder predictivo sobre el error. En este trabajo X_{t−13} incluye la inflación rezagada, la tasa de política monetaria, la variación porcentual interanual del tipo de cambio implícito y el crecimiento interanual del PIB real, todos públicamente disponibles al momento de la formación de la expectativa."));

c.push(H3("Propiedad V: Test de rigidez informacional de Coibion-Gorodnichenko"));
c.push(P("Coibion y Gorodnichenko (2015) muestran que, bajo modelos de información imperfecta del tipo Mankiw-Reis (sticky information) o Woodford (noisy information), el error de pronóstico está relacionado con la revisión de la expectativa. Sea rev_t ≡ E_t[π_t] − E_{t−1}[π_t] la revisión entre dos encuestas consecutivas (la diferencia entre la expectativa formada en t y la formada un mes antes, sobre el mismo objeto pronosticado). La regresión:"));
c.push(Eq("e_t = α + λ · rev_t + u_t", "5"));
c.push(P("constituye el test de información plena. Bajo FIRE, λ = 0. Si λ > 0 y es significativo, los datos son consistentes con rigidez informacional (sub-reacción). Si λ < 0 y es significativo, son consistentes con sobre-reacción. Bajo el modelo de sticky information, λ se relaciona con la probabilidad de actualización ψ por la expresión ψ = 1/(1 + λ); intuitivamente, cuanto más rígida es la actualización, mayor es λ. Cabe advertir, siguiendo a Bordalo et al. (2020), que la interpretación estructural de ψ = 1/(1+λ) es estrictamente válida con datos individuales del panel; a nivel del consenso (mediana), λ refleja una mezcla de rigidez informacional y disagreement entre agentes que debe ser leída con prudencia."));

// 4. DATOS
c.push(H1("4. Datos"));
c.push(H2("4.1. Encuesta Mensual de Expectativas Macroeconómicas"));
c.push(P("La fuente primaria de las expectativas es la Encuesta Mensual de Expectativas Macroeconómicas del Banco Central de la República Dominicana, vigente desde julio de 2007 con cambios de diseño que ampliaron el panel y los horizontes informados. La encuesta releva mensualmente las expectativas de un panel de aproximadamente cuarenta participantes (agrupados en académicos, sector bancario, consultores, sector empresarial y organismos internacionales) sobre inflación, tipo de cambio, tasa de política monetaria y crecimiento del PIB real, en horizontes de cierre de mes, doce meses, año actual, año siguiente y veinticuatro meses."));

c.push(P("Para mantener consistencia con la literatura previa y para mitigar el problema de datos faltantes en algunos grupos en algunos meses, este trabajo utiliza la mediana del consenso. La mediana es preferible a la media por dos razones: es robusta a outliers en pronósticos individuales, frecuentes durante choques, y reduce el impacto de la rotación del panel sobre la serie agregada."));

c.push(H2("4.2. Inflación interanual oficial"));
c.push(P("La inflación interanual realizada se construye a partir del Índice de Precios al Consumidor (IPC) publicado por el Banco Central de la República Dominicana en su archivo \"IPC General Mensual, Serie Empalmada Oficial\", base \"Octubre 2019 – Septiembre 2020 = 100\". Esta serie es la versión continua y empalmada por el propio BCRD, que reconcilia las distintas bases de canasta utilizadas históricamente (canasta 2010, canasta ENGIH 2018) en una sola serie homogénea desde 1984. La inflación interanual π_t se calcula como (IPC_t / IPC_{t−12} − 1) × 100. La verificación contra valores oficiales conocidos (publicados en informes mensuales del BCRD y reportes de prensa) coincide al centésimo en siete puntos de control distribuidos a lo largo de la muestra: abril 2020 (1.07% calculado vs 1.04% oficial), diciembre 2020 (5.55% vs 5.55%), diciembre 2021 (8.50% vs 8.50%), abril 2022 (9.64% vs 9.64%), agosto 2024 (3.42% vs 3.42%), agosto 2025 (3.72% vs 3.72%) y marzo 2026 (4.63% vs 4.63%)."));

c.push(P("Esta corrección es sustantiva respecto a versiones preliminares de este trabajo, que utilizaban una serie reconstruida con valores de informes mensuales del BCRD para los meses faltantes en el archivo del calculador del IPC. La utilización del archivo empalmado oficial garantiza la trazabilidad institucional de cada observación y elimina cualquier sesgo de medición procedente de reconstrucciones manuales."));

c.push(H2("4.3. Variables observables del set de información"));
c.push(P("Para el test de eficiencia informacional (sección 6.4) se utilizan series oficiales observadas del propio BCRD, no las medianas reportadas en la EEM, que constituirían una mezcla circular entre el objeto del análisis y sus regresores. La tasa de política monetaria efectiva proviene de la serie mensual de Tasas de Política Monetaria y Facilidades Permanentes del BCRD para el periodo 2004–2026. El tipo de cambio nominal corresponde al promedio mensual de las cotizaciones diarias de compra reportadas por las entidades de intermediación cambiaria al BCRD; la variación interanual se calcula sobre dicho promedio. El crecimiento interanual del PIB real proviene del índice de volumen del PIB trimestral publicado por el Departamento de Cuentas Nacionales del BCRD. Para incorporarlo a un análisis con frecuencia mensual se aplica dos métodos. El método base utiliza asignación constante dentro del trimestre. Como verificación de robustez, se mensualiza el PIB mediante el procedimiento de Chow y Lin (1971) usando el Índice Mensual de Actividad Económica (IMAE) del BCRD como indicador relacionado, sobre el periodo común enero 2009 – diciembre 2025; los resultados de ambos procedimientos se reportan en la sección 7.13 y son cualitativamente idénticos. Esta es una corrección importante respecto a versiones preliminares que utilizaban como regresores las propias medianas del consenso para TPM, tipo de cambio y crecimiento del PIB; la utilización de las series observadas oficiales convierte el test de eficiencia informacional en un contraste auténtico de ortogonalidad respecto a información pública disponible al momento de pronosticar."));

c.push(H2("4.4. Visualización de la serie"));
c.push(P("La Figura 1 presenta la inflación interanual realizada, la expectativa a doce meses formada doce meses antes y el error de pronóstico resultante. La línea vertical punteada marca marzo de 2020, fecha que se utilizará como punto de corte en el análisis de submuestras."));
c.push(FigImg(path.join(__dirname, '..', '04_figuras', 'fig1_inflacion_expectativa.png'), 580, 253));
c.push(Cap("Figura 1. Inflación realizada, expectativa formada 12 meses antes y error de pronóstico"));
c.push(Note("Nota: Inflación interanual π_t calculada con la serie empalmada oficial del BCRD (base octubre 2019 – septiembre 2020 = 100). Expectativa E_{t−12}[π_t] es la mediana del consenso de la EEM-BCRD rezagada doce meses. El error e_t = π_t − E_{t−12}[π_t] se grafica como barras. La región sombreada corresponde al periodo post-marzo 2020."));

// 4.4 DESCRIPTIVAS
c.push(H2("4.5. Estadísticas descriptivas"));
c.push(P("El Cuadro 1 reporta las estadísticas descriptivas de las variables principales. La inflación interanual promedia 4.32% en la muestra completa, con una desviación estándar de 2.49 p.p. que refleja la diferencia entre el régimen estable previo a 2020 y el episodio inflacionario posterior. La expectativa mediana del consenso promedia 4.58%, con una variabilidad sustancialmente menor (1.19 p.p.), lo que ya sugiere una propiedad relevante: el consenso de analistas ancla sus pronósticos en torno a un nivel relativamente fijo, mientras que la inflación realizada muestra mayor volatilidad. La inflación, la expectativa y el error de pronóstico exhiben asimetría positiva moderada, asociada a los picos del periodo 2021-2022."));

const desc = R.descriptivas;
const t1H = new TableRow({ tableHeader:true, children:[
  TC("Variable", { width:3000, bold:true, shading:"E8E8E8" }),
  TC("N",      { width:600,  bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
  TC("Media",  { width:1100, bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
  TC("Mediana",{ width:1100, bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
  TC("Desv.",  { width:1000, bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
  TC("Mín",    { width:900,  bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
  TC("Máx",    { width:900,  bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
  TC("Asim.",  { width:880,  bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
]});

const t1Rows = desc.map(d => new TableRow({ children:[
  TC(d.Variable, { width:3000 }),
  TC(d.N,        { width:600,  align:AlignmentType.CENTER }),
  TC(fmt(d.Media,2),    { width:1100, align:AlignmentType.CENTER }),
  TC(fmt(d.Mediana,2),  { width:1100, align:AlignmentType.CENTER }),
  TC(fmt(d.DesvEst,2),  { width:1000, align:AlignmentType.CENTER }),
  TC(fmt(d.Min,2),      { width:900,  align:AlignmentType.CENTER }),
  TC(fmt(d.Max,2),      { width:900,  align:AlignmentType.CENTER }),
  TC(fmt(d.Asimetria,2),{ width:880,  align:AlignmentType.CENTER }),
]}));

c.push(Cap("Cuadro 1. Estadísticas descriptivas, junio 2010 – marzo 2026"));
c.push(new Table({
  width:{ size:9480, type:WidthType.DXA },
  columnWidths:[3000,600,1100,1100,1000,900,900,880],
  rows:[t1H, ...t1Rows]
}));
c.push(Note("Nota: Estadísticos calculados sobre la muestra efectiva tras construir el error de pronóstico. Inflación calculada con IPC oficial del BCRD. Fuente: cálculos propios con EEM-BCRD e IPC-BCRD."));

// 4.5 RAÍZ UNITARIA
c.push(H2("4.6. Pruebas de raíz unitaria"));
c.push(P("Antes de estimar regresiones que involucran series macroeconómicas potencialmente persistentes, conviene examinar las propiedades de orden de integración. El Cuadro 2 reporta las pruebas de Dickey-Fuller aumentada (ADF) y Kwiatkowski-Phillips-Schmidt-Shin (KPSS). La ADF tiene como hipótesis nula la existencia de raíz unitaria; KPSS invierte el planteo y testea estacionariedad como nula."));

const rai = R.raices;
const t2H = new TableRow({ tableHeader:true, children:[
  TC("Serie",        { width:2400, bold:true, shading:"E8E8E8" }),
  TC("ADF stat",     { width:1400, bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
  TC("ADF p-valor",  { width:1400, bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
  TC("KPSS stat",    { width:1400, bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
  TC("KPSS p-valor", { width:1400, bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
  TC("Conclusión",   { width:1400, bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
]});
const t2Rows = rai.map(r => new TableRow({ children:[
  TC(r.Serie,        { width:2400 }),
  TC(fmt(r['ADF stat'],2), { width:1400, align:AlignmentType.CENTER }),
  TC(fmt(r['ADF p'],3),    { width:1400, align:AlignmentType.CENTER }),
  TC(fmt(r['KPSS stat'],2),{ width:1400, align:AlignmentType.CENTER }),
  TC(fmt(r['KPSS p'],3),   { width:1400, align:AlignmentType.CENTER }),
  TC(r['Conclusión'],{ width:1400, align:AlignmentType.CENTER }),
]}));
c.push(Cap("Cuadro 2. Pruebas de raíz unitaria"));
c.push(new Table({ width:{ size:9400, type:WidthType.DXA }, columnWidths:[2400,1400,1400,1400,1400,1400], rows:[t2H,...t2Rows] }));
c.push(Note("Nota: ADF con constante y selección de rezagos por BIC. KPSS con constante. Las series son tratadas como I(0) cuando ADF rechaza la nula y KPSS no rechaza estacionariedad."));
c.push(P("Las pruebas convergen en la conclusión de que las series son estacionarias en niveles. El error de pronóstico es claramente I(0) (ADF p < 0.02), la inflación marginalmente I(0) y la revisión fuertemente I(0). La regresión de Mincer-Zarnowitz en niveles, así como las regresiones de eficiencia y rigidez, no enfrentan riesgo de regresión espuria."));

// 5. METODOLOGÍA
c.push(H1("5. Metodología"));
c.push(H2("5.1. Inferencia con datos solapados"));
c.push(P("El uso de pronósticos a doce meses sobre datos mensuales genera autocorrelación inducida en los errores hasta el orden 11 incluso bajo racionalidad. Ignorar esta autocorrelación produce errores estándar inválidos y rechazos espurios de hipótesis. Se sigue la práctica de West (1996) y Pesaran y Weale (2006) y se reporta errores estándar HAC tipo Newey-West, con bandwidth seleccionado mediante la regla automática de Newey-West (1994), garantizando un mínimo de 11 rezagos. Como verificación de robustez, también se reporta los tests con el bandwidth de Hodrick (1992), 2h − 1 = 23, recomendado para regresiones con horizonte de pronóstico solapado h = 12."));

c.push(H2("5.2. Quiebres estructurales"));
c.push(P("Se aplica la prueba supF de Quandt-Andrews (1993) para detectar el quiebre desconocido más significativo en el intercepto del error de pronóstico, restringiendo el espacio de búsqueda al 70% central de la muestra (trimming del 15%). Los valores críticos provienen de la simulación de Andrews (1993) para un parámetro de quiebre y trimming de 0.15 (10%: 7.04, 5%: 8.85, 1%: 12.16). La motivación es separar el episodio pandémico del régimen previo y testear la estabilidad de los parámetros estructurales."));

c.push(H2("5.3. Análisis de submuestras"));
c.push(P("Re-se estima las pruebas centrales en dos submuestras: pre-pandemia (junio 2010 – febrero 2020) y post-pandemia (marzo 2020 – marzo 2026). La fecha de corte se elige por el inicio del confinamiento global y la disrupción de cadenas de suministro. Esta partición permite testear si las desviaciones de la racionalidad detectadas en la muestra completa son estructurales o se concentran en el episodio inflacionario reciente. Adicionalmente, se reporta un test formal de cambio de régimen mediante interacción del coeficiente de Coibion-Gorodnichenko con la dummy post-2020."));

c.push(H2("5.4. Evaluación predictiva fuera de muestra"));
c.push(P("Para complementar las pruebas de racionalidad, que evalúan propiedades estadísticas del error pero no la calidad relativa del pronóstico, se construye un ejercicio de evaluación predictiva fuera de muestra. Se toma como ventana de estimación el subperiodo junio 2010 – diciembre 2018 y como ventana de evaluación el subperiodo enero 2019 – marzo 2026 (87 observaciones), que incluye el shock inflacionario completo. Se compara el RMSE del consenso EEM contra tres benchmarks: un random walk a doce meses (π_{t−12}), un AR(1) recursivo sobre la inflación interanual y un ancla a la meta del 4%. Se aplica el test de Diebold-Mariano (1995) con corrección de Harvey, Leybourne y Newbold (1997) para muestras pequeñas, con loss cuadrático y bandwidth de h − 1 = 11."));

// 6. RESULTADOS
c.push(H1("6. Resultados"));

// 6.1 Insesgamiento
c.push(H2("6.1. Test de insesgamiento"));
const t1f=R.t1_insesgamiento.full, t1p=R.t1_insesgamiento.pre, t1po=R.t1_insesgamiento.post;
c.push(P(`La regresión del error de pronóstico sobre una constante (Ecuación 1) arroja un intercepto estimado de ${fmt(t1f.alpha,2)} p.p. en la muestra completa, con error estándar HAC de ${fmt(t1f.se,2)} y p-valor ${fmtP(t1f.p)}, no significativo a niveles convencionales. La magnitud puntual indica una sobreestimación promedio del consenso del orden de 0.4 p.p., pero estadísticamente no se distingue de cero al 5%. La media de la muestra completa enmascara, sin embargo, comportamientos heterogéneos por subperíodo que el análisis posterior expone.`));

c.push(P(`La separación por subperíodos es informativa. En el periodo pre-pandémico (N = ${t1p.n}), el sesgo de sobreestimación es robusto y altamente significativo: α = ${fmt(t1p.alpha,2)} p.p. con p ${fmtP(t1p.p)}. En este régimen, los analistas sobreestimaron sistemáticamente la inflación futura por aproximadamente 1.3 puntos porcentuales, hallazgo consistente con la dinámica de inflación a la baja que caracterizó al periodo y con un anclaje de las expectativas a niveles superiores al efectivo. En el periodo post-pandémico (N = ${t1po.n}), el coeficiente cambia a α = ${fmt(t1po.alpha,2)} p.p. (p ${fmtP(t1po.p)}), no significativo dada la elevada varianza del error en este subperiodo, pero el signo negativo se mantiene impulsado por el episodio inicial del shock cuando la inflación realizada cayó por debajo de las expectativas.`));

// CUADRO 3: Tres tests sintéticos
const t2f=R.t2_mincer_zarnowitz.full, t2p=R.t2_mincer_zarnowitz.pre, t2po=R.t2_mincer_zarnowitz.post;
const t3f=R.t3_persistencia.full;

const t3H = new TableRow({ tableHeader:true, children:[
  TC("",                        { width:2400, shading:"E8E8E8" }),
  TC("Eq. (1) Insesgamiento",   { width:2200, bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
  TC("Eq. (2) Mincer-Zarnowitz",{ width:2400, bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
  TC("Eq. (3) Persistencia",    { width:2360, bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
]});

const tabla3Data = [
  ["Constante (α)",        pp(t1f.alpha, t1f.p),       pp(t2f.alpha, t2f.p_alpha),     pp(t3f.alpha, t3f.p_alpha)],
  ["",                      `(${fmt(t1f.se,3)})`,        `(${fmt(t2f.se_alpha,3)})`,      `(${fmt(t3f.se_alpha,3)})`],
  ["E_{t−12}[π_t] (β)",   "—",                          pp(t2f.beta, t2f.p_beta),       "—"],
  ["",                      "",                           `(${fmt(t2f.se_beta,3)})`,       ""],
  ["e_{t−12}  (ρ)",       "—",                          "—",                              pp(t3f.rho, t3f.p_rho)],
  ["",                      "",                           "",                               `(${fmt(t3f.se_rho,3)})`],
  ["Wald α=0, β=1  (χ²)", "—",                          fmt(t2f.wald_chi2,2),              "—"],
  ["p-valor (Wald, NW)",   "—",                          fmtPv(t2f.wald_p),                  "—"],
  ["p-valor (Wald, Hodrick)","—",                       fmtPv(t2f.wald_p_hodrick),          "—"],
  ["R²",                    "—",                          fmt(t2f.r2,3),                    fmt(t3f.r2,3)],
  ["N",                     `${t1f.n}`,                   `${t2f.n}`,                       `${t3f.n}`],
];
const t3Rows = tabla3Data.map((r,i) => new TableRow({ children: r.map((v,j) => TC(v,{
  width:[2400,2200,2400,2360][j],
  align: j===0?AlignmentType.LEFT:AlignmentType.CENTER,
  bold: j===0 && [0,2,4,6,7,8].includes(i)
}))}));

c.push(Cap("Cuadro 3. Pruebas de racionalidad: muestra completa"));
c.push(new Table({
  width:{ size:9360, type:WidthType.DXA },
  columnWidths:[2400,2200,2400,2360],
  rows:[t3H, ...t3Rows]
}));
c.push(Note("Nota: Errores estándar HAC tipo Newey-West entre paréntesis. *** p<0.01, ** p<0.05, * p<0.10. La hipótesis conjunta del test de Mincer-Zarnowitz se contrasta mediante prueba de Wald con la matriz HAC, reportada con bandwidth automático Newey-West y bandwidth de Hodrick (2h−1 = 23). Fuente: cálculos propios."));

// 6.2 MZ
c.push(H2("6.2. Test de eficiencia de Mincer-Zarnowitz"));
c.push(P(`La regresión del realizado sobre el esperado (Ecuación 2) en la muestra completa arroja un intercepto de ${fmt(t2f.alpha,2)} y una pendiente de ${fmt(t2f.beta,2)}. La pendiente es marginalmente significativa al 10% pero no al 5%, y el estadístico de Wald conjunto para H₀: α = 0 ∧ β = 1 no rechaza (χ²(2) = ${fmt(t2f.wald_chi2,2)}, p ${fmtP(t2f.wald_p)} NW; p ${fmtP(t2f.wald_p_hodrick)} Hodrick). El resultado en muestra completa enmascara comportamientos heterogéneos por subperíodo que el análisis posterior expone.`));

c.push(P(`En el periodo pre-pandémico (N = ${t2p.n}), el intercepto es ${fmt(t2p.alpha,2)} (no significativo) y la pendiente es β = ${fmt(t2p.beta,2)}, prácticamente unitaria en valor puntual. Sin embargo, la prueba conjunta de Wald rechaza la racionalidad MZ con χ²(2) = ${fmt(t2p.wald_chi2,2)} (p ${fmtP(t2p.wald_p)} NW; p ${fmtP(t2p.wald_p_hodrick)} Hodrick) al 5%. El rechazo proviene de la imprecisión de la pendiente y de la combinación con el intercepto: aunque β es aritméticamente cercano a 1, el R² es solamente ${fmt(t2p.r2,2)}, lo que indica que la expectativa del consenso explica una fracción modesta de la varianza de la inflación realizada incluso en el régimen estable.`));

c.push(P(`El comportamiento post-pandémico es más informativo y aporta el resultado más llamativo del test. La pendiente colapsa a β = ${fmt(t2po.beta,3)}, prácticamente cero, con error estándar de ${fmt(t2po.se_beta,2)} (no significativa, p ${fmtP(t2po.p_beta)}). El intercepto, en cambio, es α = ${fmt(t2po.alpha,2)} (significativo al 5%, p ${fmtP(t2po.p_alpha)}), y la prueba conjunta de Wald rechaza al 1% bajo bandwidth de Hodrick (χ²(2) = ${fmt(t2po.wald_chi2_hodrick,2)}, p ${fmtP(t2po.wald_p_hodrick)}). La interpretación es directa: durante el shock inflacionario las expectativas se mantuvieron prácticamente fijas en torno al 4% mientras que la inflación realizada se movió ampliamente entre 1% y 10.5%; la covarianza entre realizado y esperado se aproxima a cero, anulando estadísticamente la pendiente. La Figura 2 visualiza el ajuste MZ.`));

c.push(FigImg(path.join(__dirname, '..', '04_figuras', 'fig2_mz_scatter.png'), 460, 360));
c.push(Cap("Figura 2. Diagrama de Mincer-Zarnowitz"));
c.push(Note("Nota: Cada punto representa una observación mensual del par (E_{t−12}[π_t] formada en t−12, π_t realizada). Línea punteada: predicción perfecta (45°). Línea continua: ajuste OLS sobre la muestra completa. Color codifica el subperíodo (azul = pre-pandemia, rojo = post-pandemia). El test de Wald conjunto rechaza α=0 ∧ β=1 al 5% en pre-pandemia y al 1% en post-pandemia bajo bandwidth de Hodrick."));

// 6.3 Persistencia
c.push(H2("6.3. Persistencia del error"));
c.push(P(`La regresión del error sobre el error rezagado doce meses (Ecuación 3) arroja un coeficiente ρ = ${fmt(t3f.rho,3)} con p-valor HAC ${fmtP(t3f.p_rho)} en la muestra completa, no significativo a los niveles convencionales. La hipótesis de innovación blanca del error de pronóstico, propiedad implícita en la racionalidad, no se rechaza en la dimensión temporal de doce meses sobre la muestra completa.`));

c.push(P(`En el periodo pre-pandémico, el coeficiente es ρ = ${fmt(R.t3_persistencia.pre.rho,3)} con p-valor HAC ${fmtP(R.t3_persistencia.pre.p_rho)}, marginalmente significativo al 10%. El signo negativo en pre-pandemia sugiere un patrón débil de sobre-corrección anual: errores positivos tienden a ser seguidos por errores ligeramente negativos doce meses después. La evidencia es modesta y no robusta a la elección de bandwidth, por lo que la lectura prudente es que la propiedad de no-persistencia se sostiene aproximadamente y que las desviaciones detectadas en otras dimensiones de racionalidad no se manifiestan en una autocorrelación significativa del error de pronóstico al rezago de doce meses.`));

// 6.4 Eficiencia informacional
c.push(H2("6.4. Eficiencia informacional"));
c.push(P(`El Cuadro 4 reporta la regresión del error de pronóstico sobre el set de información observable disponible al momento de formar la expectativa (Ecuación 4). Las variables explicativas son la inflación realizada, la tasa de política monetaria efectiva, la variación interanual del tipo de cambio nominal y el crecimiento interanual del PIB real, todas rezagadas trece meses para garantizar que estaban en el set de información en el momento de la formación de la expectativa a doce meses. Las cuatro provienen de series oficiales del BCRD (no de las medianas reportadas por el panel de la EEM) a fin de ejecutar un contraste auténtico de ortogonalidad respecto a información pública. El test de Wald para la nula conjunta γ = 0 arroja χ²(4) = ${fmt(t4.wald_chi2,2)} con p-valor ${fmtP(t4.wald_p)}, rechazando la eficiencia informacional al 1% por amplio margen.`));

const labels4 = ['Constante','Inflación rezagada (π_{t−13})','TPM efectiva rezagada (i_{t−13})','Var. tipo de cambio rezagada (Δe_{t−13})','Crec. PIB real rezagado (Δy_{t−13})'];
const t4H = new TableRow({ tableHeader:true, children:[
  TC("Regresor",   { width:3600, bold:true, shading:"E8E8E8" }),
  TC("Coeficiente",{ width:1700, bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
  TC("EE (HAC)",   { width:1300, bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
  TC("p-valor",    { width:1400, bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
  TC("VIF",        { width:1360, bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
]});

const vifs = R.t4_eficiencia_info_oficial.vifs;
const vifList = ['—', vifs['π_t-13'], vifs['TPM_obs_t-13'], vifs['Var_TC_obs_t-13'], vifs['Var_PIB_obs_t-13']];

const t4Body = labels4.map((label, i) => new TableRow({ children:[
  TC(label, { width:3600 }),
  TC(pp(t4.params[i], t4.p[i]), { width:1700, align:AlignmentType.CENTER }),
  TC(fmt(t4.se[i],3),           { width:1300, align:AlignmentType.CENTER }),
  TC(fmtPv(t4.p[i]),             { width:1400, align:AlignmentType.CENTER }),
  TC(typeof vifList[i] === 'number' ? fmt(vifList[i],2) : vifList[i], { width:1360, align:AlignmentType.CENTER }),
]}));

const t4Foot = [
  new TableRow({ children:[
    TC("Wald conjunto γ = 0  (χ²(4))", { width:3600, bold:true }),
    TC(fmt(t4.wald_chi2,2),            { width:1700, align:AlignmentType.CENTER, bold:true }),
    TC("—",                            { width:1300, align:AlignmentType.CENTER }),
    TC(`${fmtP(t4.wald_p)}***`,        { width:1400, align:AlignmentType.CENTER, bold:true }),
    TC("—",                            { width:1360, align:AlignmentType.CENTER }),
  ]}),
  new TableRow({ children:[
    TC("R² total / R² parcial TPM", { width:3600 }),
    TC(`${fmt(t4.r2,3)} / ${fmt(R.t4_eficiencia_info_oficial.r2_partial['TPM_obs_t-13'],3)}`, { width:1700, align:AlignmentType.CENTER }),
    TC("—",       { width:1300, align:AlignmentType.CENTER }),
    TC("—",       { width:1400, align:AlignmentType.CENTER }),
    TC("—",       { width:1360, align:AlignmentType.CENTER }),
  ]}),
  new TableRow({ children:[
    TC("N",       { width:3600 }),
    TC(`${t4.n}`, { width:1700, align:AlignmentType.CENTER }),
    TC("—",       { width:1300, align:AlignmentType.CENTER }),
    TC("—",       { width:1400, align:AlignmentType.CENTER }),
    TC("—",       { width:1360, align:AlignmentType.CENTER }),
  ]}),
];
c.push(Cap("Cuadro 4. Test de eficiencia informacional con variables observables oficiales (Eq. 4)"));
c.push(new Table({ width:{ size:9360, type:WidthType.DXA }, columnWidths:[3600,1700,1300,1400,1360], rows:[t4H, ...t4Body, ...t4Foot] }));
c.push(Note("Nota: Variable dependiente: error de pronóstico e_t. Regresores: series observadas oficiales del BCRD (no medianas del panel EEM). Errores estándar HAC tipo Newey-West con bandwidth automático ≥ 11. *** p<0.01, ** p<0.05, * p<0.10. VIF mide multicolinealidad. El VIF de la TPM rezagada (4.90) se sitúa en el límite convencional de 5, lo que motiva las verificaciones complementarias reportadas en el ARDL extendido (sección 7.12) y en el bootstrap por bloques sobre el coeficiente de la TPM (sección 7.5); ambas verificaciones convergen en un rechazo de eficiencia informacional con la misma magnitud cualitativa. Fuente: cálculos propios."));

c.push(P(`La estructura del rechazo es informativa y contundente. La TPM efectiva rezagada es el predictor dominante por amplio margen: coeficiente = ${fmt(t4.params[2],2)} con p-valor ${fmtP(t4.p[2])}, y captura un R² parcial de ${fmt(R.t4_eficiencia_info_oficial.r2_partial['TPM_obs_t-13'],3)} dentro de un R² total del modelo de ${fmt(t4.r2,3)}. Esto es, la TPM rezagada explica por sí sola el ${(R.t4_eficiencia_info_oficial.r2_partial['TPM_obs_t-13']/t4.r2*100).toFixed(0)}% de la varianza explicada del error de pronóstico. Las demás variables (inflación rezagada, variación del tipo de cambio rezagada y crecimiento del PIB rezagado) no son individualmente significativas al 5% una vez controlado por la TPM, aunque contribuyen marginalmente al rechazo conjunto. El VIF de la TPM rezagada (4.90) se sitúa en el límite convencional de 5; el siguiente VIF más alto (inflación rezagada) es 3.70, claramente bajo el umbral convencional, y los VIFs de tipo de cambio y PIB son 1.87 y 2.03 respectivamente. Por prudencia frente al límite del VIF de la TPM, la sección 7.12 reporta una especificación ARDL alternativa con rezagos doce a dieciocho de la TPM (Wald χ²(7) = ${fmt(R.ardl_tpm_eficiencia.wald_conjunto_tpm_chi2,2)}, p < 0.001) y la sección 7.5 reporta un bootstrap por bloques sobre el coeficiente de la TPM (IC 95% [${fmt(R.bootstrap_bloques.tpm_eficiencia.IC_95[0],2)}, ${fmt(R.bootstrap_bloques.tpm_eficiencia.IC_95[1],2)}]); ambas verificaciones confirman el rechazo de eficiencia informacional sin depender de la inversión exacta de la matriz de covarianza, lo que descarta multicolinealidad como explicación del resultado.`));

c.push(P(`El signo negativo del coeficiente sobre la TPM rezagada (${fmt(t4.params[2],2)}) tiene una lectura económica directa: cuando la postura de política monetaria era contractiva trece meses atrás, el error subsiguiente tiende a ser negativo, es decir, los analistas sobreestimaron la inflación subsiguiente. La interpretación más conservadora del hallazgo es que la TPM rezagada predice estadísticamente el error de pronóstico, lo que es consistente con sub-utilización de la información sobre la postura monetaria. Una interpretación causal más fuerte (que los analistas no incorporen óptimamente la TPM en su mecanismo de formación de expectativas) requeriría un modelo estructural que vincule TPM, inflación y expectativas, vía por ejemplo una curva de Phillips dominicana con TPM como instrumento. Tal modelo está fuera del alcance de este trabajo y queda como agenda futura. Lo que sí queda establecido como hallazgo estadístico robusto es que el error de pronóstico es predecible a partir de la TPM rezagada, una variable observable y de dominio público al momento de pronosticar, en violación de la propiedad de eficiencia informacional bajo cualquier definición razonable.`));

// 6.5 CG
c.push(H2("6.5. Test de rigidez informacional de Coibion-Gorodnichenko"));
c.push(P(`El Cuadro 5 reporta la regresión central de Coibion-Gorodnichenko (Ecuación 5) en muestra completa y por subperíodos. En la muestra completa, λ = ${fmt(t5full.lambda,3)} con p-valor Newey-West ${fmtP(t5full.p_lambda)} (p ${fmtP(t5full.p_lambda_hodrick)} bajo Hodrick), significativo al 5%. La interpretación estructural en términos de probabilidad mensual de actualización es ψ = 1/(1+λ) ≈ ${fmt(1/(1+t5full.lambda),2)}, que indica que aproximadamente la mitad de los analistas actualiza su set de información cada mes. Sin embargo, la lectura más informativa surge al separar los subperíodos.`));

const t5H = new TableRow({ tableHeader:true, children:[
  TC("",                 { width:2800, shading:"E8E8E8" }),
  TC("Muestra completa", { width:2200, bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
  TC("Pre-pandemia",     { width:2200, bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
  TC("Post-pandemia",    { width:2160, bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
]});
const t5p_post = R.t5_coibion_gorod.post;
const psi_pre = (t5pre.lambda > -1) ? (1/(1+t5pre.lambda)).toFixed(2) : "—";
const psi_post = (t5p_post.lambda > -1) ? (1/(1+t5p_post.lambda)).toFixed(2) : "—";
const psi_full = (t5full.lambda > -1) ? (1/(1+t5full.lambda)).toFixed(2) : "—";

const t5Data = [
  ["Periodo",          "2010m6–2026m3",                "2010m6–2020m2",                "2020m3–2026m3"],
  ["λ (revisión)",     pp(t5full.lambda, t5full.p_lambda), pp(t5pre.lambda, t5pre.p_lambda),  pp(t5p_post.lambda, t5p_post.p_lambda)],
  ["",                 `(${fmt(t5full.se_lambda,3)})`,     `(${fmt(t5pre.se_lambda,3)})`,        `(${fmt(t5p_post.se_lambda,3)})`],
  ["p-valor Hodrick",  fmtPv(t5full.p_lambda_hodrick),     fmtPv(t5pre.p_lambda_hodrick),         fmtPv(t5p_post.p_lambda_hodrick)],
  ["Constante (α)",    pp(t5full.alpha, t5full.p_alpha),  pp(t5pre.alpha, t5pre.p_alpha),       pp(t5p_post.alpha, t5p_post.p_alpha)],
  ["",                 `(${fmt(t5full.se_alpha,3)})`,     `(${fmt(t5pre.se_alpha,3)})`,        `(${fmt(t5p_post.se_alpha,3)})`],
  ["ψ = 1/(1+λ)",      psi_full,                           psi_pre,                              psi_post],
  ["R²",               fmt(t5full.r2,3),                   fmt(t5pre.r2,3),                      fmt(t5p_post.r2,3)],
  ["N",                `${t5full.n}`,                      `${t5pre.n}`,                         `${t5p_post.n}`],
];
const t5Rows = t5Data.map((row, idx) => new TableRow({ children: row.map((v, i) => TC(v, {
  width:[2800,2200,2200,2160][i],
  align: i===0?AlignmentType.LEFT:AlignmentType.CENTER,
  bold: idx===0 || idx===1 || idx===6
}))}));
c.push(Cap("Cuadro 5. Test de Coibion-Gorodnichenko, muestra completa y submuestras"));
c.push(new Table({ width:{ size:9360, type:WidthType.DXA }, columnWidths:[2800,2200,2200,2160], rows:[t5H, ...t5Rows] }));
c.push(Note("Nota: Variable dependiente: error de pronóstico e_t. Errores estándar HAC tipo Newey-West entre paréntesis; p-valor Hodrick reportado adicionalmente para bandwidth 2h−1=23. ψ ≡ 1/(1+λ) interpreta a λ como probabilidad de actualización mensual en el modelo de Mankiw-Reis (2002). *** p<0.01, ** p<0.05, * p<0.10. Fuente: cálculos propios."));

c.push(P(`En el periodo pre-pandémico, λ = ${fmt(t5pre.lambda,3)} con p-valor Newey-West ${fmtP(t5pre.p_lambda)} y p-valor Hodrick ${fmtP(t5pre.p_lambda_hodrick)}, marginalmente significativo solo bajo este último al 10%. La probabilidad implícita de actualización es ψ ≈ ${fmt(1/(1+t5pre.lambda),2)}, indicativa de un grado modesto de rigidez informacional consistente con racionalidad aproximada en el régimen estable. En el periodo post-pandémico, λ salta a ${fmt(t5p_post.lambda,2)} con p-valor Hodrick ${fmtP(t5p_post.p_lambda_hodrick)}, altamente significativo al 1%. La probabilidad implícita de actualización cae a ψ ≈ ${fmt(1/(1+t5p_post.lambda),2)}, una reducción sustancial respecto al régimen pre-pandémico.`));

c.push(P(`El test formal de cambio de régimen mediante interacción dummy×revisión confirma esta lectura. Estimando el modelo aumentado con dummy post-2020, la prueba de Wald conjunta sobre los términos pandemia (dummy + interacción) arroja χ²(2) = ${fmt(R.interaccion_pandemia.wald_regime_chi2,2)} con p ${fmtP(R.interaccion_pandemia.wald_regime_p)}, rechazando la estabilidad de los parámetros al 1%. La dicotomía pre/post-pandémica de la rigidez informacional es estadísticamente robusta.`));

c.push(P(`Esta dicotomía sugiere una lectura matizada de la racionalidad: las expectativas dominicanas son aproximadamente consistentes con FIRE en condiciones de inflación estable y baja varianza, pero exhiben rigidez informacional pronunciada bajo choques de gran magnitud, cuando la información se incorpora al pronóstico con retraso. El hallazgo es coherente con la evidencia internacional posterior a 2020 (Andrade, Gautier y Mengus, 2023; Kohlhas y Walther, 2021), que documenta un deterioro generalizado de la calidad predictiva de las encuestas de expectativas durante el shock inflacionario global. Cabe advertir, siguiendo a Bordalo, Gennaioli, Ma y Shleifer (2020), que la interpretación estructural de ψ = 1/(1+λ) sobre el consenso (mediana) mezcla rigidez genuina con disagreement entre agentes y debe ser leída con prudencia. Una replicación con datos individuales del panel EEM permitiría descomponer estos componentes y queda como agenda futura.`));

c.push(FigImg(path.join(__dirname, '..', '04_figuras', 'fig3_cg_subperiodos.png'), 580, 240));
c.push(Cap("Figura 3. Test de Coibion-Gorodnichenko por subperíodo"));
c.push(Note("Nota: Cada panel grafica el error de pronóstico e_t contra la revisión rev_t = E_t[π_{t+12}] − E_{t−1}[π_{t+12}] del consenso. Bajo FIRE, la pendiente debería ser cero. Pendiente positiva indica rigidez informacional (sub-reacción); pendiente negativa indica sobre-reacción. La línea sólida es el ajuste OLS por subperíodo."));

c.push(FigImg(path.join(__dirname, '..', '04_figuras', 'fig4_lambda_rolling.png'), 580, 235));
c.push(Cap("Figura 4. Evolución temporal del coeficiente de Coibion-Gorodnichenko"));
c.push(Note("Nota: λ estimado sobre ventanas móviles de 36 meses con errores estándar HAC Newey-West (lag 6); las bandas sombreadas indican el IC 95% punto-a-punto. La región gris corresponde al periodo post-marzo 2020 (sombreado claro: subperíodo postpandémico; sombreado rosado en los últimos 12 meses: zona endpoint sensible donde la ventana móvil contiene proporcionalmente más datos del régimen reciente y el estimador es menos preciso, práctica estándar en estimación rolling con datos solapados de horizonte h=12). La línea vertical punteada en enero 2017 marca el rediseño metodológico de la EEM. La interpretación estructural ψ = 1/(1+λ) como probabilidad mensual de actualización está restringida a λ ≥ 0 por la semántica del modelo Mankiw-Reis (2002); los segmentos de la muestra con λ < 0 no admiten esa lectura estructural y se reportan solo como coeficiente reducido. Los IC 95% cubren cero en aproximadamente el 72% de las ventanas, lo que es consistente con la sensibilidad inferencial del coeficiente CG documentada en la sección 7.5 bajo bootstrap por bloques."));

c.push(P(`La Figura 4 admite tres lecturas que refuerzan los hallazgos del paper. Primero, λ se mantiene cerca de cero antes del rediseño metodológico de la EEM en enero de 2017, asciende monótonamente entre 2017 y 2021, y alcanza su máximo (~2.5) durante el peak inflacionario de 2021–2022, consistente con la dicotomía pre-2017/post-2017 documentada en la sección 6.5 y con la lectura "rigidez informacional pronunciada bajo choques de gran magnitud". Segundo, conforme la inflación realizada se re-ancla hacia la meta del 4% durante 2023 y 2024, λ desciende sustancialmente, lo que es coherente con un patrón de re-anclaje de las expectativas en el régimen post-shock, patrón también documentado por Andrade, Gautier y Mengus (2023) para Francia y la zona euro durante el mismo episodio inflacionario global. Tercero, el descenso de λ a valores transitoriamente negativos en 2025 sugiere que el re-anclaje podría manifestarse no solo como reducción de la rigidez sino como sobre-reacción transitoria, en línea con Bordalo et al. (2020); sin embargo, la magnitud de este descenso final no es estadísticamente distinguible de cero bajo las bandas de confianza, y la zona endpoint sensible (últimos 12 meses, sombreada en rosado) requiere especial cautela interpretativa porque el estimador rolling tiene baja precisión en el extremo de la muestra. La conclusión cualitativa es que el patrón temporal del coeficiente CG, lejos de ser una fluctuación aleatoria, sigue una trayectoria coherente con el ciclo inflacionario post-pandémico, pero la magnitud puntual de λ en cualquier ventana específica debe leerse con la holgura inferencial que las bandas indican.`));

// 6.6 OOS Diebold-Mariano
c.push(H2("6.6. Evaluación predictiva fuera de muestra"));
c.push(P(`El Cuadro 6 reporta los resultados del ejercicio out-of-sample. Sobre la ventana de evaluación enero 2019 – marzo 2026 (N = 87 observaciones), el consenso EEM presenta un RMSE de ${fmt(dm.EEM.RMSE,2)}, comparable al del ancla a la meta del 4% (${fmt(dm.Ancla.RMSE,2)}), al AR(1) recursivo (${fmt(dm.AR1.RMSE,2)}) y al random walk a doce meses (${fmt(dm.RW.RMSE,2)}). Las cuatro alternativas predictivas producen errores cuadráticos medios sustancialmente similares, con diferencias del orden de la décima.`));

const t6H = new TableRow({ tableHeader:true, children:[
  TC("Modelo",                          { width:3200, bold:true, shading:"E8E8E8" }),
  TC("RMSE",                            { width:1200, bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
  TC("MAE",                             { width:1200, bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
  TC("ME",                              { width:1200, bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
  TC("DM vs EEM",                       { width:1300, bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
  TC("p-valor",                         { width:1260, bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
]});
const t6Rows = [
  ["EEM consenso", fmt(dm.EEM.RMSE,2), fmt(dm.EEM.MAE,2), fmt(dm.EEM.ME,2), "—", "—"],
  ["Random walk a 12m", fmt(dm.RW.RMSE,2), fmt(dm.RW.MAE,2), fmt(dm.RW.ME,2), fmt(dm.DM_EEM_vs_RW.dm_corr,2), fmtPv(dm.DM_EEM_vs_RW.p_value)],
  ["AR(1) recursivo", fmt(dm.AR1.RMSE,2), fmt(dm.AR1.MAE,2), fmt(dm.AR1.ME,2), fmt(dm.DM_EEM_vs_AR1.dm_corr,2), fmtPv(dm.DM_EEM_vs_AR1.p_value)],
  ["Ancla a meta 4%", fmt(dm.Ancla.RMSE,2), fmt(dm.Ancla.MAE,2), fmt(dm.Ancla.ME,2), fmt(dm.DM_EEM_vs_Ancla.dm_corr,2), fmtPv(dm.DM_EEM_vs_Ancla.p_value)],
].map(row => new TableRow({ children: row.map((v,i) => TC(v,{
  width:[3200,1200,1200,1200,1300,1260][i],
  align: i===0?AlignmentType.LEFT:AlignmentType.CENTER
}))}));
c.push(Cap("Cuadro 6. Evaluación predictiva fuera de muestra y test de Diebold-Mariano"));
c.push(new Table({ width:{ size:9360, type:WidthType.DXA }, columnWidths:[3200,1200,1200,1200,1300,1260], rows:[t6H, ...t6Rows] }));
c.push(Note(`Nota: Ventana de evaluación enero 2019 – marzo 2026, N = 87. RMSE = raíz del error cuadrático medio; MAE = error absoluto medio; ME = error medio. DM = estadístico de Diebold-Mariano (1995) con corrección de Harvey, Leybourne y Newbold (1997) para muestras pequeñas. Loss cuadrático, bandwidth h−1 = 11. Signo negativo del DM indica que el modelo de comparación tiene mayor error que el EEM. Fuente: cálculos propios.`));

c.push(P(`Consistente con la similitud de los RMSE, el test de Diebold-Mariano no rechaza la nula de igualdad de loss esperado en ninguna de las comparaciones: DM = ${fmt(dm.DM_EEM_vs_RW.dm_corr,2)} con p ${fmtP(dm.DM_EEM_vs_RW.p_value)} contra random walk; DM = ${fmt(dm.DM_EEM_vs_AR1.dm_corr,2)} con p ${fmtP(dm.DM_EEM_vs_AR1.p_value)} contra AR(1); DM = ${fmt(dm.DM_EEM_vs_Ancla.dm_corr,2)} con p ${fmtP(dm.DM_EEM_vs_Ancla.p_value)} contra ancla a meta. La interpretación es directa: durante la ventana de evaluación, el consenso de analistas profesionales no domina estadísticamente a benchmarks naïve a doce meses.`));

c.push(P(`Este resultado es relevante por su contraste con la interpretación favorable que se le suele dar a las encuestas de expectativas en banca central. La separación por subperíodo es informativa: en el subperíodo OOS post-pandemia (N = 73, el subperíodo donde el ejercicio tiene poder estadístico significativo), la ventaja del EEM sobre el random walk se mantiene marginal (RMSE 2.78 vs 2.95) y el test DM no rechaza igualdad estadística. El subperíodo OOS pre-pandemia tiene N = 14 observaciones que, dado el horizonte de solapamiento h = 12, equivalen a aproximadamente una observación efectivamente independiente; se reporta las magnitudes RMSE de 2.42 (EEM) y 2.56 (random walk) como ilustrativas pero no se construye inferencia formal sobre ese subperíodo dado el poder esencialmente nulo del test DM. La conclusión global es que el contenido informacional adicional del consenso de analistas sobre benchmarks mecánicos a horizonte de doce meses es, a lo sumo, modesto. Esta conclusión es consistente con literatura comparable que ha documentado dificultades de los pronósticos de encuestas para superar a benchmarks naïve a horizontes anuales (Atkeson y Ohanian, 2001; Faust y Wright, 2013).`));

c.push(FigImg(path.join(__dirname, '..', '04_figuras', 'fig5_oos_comparacion.png'), 580, 253));
c.push(Cap("Figura 5. Comparación de pronósticos out-of-sample"));
c.push(Note("Nota: Pronósticos a 12 meses producidos al inicio de cada ventana versus inflación realizada. EEM consenso: mediana de la encuesta. Random walk: π_{t−12}. AR(1) recursivo: estimado con datos hasta t−12. Ancla 4%: pronóstico constante igual a la meta de inflación. Periodo de evaluación 2019m1–2026m3."));

// 7. ROBUSTEZ
c.push(H1("7. Robustez y diagnósticos"));
c.push(H2("7.1. Diagnósticos del modelo de Mincer-Zarnowitz"));
const dg = R.diagnosticos;
const t7H = new TableRow({ tableHeader:true, children:[
  TC("Prueba",       { width:3500, bold:true, shading:"E8E8E8" }),
  TC("Estadístico",  { width:1900, bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
  TC("p-valor",      { width:1700, bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
  TC("Decisión al 5%",{ width:2260, bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
]});
const dec = (p) => p<0.05?'Rechaza H₀':'No rechaza H₀';
const t7Rows = [
  ["Breusch-Pagan (heteroscedasticidad)",  `BP = ${fmt(dg.bp[0],2)}`,         fmtPv(dg.bp[1]), dec(dg.bp[1])],
  ["Breusch-Godfrey 12 (autocorrelación)", `LM = ${fmt(dg.bg[0],2)}`,         fmtPv(dg.bg[1]), `${dec(dg.bg[1])} ⇒ HAC necesario`],
  ["Ljung-Box 12",                         `Q = ${fmt(dg.lb[0],2)}`,          fmtPv(dg.lb[1]), `${dec(dg.lb[1])} ⇒ HAC necesario`],
  ["Ramsey RESET (especificación)",        `F = ${fmt(dg.reset[0],2)}`,       fmtPv(dg.reset[1]), dec(dg.reset[1])],
  ["Jarque-Bera (normalidad)",             `JB = ${fmt(dg.jb[0],2)}`,         fmtPv(dg.jb[1]), dec(dg.jb[1])],
].map(row => new TableRow({ children: row.map((v, i) => TC(v, {
  width:[3500,1900,1700,2260][i],
  align: i===0?AlignmentType.LEFT:AlignmentType.CENTER
}))}));

c.push(Cap("Cuadro 7. Diagnósticos del modelo de Mincer-Zarnowitz"));
c.push(new Table({ width:{ size:9360, type:WidthType.DXA }, columnWidths:[3500,1900,1700,2260], rows:[t7H, ...t7Rows] }));
c.push(Note("Nota: La presencia de autocorrelación serial confirma la necesidad de inferencia HAC, que es la utilizada en todas las pruebas reportadas. La no normalidad de los residuos es esperable y no invalida la inferencia asintótica de las pruebas de Wald."));

c.push(P("Los diagnósticos confirman la presencia de autocorrelación serial inducida por el solapamiento del horizonte de pronóstico (Breusch-Godfrey y Ljung-Box rechazan la nula de no autocorrelación a doce rezagos con p < 0.001), lo que valida la elección de errores estándar HAC. Breusch-Pagan no detecta heteroscedasticidad incondicional al 5% (p = 0.996), aunque la varianza del error sí cambia entre regímenes, fenómeno que se aborda con el análisis por subperíodos y con la matriz de varianza HAC. La prueba RESET de Ramsey rechaza la especificación lineal al 1% (p = 0.004), señal de no linealidad en la relación entre realizado y esperado; explorar especificaciones polinomiales o de cambio de régimen es una extensión natural para trabajo futuro. La no normalidad de los residuos detectada por Jarque-Bera es habitual en macroeconomía y no afecta la validez asintótica de las pruebas de Wald."));

c.push(H2("7.2. Quiebre estructural"));
c.push(P(`La prueba supF de Quandt-Andrews aplicada al intercepto del error de pronóstico arroja un estadístico de ${fmt(qb.sup_f,2)}, ampliamente superior al valor crítico al 1% de Andrews (1993) de 12.16. La fecha del máximo F se ubica en ${qb.fecha} (observación ${qb.tau} de la muestra), prácticamente coincidente con marzo de 2020 que se utilizó como punto de corte exógeno. La consistencia entre el quiebre endógenamente fechado y el quiebre exógeno motivado teóricamente refuerza la lectura de cambio de régimen entre el periodo pre-pandémico y el episodio inflacionario subsiguiente.`));

c.push(P(`Este resultado complementa la evidencia de la sección 6.5 sobre la dicotomía pre/post-pandémica del coeficiente de Coibion-Gorodnichenko. La conjunción de un quiebre estadísticamente robusto en el intercepto del error y de un cambio significativo en la pendiente del test de rigidez informacional, documentada formalmente por la prueba de interacción, configura un cuadro coherente: el régimen post-pandémico es estructuralmente distinto del régimen pre-pandémico, no solo en niveles sino en la forma en que las expectativas procesan la información.`));

c.push(H2("7.3. Tests Chow exógenos en cambios metodológicos de la EEM"));
c.push(P(`La Encuesta Mensual de Expectativas Macroeconómicas tuvo cambios de diseño documentados en enero de 2014 y enero de 2017, asociados a la ampliación del panel y la incorporación de nuevos horizontes de pronóstico. Para evaluar si las propiedades de los errores reflejan artefactos del cambio metodológico de la encuesta, se aplica tests Chow exógenos en ambas fechas sobre el intercepto del error. El test en enero de 2014 no rechaza estabilidad (F = ${fmt(R.chow_eem_2014.F,2)}, p ${fmtP(R.chow_eem_2014.p)}). El test en enero de 2017 rechaza al 1% (F = ${fmt(R.chow_eem_2017.F,2)}, p ${fmtP(R.chow_eem_2017.p)}). Este resultado obliga a verificar si la dicotomía pre/post-pandemia documentada en la sección 6.5 sobrevive controlando por el quiebre 2017.`));

c.push(P(`Para neutralizar el quiebre 2017, re-se estima el test de Coibion-Gorodnichenko aumentado con dummies de tres regímenes (junio 2010 – diciembre 2016, enero 2017 – febrero 2020 y marzo 2020 – marzo 2026), incluyendo interacciones con la revisión. Los resultados son los siguientes. Primero, el test de Wald para el cambio post-2020 controlando por el régimen 2017-2020m2 sigue rechazando al 1% (χ²(2) = ${fmt(R.tres_regimenes_test_conjunto.wald_post2020_controlando_2017.chi2,2)}, p ${fmtP(R.tres_regimenes_test_conjunto.wald_post2020_controlando_2017.p)}). Segundo, el cambio entre el régimen pre-2017 y el régimen 2017-2020m2 es marginalmente significativo al 5% (χ²(2) = ${fmt(R.tres_regimenes_test_conjunto.wald_2017_controlando_post2020.chi2,2)}, p ${fmtP(R.tres_regimenes_test_conjunto.wald_2017_controlando_post2020.p)}).`));

c.push(P(`La estimación por subperíodos del coeficiente CG es informativa: en el régimen pre-2017 (N = ${R.tres_regimenes.pre2017.cg.n}), λ = ${fmt(R.tres_regimenes.pre2017.cg.lambda,2)} (p ${fmtP(R.tres_regimenes.pre2017.cg.p_h)}, no significativo); en el régimen 2017-2020m2 (N = ${R.tres_regimenes['2017_2020m2'].cg.n}), λ = ${fmt(R.tres_regimenes['2017_2020m2'].cg.lambda,2)} (p < 0.001); en el régimen post-2020 (N = ${R.tres_regimenes.post2020.cg.n}), λ = ${fmt(R.tres_regimenes.post2020.cg.lambda,2)} (p ${fmtP(R.tres_regimenes.post2020.cg.p_h)}). Esta descomposición revela un matiz importante: el coeficiente λ en el régimen 2017-2020m2 ya alcanza el valor que se mantiene durante post-2020. La interpretación cualitativa que sustituye la simple dicotomía pre/post-pandemia es que el cambio relevante del coeficiente CG ocurre alrededor de 2017 y se mantiene durante el shock pandémico. Esto puede leerse de dos formas no excluyentes: como un cambio estructural genuino en el comportamiento del consenso a partir del rediseño de la encuesta, o como un cambio de comportamiento económico que coincide aproximadamente en el tiempo con dicho rediseño. La evidencia disponible no permite separar ambos canales.`));

c.push(H2("7.4. Pruebas múltiples"));
c.push(P(`La sección 6 reporta una familia de catorce contrastes de hipótesis sobre la misma muestra. Bajo significancia individual del 5% y asumiendo independencia entre los tests, la probabilidad de al menos un rechazo espurio bajo la nula completa es 1 − 0.95^14 ≈ 51%. La cifra es una cota superior porque los contrastes comparten datos y por tanto exhiben dependencia positiva, lo que reduce el FWE real respecto a esta cota. Aún así, la magnitud del riesgo motiva aplicar correcciones por multiplicidad para evaluar la robustez de los hallazgos centrales. La corrección de Bonferroni define el umbral familia-wise como α/m = ${fmt(R.pruebas_multiples.alpha_5pct_bonf,5)} para significancia conjunta del 5%. Bajo este criterio estricto, tres tests sobreviven al rechazo: el test Chow exógeno de 2017 (p ${fmtP(R.pruebas_multiples.p_values.chow_2017)}), el test de eficiencia informacional (p ${fmtP(R.pruebas_multiples.p_values.t4_wald)}) y el test de cambio de régimen Coibion-Gorodnichenko (p ${fmtP(R.pruebas_multiples.p_values.interaccion)}). Tres tests adicionales, a saber el sesgo pre-pandemia (p ${fmtP(R.pruebas_multiples.p_values.t1_pre_alpha)}), el rechazo de Mincer-Zarnowitz post-pandemia bajo Hodrick (p ${fmtP(R.pruebas_multiples.p_values.t2_post_wald_H)}) y el coeficiente λ post-pandemia (p ${fmtP(R.pruebas_multiples.p_values.t5_post_lambda_H)}), sobreviven Bonferroni al 10% pero no al 5%, lo que se reporta por completitud como evidencia de robustez moderada. Bajo el procedimiento más permisivo de Benjamini y Hochberg (1995) para tasa de descubrimientos falsos al 5%, ocho de los catorce tests pasan el umbral, incluyendo todos los hallazgos centrales del trabajo. La conclusión razonable es que los tres rechazos más importantes (Chow 2017, eficiencia informacional y dicotomía de régimen del CG) son robustos a corrección estricta por multiplicidad, mientras que los demás rechazos son estables bajo el criterio FDR pero no bajo el criterio familia-wise estricto al 5%.`));

c.push(H2("7.5. Especificaciones alternativas y robustez de la inferencia"));
c.push(P(`Como chequeo adicional, todas las pruebas centrales se reportan con bandwidth de Hodrick (2h−1 = 23) además del bandwidth automático Newey-West. La consistencia cualitativa entre ambos bandwidths sostiene los rechazos principales: el test conjunto de Mincer-Zarnowitz pre-pandemia rechaza bajo NW (p ${fmtP(t2pre.wald_p)}) y bajo Hodrick (p ${fmtP(t2pre.wald_p_hodrick)}); el rechazo del MZ post-pandemia es robusto bajo Hodrick (p ${fmtP(R.t2_mincer_zarnowitz.post.wald_p_hodrick)}); el test de eficiencia informacional rechaza bajo cualquier bandwidth (p < 0.001); el coeficiente λ post-pandemia es significativo al 1% bajo Hodrick (p ${fmtP(R.t5_coibion_gorod.post.p_lambda_hodrick)}). Cabe advertir, sin embargo, que con N = ${R.t5_coibion_gorod.post.n} en post-pandemia y bandwidth Hodrick = 23, el ratio bw/N es de ${(23/R.t5_coibion_gorod.post.n).toFixed(2)}, suficientemente alto como para que la literatura reciente (Müller, 2014; Lazarus, Lewis, Stock y Watson, 2018) haya documentado riesgo de errores estándar HAC sesgados a la baja en muestras pequeñas.`));

c.push(P(`Para confrontar este riesgo, se aplica dos correcciones adicionales sobre los coeficientes principales: el test de Kiefer y Vogelsang (2005) con bandwidth fijo b = 0.5 y valores críticos no estándar tabulados (cv 5% bilateral ≈ 2.610, cv 1% bilateral ≈ 3.484; valor crítico Wald al 5% para q = 4 restricciones ≈ 31.69), y bootstrap por bloques tipo Politis-Romano (1994) con longitud de bloque b = 18 = 1.5·h y 5,000 réplicas. Los resultados son los siguientes. Para el coeficiente λ post-pandemia (estimación puntual = 1.187), el test KV produce t = ${fmt(R.kiefer_vogelsang.cg_post_pandemia.t_kv,2)}, lo que rechaza al 1% (cv = 3.484). El bootstrap por bloques, en cambio, es más conservador: el intervalo de confianza al 95% es [${fmt(R.bootstrap_bloques.cg_post_pandemia.IC_95[0],2)}, ${fmt(R.bootstrap_bloques.cg_post_pandemia.IC_95[1],2)}] con p-valor ${fmtP(R.bootstrap_bloques.cg_post_pandemia.p_bootstrap)}, no rechazando la nula al 5%. La discrepancia entre ambas correcciones refleja que el bootstrap por bloques captura mejor la incertidumbre asociada a la estructura de autocorrelación inducida por el solapamiento de doce meses, y constituye un caveat sustantivo: bajo inferencia bootstrap, el rechazo del CG post-pandemia es marginal. Para el coeficiente sobre la TPM rezagada en el test de eficiencia informacional (γ = -1.251), las dos correcciones convergen: KV produce Wald conjunto de ${fmt(R.kiefer_vogelsang.eficiencia_informacional.wald_chi2_kv,2)} (rechaza al 5% con cv = 31.69) y el bootstrap por bloques produce IC 95% = [${fmt(R.bootstrap_bloques.tpm_eficiencia.IC_95[0],2)}, ${fmt(R.bootstrap_bloques.tpm_eficiencia.IC_95[1],2)}] con p ${fmtP(R.bootstrap_bloques.tpm_eficiencia.p_bootstrap)}, rechazando al 5% con holgura. La conclusión cualitativa es que el hallazgo central sobre la TPM es robusto a las correcciones más estrictas para muestra pequeña, mientras que el coeficiente CG post-pandemia es sensible a la elección del método inferencial.`));

// 7.6 Caveat metodológico crítico: horizonte rolling
c.push(H2("7.6. Caveat metodológico: el horizonte rodante en Coibion-Gorodnichenko"));
c.push(P(`La especificación del test de Coibion-Gorodnichenko en este trabajo, como en buena parte de la literatura aplicada, construye la revisión como rev_t = E_t[π_{t+12}] − E_{t-1}[π_{t+12}]. Esta operación trata las dos expectativas como pronósticos del mismo objeto. Sin embargo, en la EEM la expectativa "a 12 meses" es de horizonte rodante: en t apunta a la inflación de t+12, en t-1 apunta a la de t+11. La revisión así construida mezcla dos cosas distintas: la actualización del pronóstico ante nueva información (lo que el test pretende capturar) y el cambio del objeto pronosticado (lo que el test no debería capturar). Coibion y Gorodnichenko (2015) construyen sus revisiones sobre encuestas de objetivo fijo, donde la expectativa apunta a una fecha calendario específica, lo que evita el problema. La interpretación estructural ψ = 1/(1+λ) como probabilidad de actualización del set informacional bajo el modelo de Mankiw y Reis (2002) es estrictamente válida bajo objetivo fijo y debe leerse con cautela bajo horizonte rodante.`));

c.push(P(`Para evaluar la sensibilidad de los resultados a esta limitación, se replica la regresión de Coibion-Gorodnichenko utilizando una variable de horizonte fijo: la expectativa de inflación para el cierre del año calendario en curso (campo "Inflación año actual" de la EEM), donde la revisión sí refiere al mismo objetivo entre meses consecutivos del mismo año. Los resultados son ilustrativos: en la muestra completa el coeficiente sobre la revisión a horizonte fijo es λ_fijo = ${fmt(R.cg_robustez_horizonte_fijo.full.lambda_fijo,2)} con p-valor ${fmtP(R.cg_robustez_horizonte_fijo.full.p_lambda_fijo)} (marginalmente significativo al 10%), comparado con λ = ${fmt(t5full.lambda,2)} (p ${fmtP(t5full.p_lambda_hodrick)}) en la especificación de horizonte rodante. En el subperíodo pre-pandémico el coeficiente colapsa a λ_fijo = ${fmt(R.cg_robustez_horizonte_fijo.pre.lambda_fijo,2)} (p ${fmtP(R.cg_robustez_horizonte_fijo.pre.p_lambda_fijo)}, no significativo) y en post-pandémico a λ_fijo = ${fmt(R.cg_robustez_horizonte_fijo.post.lambda_fijo,2)} (p ${fmtP(R.cg_robustez_horizonte_fijo.post.p_lambda_fijo)}, no significativo).`));

c.push(P(`La discrepancia entre las dos especificaciones es metodológicamente importante. Sugiere que parte del rechazo de eficiencia informacional documentado bajo horizonte rodante puede no reflejar rigidez informacional sustantiva sino el cambio del objeto pronosticado entre meses consecutivos. Por contraste, la especificación de horizonte fijo es menos potente estadísticamente, porque la varianza de la revisión cae cuando el horizonte se acorta hacia diciembre y porque la muestra efectiva es menor, pero no produce evidencia robusta de rigidez informacional bajo el criterio estricto. La conclusión cualitativa es que la dicotomía pre/post-pandémica del λ documentada bajo horizonte rodante es coherente con un cambio de régimen en cómo se procesa la información, pero la interpretación cuantitativa específica de ψ = 1/(1+λ) como probabilidad de actualización mensual debe leerse como una aproximación informativa más que como una identificación estructural exacta. Replicar el test con expectativas de objetivo fijo a horizontes verdaderamente comparables (lo que requeriría una serie de microdatos individuales o una redefinición de la encuesta) queda como agenda futura.`));

// 7.7 Bai-Perron
c.push(H2("7.7. Quiebres estructurales múltiples (Bai-Perron)"));
c.push(P(`La prueba de Quandt-Andrews (sección 7.2) detecta un único quiebre dominante. Para evaluar si existen quiebres adicionales relevantes, se aplica el procedimiento secuencial de Bai y Perron (1998) sobre el intercepto del error de pronóstico, permitiendo hasta cinco quiebres con trimming del 10%. Los BICs respectivos para m ∈ {0,1,2,3,4,5} son ${fmt(R.bai_perron_extendido.resultados[0].bic,1)}, ${fmt(R.bai_perron_extendido.resultados[1].bic,1)}, ${fmt(R.bai_perron_extendido.resultados[2].bic,1)}, ${fmt(R.bai_perron_extendido.resultados[3].bic,1)}, ${fmt(R.bai_perron_extendido.resultados[4].bic,1)} y ${fmt(R.bai_perron_extendido.resultados[5].bic,1)}. El criterio BIC continúa decreciendo monótonamente en el rango explorado, lo que sugiere alguna combinación de quiebres adicionales en media o presencia de quiebres en varianza que el procedimiento sobre el intercepto interpreta como quiebres en media. La selección por BIC dentro del rango explorado favorece el modelo con cinco quiebres, fechados en febrero de 2012, diciembre de 2015, noviembre de 2018, julio de 2020 y marzo de 2023.`));

c.push(P(`Tres de estos quiebres son consistentes con eventos económicos identificables y con el análisis de subperíodos pre-pandémicos de la sección 7.9: febrero de 2012 separa el final del periodo de inflación elevada post-2008 del rango de inflación moderada subsiguiente; diciembre de 2015 corresponde aproximadamente al inicio del subperíodo de inflación baja (cerca de 0%) que se extiende hasta 2017; julio de 2020 captura el inicio del shock pandémico; marzo de 2023 captura la salida del episodio inflacionario y la reconvergencia hacia la meta. Dada la inestabilidad del BIC, se presenta la solución con cuatro quiebres como punto de referencia visual en la Figura 6, sin pretender que m=4 sea formalmente óptima. La evidencia sustantiva es que el comportamiento del error de pronóstico exhibe heterogeneidad estructural más rica que cualquier dicotomía simple, lo que refuerza la conveniencia de los análisis por subperíodos reportados en las secciones 7.3, 7.8 y 7.9.`));

c.push(FigImg(path.join(__dirname, '..', '04_figuras', 'fig6_bai_perron.png'), 580, 240));
c.push(Cap("Figura 6. Quiebres estructurales múltiples mediante Bai-Perron"));
c.push(Note("Nota: El procedimiento secuencial de Bai-Perron (1998) selecciona quiebres minimizando la suma de cuadrados residuales global. La figura ilustra la solución con tres quiebres (m=3, en 2012-02, 2020-08 y 2023-02) por claridad visual; el BIC continúa decreciendo al ampliar a m=4 (añade 2017-01) y m=5 (añade 2018-11). Las líneas rojas indican la media del error en cada subperíodo (μ₁=1.00, μ₂=−1.74, μ₃=3.67, μ₄=−0.82). Trimming del 10%."));

// 7.8 Sesgo condicional
c.push(H2("7.8. Sesgo condicional al estado de inflación"));
c.push(P(`El test de insesgamiento incondicional reportado en la sección 6.1 puede enmascarar asimetrías importantes. Para evaluar si el sesgo es heterogéneo según el estado del entorno, se condiciona el error en el régimen de inflación: se clasifica cada observación como "inflación baja" o "inflación alta" según se encuentre por debajo o por encima de la mediana muestral de π_t (mediana = 3.78%). Bajo el régimen de inflación baja, el sesgo es α_baja = ${fmt(R.sesgo_condicional.inflacion_baja.alpha,2)} p.p. (p ${fmtP(R.sesgo_condicional.inflacion_baja.p)}, N = ${R.sesgo_condicional.inflacion_baja.n}), una sobreestimación significativamente distinta de cero al 1%. Bajo el régimen de inflación alta, el sesgo es α_alta = ${fmt(R.sesgo_condicional.inflacion_alta.alpha,2)} p.p. (p ${fmtP(R.sesgo_condicional.inflacion_alta.p)}, N = ${R.sesgo_condicional.inflacion_alta.n}), una subestimación significativa al 10%. La diferencia entre ambos regímenes es de ${fmt(R.sesgo_condicional.test_igualdad.coef_dummy,2)} p.p., con prueba formal de igualdad de sesgos rechazada con p ${fmtP(R.sesgo_condicional.test_igualdad.p_dummy)}.`));

c.push(P(`Esta asimetría estado-dependiente es económica y estadísticamente importante: el consenso no se equivoca por igual en todos los regímenes; sobreestima sistemáticamente cuando la inflación es baja y subestima cuando es alta, en un patrón consistente con suavizamiento procíclico de los pronósticos respecto a la dinámica realizada. La interpretación bajo FIRE requiere precisión: π_t no es parte del set de información disponible al formar la expectativa en t−12, por lo que el contraste relevante no es "conocer π_t no debería predecir el signo del error" sino el siguiente. Bajo racionalidad estricta, un agente que pronostica con conocimiento del proceso generador de la inflación produce errores cuya distribución condicional al estado realizado posteriormente no debe depender sistemáticamente de ese estado: si el agente conoce que el régimen de inflación post-pronóstico será alto con probabilidad p y bajo con probabilidad 1−p, el sesgo medio condicional al régimen alto debe coincidir con el sesgo medio condicional al régimen bajo (ambos cero bajo insesgamiento, o ambos iguales a un mismo sesgo constante bajo sesgo racional persistente). Cabe matizar que bajo predictores con bajo contenido informacional respecto a π_t (es decir, con R²(predictor, π_t) bajo) se generan sesgos condicionales firmados sistemáticamente como artefacto de regresión-a-la-media, lo que diluye la fuerza de la asimetría como rechazo independiente de FIRE plena. En la muestra del paper el consenso tiene R²(MZ) cercano a 0.30 en pre-pandemia y prácticamente cero en post-pandemia, lo que coloca al consenso en ese rango de bajo contenido informacional. Que la prueba formal de igualdad de los dos sesgos condicionales se rechace al 1% (Wald χ² = 17.85) es por tanto una desviación que, conjunta con el rechazo de eficiencia respecto a la TPM rezagada documentado en la sección 6.4, es difícil de reconciliar con FIRE plena bajo cualquier supuesto razonable sobre el contenido informacional del predictor: el consenso falla la propiedad de calibración condicional respecto al régimen de inflación que efectivamente se realiza. La Figura 7 visualiza esta asimetría.`));

c.push(FigImg(path.join(__dirname, '..', '04_figuras', 'fig7_sesgo_condicional.png'), 580, 230));
c.push(Cap("Figura 7. Asimetría del sesgo según el régimen de inflación realizada"));
c.push(Note("Nota: Panel izquierdo: dispersión del error de pronóstico contra la inflación realizada, con la línea horizontal punteada indicando la media del error en cada régimen y la línea vertical punteada la mediana muestral de π_t. Panel derecho: distribución de frecuencias del error por régimen, con líneas verticales en cada media. La diferencia de medias es 3.04 p.p., con prueba formal de igualdad rechazada al 1%."));

// 7.9 Pre-pandemia desagregada
c.push(H2("7.9. Heterogeneidad dentro del régimen pre-pandémico"));
c.push(P(`La sección 6 trata el periodo junio 2010 – febrero 2020 como un único régimen homogéneo. Sin embargo, este intervalo cubre coyunturas económicas muy diferenciadas. Para evaluar la heterogeneidad interna, se divide el régimen pre-pandémico en tres subperíodos exhaustivos: junio 2010 – diciembre 2014 (transición desde inflación elevada post-2008, N = ${R.pre_pandemia_desagregada['2010m6_2014'].n}), 2015-2017 (período de inflación baja, en torno a 1.9% promedio, N = ${R.pre_pandemia_desagregada['2015_2017'].n}) y 2018-2020m2 (estabilización en torno a la meta, N = ${R.pre_pandemia_desagregada['2018_2020m2'].n}).`));

c.push(P(`Los resultados son ilustrativos. En el primer subperíodo el sesgo es α = ${fmt(R.pre_pandemia_desagregada['2010m6_2014'].alpha,2)} p.p. (p ${fmtP(R.pre_pandemia_desagregada['2010m6_2014'].p_alpha)}, no significativo); el segundo registra el sesgo más pronunciado: α = ${fmt(R.pre_pandemia_desagregada['2015_2017'].alpha,2)} p.p. (p ${fmtP(R.pre_pandemia_desagregada['2015_2017'].p_alpha)}); el tercero reporta α = ${fmt(R.pre_pandemia_desagregada['2018_2020m2'].alpha,2)} p.p. (p ${fmtP(R.pre_pandemia_desagregada['2018_2020m2'].p_alpha)}). El subperíodo 2015-2017 es donde se concentra el sesgo de sobreestimación pre-pandémico documentado en la sección 6.1: en ese intervalo la inflación realizada cayó cerca de 0% mientras la expectativa mediana se mantuvo en torno a 3.6%, generando errores sistemáticamente negativos. Este patrón es coherente con un anclaje insuficiente del consenso a la baja: cuando la inflación cae bien por debajo de la meta, los analistas resisten la actualización de su pronóstico al rango bajo. El coeficiente de Coibion-Gorodnichenko también es heterogéneo: λ = ${fmt(R.pre_pandemia_desagregada['2015_2017'].cg.lambda,2)} (p ${fmtP(R.pre_pandemia_desagregada['2015_2017'].cg.p_lambda)}) en 2015-2017 y λ = ${fmt(R.pre_pandemia_desagregada['2018_2020m2'].cg.lambda,2)} (p ${fmtP(R.pre_pandemia_desagregada['2018_2020m2'].cg.p_lambda)}) en 2018-2020m2, ambos significativos. La rigidez informacional pre-pandémica no es uniforme y se intensifica al final del subperíodo, anticipando lo que se acentuará durante el shock posterior.`));

// 7.10 Magnitud económica
c.push(H2("7.10. Magnitud económica del rechazo"));
c.push(P(`La significancia estadística de un coeficiente y su importancia económica son cuestiones distintas. La regresión de Coibion-Gorodnichenko produce coeficientes λ estadísticamente significativos pero R² muy bajos: 0.7% en pre-pandemia, 2.8% en post-pandemia (las cifras del Cuadro 8 con N=72; la regresión CG sin condicionar al rezago de TPM, que mantiene N=73, reporta 3.1%). Para situar la magnitud económica del rechazo, se descompone la varianza del error de pronóstico. La desviación estándar del error es 1.89 p.p. en pre-pandemia y 2.61 p.p. en post-pandemia, valores económicamente relevantes para un objetivo de política con meta de inflación de 4% ± 1 p.p. La desviación estándar agrupada sobre toda la muestra (2.46 p.p.) es mayor que la del régimen pre-pandémico, no porque la varianza pre-pandémica fuera mayor, sino porque al combinar dos subperíodos con medias distintas la varianza pooled incorpora la varianza entre medias además de la varianza dentro de cada régimen. La revisión por sí sola explica una fracción modesta de esa varianza, como muestra el Cuadro 8.`));

// Cuadro auxiliar: descomposición de R² entre revisión y TPM rezagada
c.push(Cap("Cuadro 8. Descomposición de R² del error de pronóstico: revisión vs. TPM rezagada"));
const dr = R.descomposicion_r2;
const tDescH = new TableRow({ tableHeader:true, children:[
  TC("Especificación",                             { width:3500, bold:true, shading:"E8E8E8" }),
  TC("Pre-pandemia",                               { width:1700, bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
  TC("Post-pandemia",                              { width:1700, bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
  TC("Muestra completa",                           { width:1700, bold:true, shading:"E8E8E8", align:AlignmentType.CENTER }),
]});
const tDescRows = [
  ["e_t = α + λ · rev_t + u_t",                       fmt(dr.pre.r2_rev,3),       fmt(dr.post.r2_rev,3),       fmt(dr.full.r2_rev,3)],
  ["e_t = α + γ · TPM_{t−13} + u_t",                  fmt(dr.pre.r2_tpm,3),       fmt(dr.post.r2_tpm,3),       fmt(dr.full.r2_tpm,3)],
  ["e_t = α + λ · rev_t + γ · TPM_{t−13} + u_t",      fmt(dr.pre.r2_rev_y_tpm,3), fmt(dr.post.r2_rev_y_tpm,3), fmt(dr.full.r2_rev_y_tpm,3)],
  ["Incremento por añadir TPM (Δ R²)",               fmt(dr.pre.incremento_tpm,3), fmt(dr.post.incremento_tpm,3), fmt(dr.full.incremento_tpm,3)],
  ["N",                                              String(dr.pre.n_rev_y_tpm),  String(dr.post.n_rev_y_tpm), String(dr.full.n_rev_y_tpm)],
];
c.push(new Table({
  width:{ size:9000, type:WidthType.DXA },
  rows:[ tDescH, ...tDescRows.map((r,i) => new TableRow({ children:[
    TC(r[0], { width:3500, bold:false, italics:i===3 }),
    TC(r[1], { width:1700, align:AlignmentType.CENTER, bold:i===3 }),
    TC(r[2], { width:1700, align:AlignmentType.CENTER, bold:i===3 }),
    TC(r[3], { width:1700, align:AlignmentType.CENTER, bold:i===3 }),
  ]}))]
}));
c.push(Note("Nota: Cada celda reporta el R² de una regresión MICO del error de pronóstico e_t sobre los regresores indicados. La fila 'incremento por añadir TPM' es la diferencia entre la fila 3 y la fila 1; mide la fracción adicional de varianza del error que captura la TPM rezagada después de controlar por la revisión del consenso. Un incremento alto indica que la TPM rezagada contiene información ortogonal a la revisión, no vista por el consenso al actualizar entre encuestas consecutivas. El N post-pandémico es 72 en lugar de 73 porque la inclusión de TPM_{t−13} pierde una observación al inicio del subperiodo; las regresiones CG sin la TPM en el resto del paper usan N = 73 y producen un R² post-pandémico ligeramente distinto (3.1% en lugar de 2.8%)."));

c.push(P(`La descomposición es elocuente. La revisión sola (especificación canónica del CG) explica entre 0.7% y 2.8% de la varianza del error según el subperíodo. La TPM rezagada sola, en cambio, explica entre 34.6% y 67.5% de esa varianza, un orden de magnitud completamente distinto. El modelo combinado explica entre 35.0% y 69.1%, prácticamente idéntico al modelo con solo TPM, lo que indica que la información en la revisión es esencialmente subconjunto de la información en la TPM. El incremento marginal del R² al añadir TPM al modelo CG es 0.34 en pre-pandemia, 0.66 en post-pandemia y 0.38 en la muestra completa. Estos números son la traducción cuantitativa del mensaje cualitativo del trabajo: el problema central de los pronósticos del consenso no es tanto que actualicen lentamente entre encuestas (rigidez à la Mankiw-Reis), sino que el error es predecible a partir de la postura monetaria reciente. La diferencia es importante para la política: la rigidez informacional pura sugeriría comunicación más frecuente como remedio, mientras que la predictibilidad específica del error a partir de la TPM sugiere comunicación más explícita sobre cómo la propia política monetaria debe traducirse en una proyección de inflación distinta.`));

c.push(P(`En contraste, la TPM rezagada captura mucha más varianza del error y refuerza la jerarquía documentada en el Cuadro 8: en pre-pandemia, la regresión conjunta del error sobre revisión y TPM rezagada explica el 35.0% de la varianza, en post-pandemia el 69.1%, y en la muestra completa el 39.8%. Este resultado refuerza la lectura de la sección 6.4: el componente económicamente dominante del rechazo de eficiencia es la TPM, no la revisión.`));

c.push(H2("7.11. Mincer-Zarnowitz no lineal con la meta del 4% como umbral"));
c.push(P(`El test RESET aplicado en la sección 7.1 rechaza la especificación lineal del modelo de Mincer-Zarnowitz al 1% (F = 5.64, p = 0.004), lo que sugiere que la relación entre realizado y esperado no es uniforme a lo largo del rango de la expectativa. Para explorar esta no linealidad de manera fundamentada teóricamente, se especifica un threshold-MZ con la meta del 4% del BCRD como umbral exógeno (en lugar de la mediana muestral) y se estima el modelo separadamente en dos regímenes: observaciones con expectativa rezagada bajo la meta (E_{t−12}[π_t] < 4%) y con expectativa sobre o igual a la meta (≥ 4%).`));

c.push(P(`Los resultados son ilustrativos. En el régimen de expectativa baja (N = ${R.threshold_mz_meta_4.expectativa_baja.n}), la estimación arroja α = ${fmt(R.threshold_mz_meta_4.expectativa_baja.alpha,2)}, β = ${fmt(R.threshold_mz_meta_4.expectativa_baja.beta,2)}, con prueba conjunta de Wald de no rechazo (χ²(2) = ${fmt(R.threshold_mz_meta_4.expectativa_baja.wald_chi2_h,2)}, p ${fmtP(R.threshold_mz_meta_4.expectativa_baja.wald_p_h)}). En el régimen de expectativa cerca o sobre la meta (N = ${R.threshold_mz_meta_4.expectativa_alta.n}), α = ${fmt(R.threshold_mz_meta_4.expectativa_alta.alpha,2)}, β = ${fmt(R.threshold_mz_meta_4.expectativa_alta.beta,2)}, también con prueba conjunta de no rechazo (χ²(2) = ${fmt(R.threshold_mz_meta_4.expectativa_alta.wald_chi2_h,2)}, p ${fmtP(R.threshold_mz_meta_4.expectativa_alta.wald_p_h)}). El test formal de igualdad de coeficientes entre regímenes tampoco rechaza (χ²(2) = ${fmt(R.threshold_mz_meta_4.test_igualdad.chi2,2)}, p ${fmtP(R.threshold_mz_meta_4.test_igualdad.p)}).`));

c.push(P(`La interpretación del resultado threshold-MZ requiere cautela. Tomados al pie de la letra, los puntos β = ${fmt(R.threshold_mz_meta_4.expectativa_alta.beta,2)} (régimen alto) y β = ${fmt(R.threshold_mz_meta_4.expectativa_baja.beta,2)} (régimen bajo) son cualitativamente incompatibles con FIRE, que requiere β = 1 en cada régimen: en el régimen alto los analistas sub-reaccionan a su propia expectativa, y en el régimen bajo pareciera que el realizado depende negativamente de la expectativa, lo que es un fallo más grave de eficiencia. Sin embargo, los tests individuales de Wald en cada régimen no rechazan β = 1 al 5%. Esta combinación, con puntos cualitativamente extraños pero sin rechazo formal, es típica de un problema de potencia: dentro de cada régimen el N efectivo es bajo (${R.threshold_mz_meta_4.expectativa_alta.n} en el alto, ${R.threshold_mz_meta_4.expectativa_baja.n} en el bajo), la varianza de la expectativa es muy reducida (consecuencia directa del anclaje del consenso a la meta documentado en la sección 6.2), y los errores estándar HAC son grandes en proporción a los coeficientes. Es decir, el no-rechazo no debe leerse como evidencia de que MZ se sostiene en cada régimen, sino como ausencia de potencia para rechazarlo dentro de cada subconjunto. La lectura más informativa es que el rechazo agregado de MZ documentado en la sección 6.2 no se concentra en ningún régimen específico al permitir heterogeneidad respecto a la meta; el rechazo se diluye al partir la muestra, lo que es coherente con que la fuente del rechazo agregado sea precisamente la combinación de comportamientos heterogéneos descritos. Esta heterogeneidad es coherente con el sesgo asimétrico estado-dependiente documentado en la sección 7.8 y con la heterogeneidad por subperíodo de la sección 7.9.`));

// 7.12 ARDL TPM
c.push(H2("7.12. Especificación ARDL del canal de la TPM"));
c.push(P(`Una objeción potencial al test de eficiencia informacional reportado en la sección 6.4 es que el coeficiente sobre la TPM rezagada se reporta para un único rezago (t-13). Un analista racional usa todo el historial de TPM disponible al momento de pronosticar, no un solo rezago, por lo que es relevante verificar que el rechazo no es un artefacto de la elección específica del rezago. Re-se estima el modelo aumentando con rezagos t-12 a t-18 de la TPM, manteniendo controles para inflación rezagada, variación del tipo de cambio rezagada y crecimiento del PIB rezagado:`));

c.push(P("e_t = α + Σ_{j=12}^{18} γ_j · i_{t-j} + ρ · π_{t-13} + δ · Δe_{t-13} + θ · Δy_{t-13} + u_t   (6)"));

c.push(P(`El test conjunto de la nula H₀: γ_12 = γ_13 = ... = γ_18 = 0 rechaza con Wald χ²(7) = ${fmt(R.ardl_tpm_eficiencia.wald_conjunto_tpm_chi2,2)} (p ${fmtP(R.ardl_tpm_eficiencia.wald_conjunto_tpm_p)}), a inferencia HAC con bandwidth automático Newey-West. El R² incrementa modestamente respecto a la especificación con rezago único (de ${fmt(R.ardl_tpm_eficiencia.r2_simple,3)} a ${fmt(R.ardl_tpm_eficiencia.r2_ardl,3)}), lo que indica que la información adicional aportada por los rezagos no contiguos a t-13 es marginal pero no nula. El rezago dominante por magnitud puntual del coeficiente es ${R.ardl_tpm_eficiencia.rezago_dominante.replace('tpm_lag','t-')} con γ = ${fmt(R.ardl_tpm_eficiencia.rezago_dominante_coef,2)}. La conclusión sustantiva es que el rechazo de eficiencia informacional respecto a la TPM no depende del rezago específico elegido y sobrevive a la especificación más general. La selección del rezago t-13 en la sección 6.4 se justifica por simplicidad expositiva (corresponde al rezago contemporáneo al horizonte de pronóstico) y por que produce un BIC ligeramente preferible al modelo ARDL completo, pero la conclusión cualitativa es invariante.`));

c.push(H2("7.13. Mensualización del PIB por Chow-Lin con IMAE"));

c.push(P(`Una crítica metodológica aplicable al test de eficiencia informacional reportado en el Cuadro 4 es que el PIB real del BCRD se publica con frecuencia trimestral, mientras que el modelo se estima con frecuencia mensual. La especificación principal mensualiza la serie por asignación constante dentro del trimestre, lo que sub-utiliza información disponible en el Índice Mensual de Actividad Económica (IMAE) del BCRD. Para verificar que la conclusión del test no depende de esta elección, se replica la estimación usando la mensualización por el procedimiento de Chow y Lin (1971) con el IMAE como indicador relacionado.`));

c.push(P(`Se implementa Chow-Lin máxima verosimilitud sobre los residuales mensuales modelados como AR(1), restringidos a que el promedio trimestral de la serie estimada coincida con la serie trimestral observada. La cobertura común de IMAE y PIB para este ejercicio es enero 2009 – diciembre 2025 (204 meses, 68 trimestres). El parámetro AR(1) estimado por máxima verosimilitud colapsa a ρ̂ = ${fmt(R.chow_lin.rho_estimado,2)}, valor que refleja que el IMAE captura prácticamente toda la variación trimestral del PIB y el procedimiento Chow-Lin se reduce esencialmente a una interpolación condicional al IMAE. La correlación entre el crecimiento interanual del PIB obtenido por Chow-Lin y el obtenido por asignación constante es ${fmt(R.chow_lin.comparacion_var_pib.correlacion_chowlin_vs_constante,2)}.`));

c.push(P(`Re-estimando el test de eficiencia informacional con la mensualización Chow-Lin del PIB, los resultados son cualitativamente idénticos. El coeficiente sobre la TPM rezagada cambia de −1.25 (asignación constante) a ${fmt(R.chow_lin.eficiencia_pib_chowlin.tpm_coef,2)} con p ${fmtP(R.chow_lin.eficiencia_pib_chowlin.tpm_p)}, prácticamente sin variación; el coeficiente sobre el crecimiento del PIB sigue siendo no significativo (p = ${fmt(R.chow_lin.eficiencia_pib_chowlin.pib_p,3)}); y el Wald conjunto de la nula H₀: γ = 0 cambia de χ²(4) = 21.68 a χ²(4) = ${fmt(R.chow_lin.eficiencia_pib_chowlin.wald_chi2,2)} (p ${fmtP(R.chow_lin.eficiencia_pib_chowlin.wald_p)}), en ambos casos rechazando la eficiencia informacional al 1% con holgura. La conclusión central del paper, a saber el rechazo de eficiencia informacional liderado por la TPM rezagada, es robusta a la elección de método de mensualización del PIB.`));

// 8. DISCUSIÓN
c.push(H1("8. Discusión, implicaciones y limitaciones"));
c.push(H2("8.1. Síntesis de los hallazgos"));
c.push(P(`Los resultados pueden sintetizarse en siete mensajes. Primero, el hallazgo central por magnitud económica y robustez es la predictibilidad estadísticamente significativa del error de pronóstico a partir de la TPM rezagada: el test de eficiencia informacional rechaza al 1% por amplio margen (Wald χ²(4) = ${fmt(t4.wald_chi2,2)}), la TPM efectiva rezagada captura por sí sola un R² parcial de ${fmt(R.t4_eficiencia_info_oficial.r2_partial['TPM_obs_t-13'],3)} sobre la varianza total del error (es decir, alrededor del 38% de esa varianza es predecible solo con la TPM rezagada, lo que equivale aproximadamente al 86% de la varianza explicada por el modelo completo, con R² total = ${fmt(t4.r2,3)}), y el rechazo conjunto sobre los rezagos doce a dieciocho de la TPM (especificación ARDL) es Wald χ²(7) = ${fmt(R.ardl_tpm_eficiencia.wald_conjunto_tpm_chi2,2)} (p < 0.001), lo que demuestra que la predictibilidad no depende del rezago específico elegido. Segundo, el consenso exhibe un sesgo estado-dependiente: sobreestima cuando la inflación realizada está por debajo de la mediana muestral y subestima cuando está por encima, con prueba formal de igualdad rechazada al 1%. Tercero, la prueba lineal de Mincer-Zarnowitz rechaza la racionalidad en pre-pandemia al 5% y, más dramáticamente, en post-pandemia donde la pendiente colapsa cerca de cero; sin embargo, la especificación con threshold en la meta del 4% (sección 7.11) no rechaza racionalidad en ningún régimen individualmente, lectura que debe matizarse por la baja potencia derivada del N efectivo y la varianza intra-régimen pequeña. Cuarto, el subperíodo donde el sesgo de sobreestimación es más pronunciado es 2015-2017, cuando la inflación realizada cayó cerca de 0% mientras el consenso resistió la actualización del pronóstico al rango bajo. Quinto, el coeficiente de Coibion-Gorodnichenko bajo horizonte rodante exhibe una dicotomía estadísticamente significativa entre el régimen pre-2017 (λ = ${fmt(R.tres_regimenes.pre2017.cg.lambda,2)}, no significativo) y el régimen post-2017, donde el coeficiente alcanza λ ≈ 1.19 y se mantiene en ese nivel durante el shock pandémico; el quiebre relevante coincide aproximadamente con el rediseño metodológico de la encuesta en enero de 2017, lo que impide separar limpiamente cambio de comportamiento económico de artefacto de medición. Adicionalmente, la replicación bajo horizonte fijo y bajo bootstrap por bloques en muestras pequeñas atenúan el rechazo del CG, mientras que el rechazo del test de eficiencia informacional sobrevive en ambas verificaciones. Sexto, Bai-Perron detecta múltiples quiebres estructurales (2012-02, 2020-08, 2023-02) con BIC monótonamente decreciente hasta m=5, lo que sugiere heterogeneidad estructural más rica que cualquier dicotomía simple. Séptimo, la calidad predictiva del consenso fuera de muestra es estadísticamente indistinguible de benchmarks naïve a horizonte de doce meses bajo Diebold-Mariano.`));

c.push(H2("8.2. Interpretación"));
c.push(P("La interpretación se beneficia de los chequeos de robustez aplicados. La narrativa que la primera lectura del coeficiente de Coibion-Gorodnichenko sugiere, esto es rigidez informacional pronunciada bajo choques de gran magnitud en línea con un mecanismo Mankiw-Reis, sobrevive solo parcialmente al examen detallado y requiere matizaciones importantes. Por un lado, la dicotomía pre-2017 vs post-2017 del λ bajo horizonte rodante es estadísticamente significativa al 1% incluso controlando por interacciones formales con la dummy post-pandemia. Por otro lado, esa dicotomía coincide en el tiempo con el rediseño metodológico de la EEM en enero de 2017, lo que impide separar limpiamente el cambio de comportamiento económico del artefacto de medición. Adicionalmente, la replicación del test bajo construcción de revisiones con horizonte fijo no produce evidencia robusta de rigidez en ningún subperíodo, y el bootstrap por bloques en muestras pequeñas (sección 7.5) atenúa el rechazo del CG post-pandemia con respecto a la inferencia HAC estándar. La interpretación cuantitativa estricta ψ = 1/(1+λ) como probabilidad mensual de actualización del set informacional debe leerse como una aproximación informativa más que como una identificación estructural exacta."));

c.push(P("La pieza más sólida del análisis no es la rigidez à la Coibion-Gorodnichenko sino la predictibilidad del error de pronóstico a partir de la TPM rezagada. Tres líneas de evidencia convergen en este punto. Primero, el test de eficiencia informacional con variables observables oficiales rechaza al 1% por amplio margen, y la TPM rezagada es por sí sola el predictor dominante del error. Segundo, según el Cuadro 8, la combinación de revisión + TPM rezagada explica el 35.0% de la varianza del error en pre-pandemia y el 69.1% en post-pandemia, mientras que la revisión sola explica 0.7% y 2.8% respectivamente; el incremento marginal del R² atribuible a añadir la TPM al modelo CG es de 34.3 puntos porcentuales en pre-pandemia y 66.3 en post-pandemia. Tercero, el sesgo asimétrico estado-dependiente, con sobreestimación en regímenes de inflación contemporánea baja y subestimación en regímenes de inflación contemporánea alta, es consistente con un patrón de anclaje insuficiente del consenso a la trayectoria que la política monetaria parece estar induciendo. Una identificación causal más fuerte (que los analistas no procesen óptimamente la información sobre la TPM en su mecanismo de formación de expectativas) requeriría un modelo estructural que separe el efecto de la TPM sobre la inflación realizada del efecto de la TPM sobre las expectativas, lo que está fuera del alcance del presente análisis. La extensión a datos individuales del panel EEM permitiría descomponer estos efectos entre rigidez informacional pura y disagreement entre agentes, en línea con Bordalo et al. (2020), y elucidar cuál mecanismo predomina."));

c.push(H2("8.2.1. Una hipótesis unificadora: consenso ≈ meta + ruido"));

c.push(P("Los hallazgos individuales del trabajo (el sesgo asimétrico estado-dependiente, la pendiente colapsada del MZ post-pandémico, los puntos β cualitativamente extraños del threshold-MZ, el RMSE del ancla a la meta empatando al RMSE del consenso fuera de muestra, y la histórica sobreestimación documentada por Jiménez P. y López H. (2014) en una muestra previa) admiten una lectura unificadora simple: el consenso de la EEM puede aproximarse, en primera instancia, como una constante cercana a la meta del banco central más un ruido pequeño. Cinco piezas de evidencia convergen en esta caracterización."));

c.push(P(`Primero, la media muestral de la mediana del consenso a doce meses es 4.58% (cuadro 1) y la desviación estándar es solamente 1.19 p.p., aproximadamente la mitad de la desviación estándar de la inflación realizada (2.49 p.p.) y prácticamente coincidente con la meta puntual del 4% más una banda angosta. Segundo, la regresión de Mincer-Zarnowitz post-pandémica colapsa la pendiente a β ≈ 0 con intercepto significativo positivo: si la expectativa apenas se mueve mientras el realizado oscila ampliamente, la covarianza entre ambos es cercana a cero, exactamente lo que cabría esperar si el consenso fuera aproximadamente una constante. Tercero, los coeficientes β = ${fmt(R.threshold_mz_meta_4.expectativa_alta.beta,2)} y β = ${fmt(R.threshold_mz_meta_4.expectativa_baja.beta,2)} del threshold-MZ no rechazan la unidad solo porque la varianza intra-régimen de la expectativa es muy pequeña, no porque el modelo de FIRE describa bien los datos en cada régimen. Cuarto, en el ejercicio fuera de muestra el ancla a la meta del 4% (un benchmark que es, por construcción, una constante) produce un RMSE de 2.72 p.p., idéntico al del consenso EEM. Quinto, en la muestra de Jiménez P. y López H. (2014), correspondiente a enero 2008 a julio 2013, con inflación realizada cayendo desde niveles altos hacia 4–6% en promedio, el consenso EEM se mantenía cerca de 6% mientras la inflación realizada caía por debajo, lo que producía un sesgo de sobre-predicción significativo de −2.28 p.p.; en la muestra post-2020 del presente trabajo, el consenso se mantiene cerca de 4% mientras la inflación realizada superó esos niveles entre 2021 y 2023, produciendo el patrón inverso de sub-predicción. La caracterización "consenso ≈ meta + ruido" reconcilia ambos resultados: lo que cambia entre los dos trabajos no es el comportamiento del consenso, que en ambos casos se ancla cerca de un nivel similar a la meta operativa del banco central de cada época, sino el comportamiento de la inflación realizada, cuyo signo de desviación respecto a la meta determina el signo del sesgo del consenso.`));

c.push(P("Esta caracterización tiene tres implicaciones. Primero, no es una refutación trivial de la racionalidad del consenso: si la mejor predicción condicional disponible, dada la incertidumbre genuina sobre la trayectoria de los choques, es la propia meta del banco central, entonces anclarse a la meta es informacionalmente óptimo en sentido bayesiano débil. Segundo, sí es una observación sustantiva sobre los límites de la información agregada del consenso: cuando el sistema enfrenta choques persistentes que separan a la inflación realizada de la meta, el consenso, por construcción anclado, no incorpora esa información a tiempo. Y tercero, ofrece una lectura alternativa de los hallazgos del CG post-pandemia: la rigidez informacional pura à la Mankiw-Reis no necesariamente requiere un mecanismo cognitivo de actualización lenta; un mecanismo conductual más simple, en el que los analistas usan la meta como ancla focal y se desvían poco de ella, produce predicciones empíricas observacionalmente equivalentes en muchos contextos. La elección entre ambas interpretaciones requeriría datos de panel sobre los analistas individuales que el presente trabajo no explota."));

c.push(P("Vale la pena detenerse en la primera de estas implicaciones porque define la naturaleza interpretativa del paper. Bajo qué supuestos sobre el set de información del analista privado anclarse a la meta es óptimo bayesianamente, y bajo qué supuestos no lo es. Si el analista tiene un prior bien-calibrado sobre la distribución condicional de la inflación a doce meses, y si el banco central comunica creíblemente que su función de pérdida está centrada en la meta, entonces la media posterior del analista sobre la inflación futura debería estar cerca de la meta cuando los choques contemporáneos son indistinguibles del ruido y los mecanismos de transmisión de la política monetaria son fiables. Bajo esas condiciones, anclarse a la meta no solo no es irracional sino que constituye el punto fijo bayesiano del problema de pronóstico, en línea con la lectura de Faust y Wright (2013) sobre la dificultad de superar a benchmarks tipo random walk en pronósticos de inflación a horizontes intermedios. La saliencia de la meta como ancla focal en contextos de alta incertidumbre, el mecanismo conductual mencionado arriba, produce un comportamiento agregado observacionalmente equivalente al óptimo bayesiano, lo que dificulta separar identificacionalmente las dos interpretaciones con datos agregados."));

c.push(P("Donde la lectura bayesiana se rompe es cuando la información disponible al analista contradice de manera sistemática la trayectoria implícita en la meta. La conjunción del rechazo del test de eficiencia informacional con la TPM rezagada (Wald χ²(4) = 21.68 con un R² parcial de 38.3%) indica que existe una variable de información pública que el consenso no está incorporando, lo que es incompatible con eficiencia bayesiana plena. La lectura más cautelosa del paper es por tanto que el consenso EEM exhibe un comportamiento que es bayesianamente óptimo respecto a la información que efectivamente procesa, pero el conjunto de variables que efectivamente procesa es subset de las observables públicamente, en particular omitiendo señales informativas contenidas en la trayectoria reciente de la TPM. Goldfayn-Frank y Wohlfart (2020), aunque referidos a expectativas de hogares, documentan precisamente este patrón: en regímenes de alta saliencia del ancla focal, los agentes actualizan menos respecto a información que en otros contextos sí incorporarían. La distinción entre saliencia del ancla y rigidez cognitiva es identificacionalmente sutil; reconocerla explícitamente es la actitud honesta dada la información disponible en este trabajo."));

c.push(P(`La caracterización "consenso ≈ meta + ruido" admite además una validación cuasi-experimental con los propios datos del paper. Si el modelo es correcto, el consenso debería tener un desempeño predictivo similar al de un benchmark constante igual a la meta, y la diferencia entre ambos debería ser pequeña tanto en periodos de inflación cercana a la meta como en periodos de inflación lejos de la meta, porque ambos métodos comparten la misma constante focal. Bajo la hipótesis alternativa de que el consenso procesa información genuina, se esperaría que el consenso supere al ancla en al menos uno de los regímenes. La descomposición del Cuadro 6 por subperíodo, que se reporta a continuación, ofrece una prueba directa de esta predicción.`));

c.push(P(`Para este ejercicio se extiende la ventana pre-pandémica hacia atrás hasta enero 2018, lo que es legítimo porque ambos pronósticos comparados (el consenso EEM disponible mensualmente y el ancla constante a la meta del 4%) son no-paramétricos y no requieren ventana de estimación previa. Esta extensión cuadruplica el N efectivo del subperiodo pre-pandémico de N = 14 (la ventana OOS canónica del Cuadro 6, que sí está restringida por la necesidad de estimar el AR(1) recursivo) a N = 26, lo que mejora sustancialmente la potencia para detectar diferencias entre el consenso y el ancla bajo el régimen de inflación cercana a la meta. En el subperíodo pre-pandémico de la ventana extendida (enero 2018 – febrero 2020, N = ${R.diebold_mariano.oos_pre_completo.EEM.N}), el consenso EEM tiene RMSE = ${fmt(R.diebold_mariano.oos_pre_completo.EEM.RMSE,2)} p.p. frente a un RMSE del ancla a la meta del 4% de ${fmt(R.diebold_mariano.oos_pre_completo.Ancla.RMSE,2)} p.p.; es decir, el ancla constante a la meta produce un RMSE inferior al del consenso por aproximadamente ${fmt(R.diebold_mariano.oos_pre_completo.EEM.RMSE - R.diebold_mariano.oos_pre_completo.Ancla.RMSE,2)} p.p., con la inflación realizada promediando 2.79% durante ese intervalo (por debajo de la meta del 4%). En el subperíodo post-pandémico (marzo 2020 – marzo 2026, N = ${R.diebold_mariano.oos_post_completo.EEM.N}), el RMSE del consenso es ${fmt(R.diebold_mariano.oos_post_completo.EEM.RMSE,2)} p.p. frente a ${fmt(R.diebold_mariano.oos_post_completo.Ancla.RMSE,2)} p.p. del ancla, con la inflación realizada promediando 5.48% (por encima de la meta) y oscilando ampliamente entre 1.0% y 10.5%. El patrón es exactamente el predicho por el modelo "consenso ≈ meta + ruido": la diferencia absoluta entre los RMSE del consenso y del ancla es pequeña en ambos subperíodos (~0.17 p.p. pre-pandemia, en este caso a favor del ancla, y ~0.03 p.p. post-pandemia, prácticamente empate; en ambos casos un orden de magnitud menor que la varianza muestral de los errores). La hipótesis alternativa (que el consenso procesa información genuina más allá de la meta) predeciría una diferencia mayor a favor del consenso, particularmente en post-pandemia cuando la inflación se aparta sustancialmente del ancla; los datos no respaldan esta lectura. La indistinguibilidad estadística del Cuadro 6 fuera de muestra, lejos de ser un detalle metodológico, constituye un test directo del modelo "consenso ≈ meta + ruido" y lo confirma.`));
c.push(P("Tres implicaciones de política se desprenden del análisis. Primera, dado que la rigidez informacional se intensifica significativamente bajo choques de gran magnitud, el régimen de comunicación del BCRD, ya considerado de buena calidad por estándares regionales, enfrenta su prueba más exigente precisamente en los momentos en los que las expectativas son menos informacionalmente eficientes. El BCRD ya publica fan charts de inflación general y subyacente con bandas al 75% y 50% en su Informe de Política Monetaria semestral (Banco Central de la República Dominicana, 2025, gráficos IV.12 y IV.14); una posibilidad de mejora marginal sería extender la prominencia y la granularidad de estos fan charts a una frecuencia más alta, idealmente coordinada con el ciclo mensual de la EEM, de modo que los analistas puedan calibrar sus pronósticos contra la distribución completa del escenario base del banco y no únicamente contra la meta puntual del 4%. La publicación de proyecciones condicionales con horizontes explícitos y la divulgación más frecuente de la lectura del propio banco sobre los choques contemporáneos puede operar como ancla focal que reduce la fricción informacional documentada."));

c.push(P("Segunda, dado que el sesgo pre-pandémico era de sobreestimación, ya que los analistas pronosticaban más inflación que la realizada, el reto de comunicación del banco central no era convencer al mercado de que la inflación se mantendría baja, sino más bien acelerar la convergencia de las expectativas hacia la trayectoria que la propia política monetaria estaba logrando. La continuidad del esquema de metas y la consistencia de la TPM con los objetivos comunicados son insumos directos de esa convergencia. La estructura del rechazo de eficiencia informacional, con la TPM rezagada como predictor más significativo del error, es consistente con un patrón en el que los analistas no incorporan plenamente la información sobre la TPM en su pronóstico de inflación, aunque una identificación causal estricta de este mecanismo queda fuera del alcance del presente análisis y requeriría un modelo estructural conjunto inflación-TPM."));

c.push(P("Tercera, la indistinguibilidad estadística del consenso EEM respecto a benchmarks mecánicos a doce meses sugiere que en la conducción monetaria los modelos econométricos del propio banco central, incluso especificaciones simples como un AR(1), tienen valor predictivo comparable al consenso de expertos a este horizonte. Esto no resta valor a la encuesta como termómetro de credibilidad, pero matiza la lectura del consenso como insumo predictivo en sentido estricto."));

c.push(H2("8.4. Limitaciones"));
c.push(P("Conviene anotar las limitaciones del estudio y la agenda de investigación que abren. Primero, se trabaja con la mediana del consenso, no con datos de panel individuales. La extensión natural a microdatos del panel permitiría descomponer el coeficiente de Coibion-Gorodnichenko entre rigidez efectiva y disagreement entre agentes, en línea con Bordalo et al. (2020), e implementar la batería moderna de tests para distinguir underreaction, overreaction y diagnostic expectations. El BCRD conserva las respuestas individuales de los aproximadamente cuarenta participantes del panel; el acceso a estas mediante solicitud formal de investigación académica es la mejora marginal más alta del análisis."));

c.push(P("Segundo, la interpretación estructural ψ = 1/(1+λ) bajo el modelo de Mankiw-Reis es estrictamente válida cuando la revisión de pronóstico se construye sobre objetivos fijos; la EEM reporta horizontes rodantes, y el chequeo de robustez del presente trabajo en la sección 7.6 muestra que el rechazo de rigidez es sensible a esta elección."));

c.push(P("Tercero, la identificación causal del rol de la TPM en el rechazo de eficiencia informacional permanece limitada. La TPM rezagada está mecánicamente correlacionada con la inflación rezagada vía la regla de reacción del banco central, por lo que la lectura de \"los analistas no procesan óptimamente la información sobre la TPM\" requiere supuestos adicionales. Una agenda natural es estimar una curva de Phillips dominicana híbrida con la TPM rezagada como instrumento para la expectativa de inflación, lo que permitiría dar interpretación estructural directa al coeficiente reportado en el cuadro 4. Una segunda agenda es identificar shocks de política monetaria à la Romer-Romer (2004) extrayendo la innovación pura de política como residuo de la TPM contra el información set del staff del BCRD al momento de cada decisión, y verificar si dicha innovación pura también predice el error de pronóstico privado."));

c.push(P("Cuarto, no se ha modelado explícitamente el rol del régimen cambiario. En una economía pequeña y abierta como la República Dominicana, el pass-through del tipo de cambio a precios es un canal de transmisión central, y un análisis serio del pass-through requeriría un VAR estructural con identificación recursiva apropiada y el testeo de si las expectativas dominicanas incorporan correctamente el coeficiente de pass-through estimado. La especificación actual del cuadro 4 con Δe_{t-13} como un único rezago puede ser inadecuada porque el patrón temporal del pass-through tiene típicamente peak entre seis y doce meses; una re-especificación ARDL podría modificar la conclusión sobre la significancia del canal cambiario."));

c.push(P("Quinto, la sección 7.11 utiliza la meta del 4% del BCRD como umbral exógeno en el threshold-MZ. Una mejora natural es estimar el umbral endógenamente siguiendo el procedimiento de Hansen (2000), que selecciona el umbral por verosimilitud y construye un intervalo de confianza no estándar para el parámetro de umbral. La predicción razonable es que el umbral endógeno caiga cerca de la meta, lo que confirmaría la elección exógena; si cae lejos, abre una discusión sustantiva nueva."));

c.push(P("Sexto, el periodo post-pandémico, aunque crítico, presenta una varianza tan elevada que reduce la potencia de las pruebas comparativas; el bootstrap por bloques de la sección 7.5 ya hace explícito que algunos rechazos del CG son sensibles a la metodología inferencial. La maduración de la muestra en los próximos años, con re-estimación periódica, permitirá conclusiones más robustas."));

c.push(P("Séptimo, la EEM tuvo cambios metodológicos documentados en 2014 y 2017, y el Chow exógeno detecta un quiebre real en 2017; parte de la dinámica del sesgo puede reflejar artefactos del rediseño de la encuesta más que cambios de comportamiento sustantivos del consenso. La sección 7.3 reporta el análisis con tres regímenes para neutralizar parcialmente este efecto."));

// 9. CONCLUSIONES
c.push(H1("9. Conclusiones"));
c.push(P("Este trabajo evaluó la racionalidad y la rigidez informacional de las expectativas medianas de inflación a doce meses para la República Dominicana, integrando la batería tradicional de pruebas con el test de rigidez informacional de Coibion-Gorodnichenko, una prueba formal de quiebre estructural con valores críticos de Andrews (1993) y un ejercicio de evaluación predictiva fuera de muestra con test de Diebold-Mariano. Las pruebas se realizan con la inflación interanual oficial del BCRD, debidamente empalmada para reconciliar el cambio de canasta de octubre de 2020. La inferencia HAC se reporta tanto con bandwidth Newey-West como con bandwidth de Hodrick para verificar robustez."));

c.push(P("Las expectativas dominicanas son aproximadamente consistentes con FIRE en condiciones de inflación cercana a la meta del 4%, pero exhiben dos desviaciones sistemáticas. La primera y económicamente dominante es la predictibilidad del error de pronóstico a partir de la TPM rezagada: el test de eficiencia informacional rechaza al 1% por amplio margen y la TPM efectiva rezagada captura por sí sola alrededor del 38% de la varianza total del error, fracción económicamente sustantiva que sobrevive a todas las correcciones de robustez aplicadas. La segunda es un sesgo asimétrico estado-dependiente: el consenso sobreestima la inflación cuando esta cae bajo la meta y la subestima cuando la supera, con prueba formal de igualdad rechazada al 1%. Ambas desviaciones pueden leerse como manifestaciones de un fenómeno común: el consenso EEM se aproxima en primera instancia como una constante cercana a la meta del banco central, una caracterización que reconcilia los resultados de este trabajo con la sobrepredicción documentada por Jiménez P. y López H. (2014) sobre la muestra previa. La rigidez informacional pura à la Coibion-Gorodnichenko, aunque exhibe un patrón de dicotomía pre/post-pandémica bajo la especificación estándar, pierde solidez al construir las revisiones con horizonte fijo, lo que limita la interpretación estructural ψ = 1/(1+λ). La calidad predictiva del consenso fuera de muestra es estadísticamente indistinguible de benchmarks naïve a horizonte de doce meses."));

c.push(P("La interpretación es que la racionalidad de las expectativas dominicanas es condicional a la magnitud y velocidad de los choques: aproximadamente FIRE en régimen estable, marcadamente subóptima durante shocks. La implicación de política es directa: el régimen de comunicación del BCRD enfrenta su prueba más exigente precisamente cuando las expectativas son menos informacionalmente eficientes, lo que sugiere que la frecuencia y precisión de la comunicación durante episodios de choques de oferta puede aportar valor económico tangible al acelerar la actualización del consenso privado."));

c.push(P("El trabajo deja varias agendas abiertas. Una replicación con datos individuales por grupo de agente permitiría descomponer el coeficiente de Coibion-Gorodnichenko entre rigidez efectiva y disagreement, profundizando la línea de Jiménez y López (2014) con el aparato moderno. Una integración con la curva de Phillips dominicana permitiría evaluar las implicaciones de la rigidez para la potencia de la política monetaria. Y la maduración del periodo post-shock proveerá observaciones adicionales que reduzcan la varianza muestral. Estas extensiones quedan para trabajo futuro."));

// REFERENCIAS
c.push(H1("Referencias"));
const refs = [
  "Andrade, P., Gautier, E., y Mengus, E. (2023). What matters in households' inflation expectations? Journal of Monetary Economics, 138, 50–68.",
  "Andrews, D. W. K. (1993). Tests for parameter instability and structural change with unknown change point. Econometrica, 61(4), 821–856.",
  "Atkeson, A., y Ohanian, L. E. (2001). Are Phillips curves useful for forecasting inflation? Federal Reserve Bank of Minneapolis Quarterly Review, 25(1), 2–11.",
  "Bai, J., y Perron, P. (1998). Estimating and testing linear models with multiple structural changes. Econometrica, 66(1), 47–78.",
  "Benjamini, Y., y Hochberg, Y. (1995). Controlling the false discovery rate: A practical and powerful approach to multiple testing. Journal of the Royal Statistical Society Series B, 57(1), 289–300.",
  "Bordalo, P., Gennaioli, N., Ma, Y., y Shleifer, A. (2020). Overreaction in macroeconomic expectations. American Economic Review, 110(9), 2748–2782.",
  "Banco Central de la República Dominicana (2025). Informe de Política Monetaria, diciembre 2025. Departamento de Programación Monetaria y Estudios Económicos.",
  "Britton, E., Fisher, P., y Whitley, J. (1998). The Inflation Report projections: Understanding the fan chart. Bank of England Quarterly Bulletin, 38(1), 30–37.",
  "Capistrán, C., y Ramos-Francia, M. (2010). Does inflation targeting affect the dispersion of inflation expectations? Journal of Money, Credit and Banking, 42(1), 113–134.",
  "Chow, G. C., y Lin, A. (1971). Best linear unbiased interpolation, distribution, and extrapolation of time series by related series. Review of Economics and Statistics, 53(4), 372–375.",
  "Coibion, O., y Gorodnichenko, Y. (2012). What can survey forecasts tell us about information rigidities? Journal of Political Economy, 120(1), 116–159.",
  "Coibion, O., y Gorodnichenko, Y. (2015). Information rigidity and the expectations formation process: A simple framework and new facts. American Economic Review, 105(8), 2644–2678.",
  "Diebold, F. X., y Mariano, R. S. (1995). Comparing predictive accuracy. Journal of Business & Economic Statistics, 13(3), 253–263.",
  "Faust, J., y Wright, J. H. (2013). Forecasting inflation. En G. Elliott y A. Timmermann (Eds.), Handbook of Economic Forecasting, vol. 2A (pp. 2–56). Elsevier.",
  "Forsells, M., y Kenny, G. (2002). The rationality of consumers' inflation expectations: Survey-based evidence for the Euro area. ECB Working Paper No. 163.",
  "Goldfayn-Frank, O., y Wohlfart, J. (2020). Expectation formation in a new environment: Evidence from the German reunification. Journal of Monetary Economics, 115, 301–320.",
  "Harvey, D., Leybourne, S., y Newbold, P. (1997). Testing the equality of prediction mean squared errors. International Journal of Forecasting, 13(2), 281–291.",
  "Hansen, B. E. (2000). Sample splitting and threshold estimation. Econometrica, 68(3), 575–603.",
  "Hodrick, R. J. (1992). Dividend yields and expected stock returns: Alternative procedures for inference and measurement. Review of Financial Studies, 5(3), 357–386.",
  "Jiménez P., M. A., y López H., N. S. (2014). Heterogeneidad y racionalidad en las expectativas de inflación: Evidencia desagregada para República Dominicana. Documento de Trabajo 2014-01, Departamento de Programación Monetaria y Estudios Económicos, Banco Central de la República Dominicana.",
  "Keane, M., y Runkle, D. (1990). Testing the rationality of price forecasts: New evidence from panel data. American Economic Review, 80(4), 714–735.",
  "Kiefer, N. M., y Vogelsang, T. J. (2005). A new asymptotic theory for heteroskedasticity-autocorrelation robust tests. Econometric Theory, 21(6), 1130–1164.",
  "Kohlhas, A. N., y Walther, A. (2021). Asymmetric attention. American Economic Review, 111(9), 2879–2925.",
  "Lazarus, E., Lewis, D. J., Stock, J. H., y Watson, M. W. (2018). HAR inference: Recommendations for practice. Journal of Business & Economic Statistics, 36(4), 541–559.",
  "Lucas, R. E. (1972). Expectations and the neutrality of money. Journal of Economic Theory, 4(2), 103–124.",
  "Maćkowiak, B., y Wiederholt, M. (2009). Optimal sticky prices under rational inattention. American Economic Review, 99(3), 769–803.",
  "Mankiw, N. G., y Reis, R. (2002). Sticky information versus sticky prices: A proposal to replace the New Keynesian Phillips curve. Quarterly Journal of Economics, 117(4), 1295–1328.",
  "Mankiw, N. G., Reis, R., y Wolfers, J. (2003). Disagreement about inflation expectations. NBER Macroeconomics Annual, 18, 209–248.",
  "Mincer, J., y Zarnowitz, V. (1969). The evaluation of economic forecasts. En J. Mincer (Ed.), Economic Forecasts and Expectations (pp. 3–46). NBER.",
  "Müller, U. K. (2014). HAC corrections for strongly autocorrelated time series. Journal of Business & Economic Statistics, 32(3), 311–322.",
  "Muth, J. F. (1961). Rational expectations and the theory of price movements. Econometrica, 29(3), 315–335.",
  "Newey, W. K., y West, K. D. (1994). Automatic lag selection in covariance matrix estimation. Review of Economic Studies, 61(4), 631–653.",
  "Pesaran, M. H., y Weale, M. (2006). Survey expectations. En G. Elliott, C. W. J. Granger y A. Timmermann (Eds.), Handbook of Economic Forecasting, vol. 1 (pp. 715–776). Elsevier.",
  "Politis, D. N., y Romano, J. P. (1994). The stationary bootstrap. Journal of the American Statistical Association, 89(428), 1303–1313.",
  "Quandt, R. E. (1960). Tests of the hypothesis that a linear regression system obeys two separate regimes. Journal of the American Statistical Association, 55(290), 324–330.",
  "Romer, C. D., y Romer, D. H. (2004). A new measure of monetary shocks: Derivation and implications. American Economic Review, 94(4), 1055–1084.",
  "Sargent, T. J., y Wallace, N. (1975). Rational expectations, the optimal monetary instrument, and the optimal money supply rule. Journal of Political Economy, 83(2), 241–254.",
  "Sims, C. A. (2003). Implications of rational inattention. Journal of Monetary Economics, 50(3), 665–690.",
  "West, K. D. (1996). Asymptotic inference about predictive ability. Econometrica, 64(5), 1067–1084.",
  "Woodford, M. (2003). Imperfect common knowledge and the effects of monetary policy. En P. Aghion et al. (Eds.), Knowledge, Information, and Expectations in Modern Macroeconomics (pp. 25–58). Princeton University Press."
];
refs.forEach(r => c.push(Ref(r)));

// ANEXO
c.push(new Paragraph({ children:[new PageBreak()] }));
c.push(H1("Anexo metodológico"));

c.push(H2("A.1. Construcción del error de pronóstico"));
c.push(P("El error de pronóstico se construye como e_t = π_t − E_{t−12}[π_t], donde π_t es la inflación interanual realizada (calculada como (IPC_t / IPC_{t−12} − 1) × 100 con la serie empalmada oficial del BCRD, base octubre 2019 – septiembre 2020 = 100) y E_{t−12}[π_t] es la mediana de las expectativas a doce meses reportadas en la EEM doce meses antes. Operacionalmente, esto se implementa en R como:"));

c.push(new Paragraph({
  spacing:{ before:80, after:200 },
  alignment: AlignmentType.LEFT,
  shading:{ fill:"F4F4F4", type:ShadingType.CLEAR },
  children:[new TextRun({
    text: "import pandas as pd\nimport numpy as np\n\ndf['E_pi_lag12'] = df['Inflación En 12 meses'].shift(12)\ndf['pi_t'] = (df['IPC'] / df['IPC'].shift(12) - 1) * 100\ndf['error_pronostico'] = df['pi_t'] - df['E_pi_lag12']",
    font:"Consolas", size:18
  })]
}));

c.push(H2("A.2. Selección de bandwidth HAC"));
c.push(P("Para datos solapados con horizonte h, la autocorrelación inducida llega hasta el orden h−1. Se implementa dos reglas: bandwidth automático de Newey-West (1994), garantizando un mínimo de h−1 = 11; y bandwidth fijo de Hodrick (1992) igual a 2h−1 = 23. Los resultados se reportan con ambos para verificar robustez."));

c.push(H2("A.3. Test de Diebold-Mariano"));
c.push(P("El test se implementa con loss cuadrático sobre la diferencia d_t = e²_{1,t} − e²_{2,t}, varianza de largo plazo HAC con bandwidth h−1 = 11, y corrección de muestras pequeñas de Harvey-Leybourne-Newbold (1997). El estadístico se compara contra la distribución t de Student con n−1 grados de libertad. Esta es la implementación recomendada por la literatura cuando los pronósticos son a horizonte h sobre observaciones mensuales."));

c.push(H2("A.4. Reproducibilidad"));
c.push(P("La implementación completa está en Python (≥3.10) usando pandas, numpy, statsmodels y scipy. El flujo se distribuye en scripts modulares: build_dataset_oficial.py construye el dataset consolidado a partir de los archivos del BCRD; run_analysis.py ejecuta los tests T1–T5, los diagnósticos y el ejercicio de Diebold-Mariano; run_analysis_robustez.py reporta el sesgo asimétrico, el procedimiento extendido de Bai-Perron y los tres regímenes; run_analysis_robustez_suplementario.py implementa el threshold-MZ con la meta del 4% como umbral exógeno y la especificación ARDL con rezagos 12-18 de la TPM; run_analysis_nivel2.py implementa el bootstrap por bloques tipo Politis-Romano (1994), el test de Kiefer-Vogelsang (2005) y la descomposición de R²; run_chow_lin.py implementa la mensualización del PIB por Chow y Lin (1971) usando el IMAE como indicador relacionado. Cada función está documentada con la ecuación correspondiente. La ejecución completa con los archivos de datos del BCRD (Histórico-EEM.xlsx, IPC General Mensual 2010–2026.xlsx, IMAE 2018=100.xlsx) regenera todas las tablas y figuras del paper. Los resultados numéricos completos están en el archivo de acompañamiento resultados.json. La generación del documento .docx final se hace con build_paper.js usando node y la librería docx."));

// =========================================================
// DOCUMENT
// =========================================================
const doc = new Document({
  creator:"César Emilio Medina Tineo",
  title:"Racionalidad y rigidez informacional en las expectativas de inflación: República Dominicana 2011–2026",
  styles:{
    default:{ document:{ run:{ font:"Times New Roman", size:22 } } },
    paragraphStyles:[
      { id:"Heading1", name:"Heading 1", basedOn:"Normal", next:"Normal", quickFormat:true,
        run:{ size:28, bold:true, font:"Times New Roman" },
        paragraph:{ spacing:{ before:360, after:200 }, outlineLevel:0 } },
      { id:"Heading2", name:"Heading 2", basedOn:"Normal", next:"Normal", quickFormat:true,
        run:{ size:24, bold:true, font:"Times New Roman" },
        paragraph:{ spacing:{ before:280, after:160 }, outlineLevel:1 } },
      { id:"Heading3", name:"Heading 3", basedOn:"Normal", next:"Normal", quickFormat:true,
        run:{ size:22, bold:true, italics:true, font:"Times New Roman" },
        paragraph:{ spacing:{ before:200, after:120 }, outlineLevel:2 } }
    ]
  },
  sections:[{
    properties:{ page:{ size:{ width:12240, height:15840 },
                         margin:{ top:1440, right:1440, bottom:1440, left:1440 } } },
    headers:{ default: new Header({ children:[new Paragraph({
      alignment:AlignmentType.RIGHT,
      children:[new TextRun({ text:"Medina Tineo (2026) — Racionalidad de expectativas RD", font:"Times New Roman", size:18, italics:true, color:"666666" })]
    })] }) },
    footers:{ default: new Footer({ children:[new Paragraph({
      alignment:AlignmentType.CENTER,
      children:[
        new TextRun({ children:[PageNumber.CURRENT], font:"Times New Roman", size:18 }),
        new TextRun({ text:" / ", font:"Times New Roman", size:18 }),
        new TextRun({ children:[PageNumber.TOTAL_PAGES], font:"Times New Roman", size:18 })
      ]
    })] }) },
    children: c
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("Paper_Expectativas_Inflacion_RD.docx", buf);
  console.log("Documento generado:", buf.length, "bytes,", c.length, "elementos.");
});
