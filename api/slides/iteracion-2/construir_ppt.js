// Construye la presentación de la iteración 2 y su guion.
// Uso (desde la raíz del repo):
//   python slides/iteracion-2/generar_imagenes.py
//   node slides/iteracion-2/construir_ppt.js      (requiere: npm install pptxgenjs)

const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const DIR = __dirname;
const IMG = path.join(DIR, "img");
const DARK = "1F3D2B";
const GREEN = "2E7D4F";
const ORANGE = "D9822B";
const INK = "1F2A24";
const MUTED = "5F6F66";

// Cada diapositiva: título, subtítulo corto opcional, imagen y lo que se dice (guion).
const slides = [
  {
    kind: "cover",
    speaker: "Carlos",
    min: 0.5,
    notes:
      "Buenos días. Somos Carlos, Aaron y Kalos. Nos tocó Specification-Driven Development y lo aplicamos a nuestro proyecto del curso, Yapa. La idea de la exposición es mostrar cómo escribir la especificación antes que el código cambió lo que construimos, no solo cómo lo documentamos.",
  },
  {
    title: "Una frase, muchas preguntas",
    subtitle: "El problema que SDD ataca: la ambigüedad",
    img: "01_ambiguedad.png",
    speaker: "Aaron",
    min: 1,
    notes:
      "Un requisito típico es 'el vecino debe poder registrar su pedido'. Suena claro, pero cada persona del equipo lo entiende distinto: ¿hasta qué hora?, ¿cuánto es el mínimo?, ¿quién pone el precio?, ¿qué pasa si mis vecinos no compran? Si esas respuestas no se escriben, cada uno las decide en su código y el sistema termina inconsistente. Eso es lo que SDD busca evitar: requisitos ambiguos, interpretaciones distintas y documentación que no coincide con el código.",
  },
  {
    title: "¿Qué es SDD?",
    subtitle: "La especificación dirige el diseño, el código y la validación",
    img: "02_flujo_sdd.png",
    speaker: "Aaron",
    min: 1.5,
    notes:
      "Specification-Driven Development pone la especificación en el centro. Partimos de una necesidad, la convertimos en requisito, y el requisito en una especificación verificable: entradas, salidas, reglas y errores. De ahí salen los criterios de aceptación, el diseño, el código y la validación contra esos mismos criterios. La flecha naranja es lo más importante: si algo cambia, no se parcha el código; se cambia primero la spec y de ahí baja el cambio. Diferencia con TDD: en TDD la prueba dirige; en SDD la especificación dirige, y las pruebas son una forma de verificarla.",
  },
  {
    title: "Las piezas de una especificación",
    subtitle: "Con un ejemplo real de nuestro proyecto",
    img: "03_piezas.png",
    speaker: "Aaron",
    min: 1.5,
    notes:
      "Estas son las cinco piezas y cómo se ven en Yapa. El requisito es la necesidad del usuario. La especificación la vuelve verificable. La regla de negocio es una condición que siempre se cumple, por ejemplo RP-10: el subtotal exacto debe ser al menos 50 soles. El criterio de aceptación es el escenario que lo prueba: con 49.99568 se rechaza, aunque redondeado daría 50. Y el contrato es la firma del componente: qué recibe y qué devuelve, incluido el código de error. Así respondemos la pregunta de requisito versus especificación: el requisito dice qué se necesita; la especificación dice exactamente cómo se comporta el sistema.",
  },
  {
    title: "Yapa en una semana",
    subtitle: "Compras grupales de vecinos, entrega el sábado",
    img: "04_ciclo_semanal.png",
    speaker: "Carlos",
    min: 1,
    notes:
      "Yapa junta los pedidos de vecinos de Lince, Jesús María y La Victoria. De lunes a miércoles cada uno arma su pedido y paga por adelantado el precio máximo. El miércoles a las 20:00 se cierra, el jueves se compra al proveedor aliado, el viernes se arma cada bolsa y se le toma foto, y el sábado se entrega en la portería de cada edificio. Después viene lo que llamamos 'te devolvemos': lo que se ahorró entre todos vuelve como saldo.",
  },
  {
    title: "Por qué fracasaron otros",
    subtitle: "Antes de especificar, revisamos los antecedentes",
    img: "05_antecedentes.png",
    speaker: "Carlos",
    min: 1,
    notes:
      "Antes de escribir reglas revisamos proyectos parecidos que cerraron. Favo, en Perú, agrupaba por distrito y nunca logró margen por pedido. Muni tenía un costo de adquisición alto y ticket bajo. Merqueo y Missfresh cargaban inventario y almacenes propios. Meituan Youxuan dependía de subsidios: cuando se prohibió vender bajo costo, el volumen cayó. Cada una de estas lecciones se convirtió en una regla: mínimo por zona, cero inventario, nunca subsidiar, margen por pedido.",
  },
  {
    title: "SDD encontró un problema legal",
    subtitle: "Antes de escribir una línea de código",
    img: "06_legal_antes_despues.png",
    speaker: "Carlos",
    min: 1.5,
    notes:
      "Al escribir la especificación del cobro encontramos que nuestro propio modelo de negocio cobraba en la puerta la diferencia cuando el peso real salía mayor, y si el cliente no pagaba, no recibía su pedido y quedaba suspendido. La Ley 29571, artículo 4.2, prohíbe cobrar recargos sobre el precio fijado. Si hubiéramos programado primero, ese error estaría en el código. Con SDD lo cambiamos en la spec: el cliente paga el precio máximo, nunca más de lo que vio, y la diferencia se le devuelve. Este es nuestro mejor ejemplo de qué pasa cuando cambia una especificación.",
  },
  {
    kind: "chart",
    title: "¿Alcanza el margen?",
    subtitle: "Ahorro del cliente frente a Plaza Vea, con 12 % de comisión y envío (precios del 24/09/2026)",
    speaker: "Carlos",
    min: 1.5,
    notes:
      "También validamos con precios reales. En abarrotes de marca, el supermercado vende casi a costo: con nuestra comisión, Yapa saldría más cara en 7 de 8 productos, hasta 25 por ciento más. En cambio, en frescos resistentes como papa, cebolla, ajo o limón, el ahorro para el cliente queda entre 36 y 67 por ciento. Esta evidencia cambió la especificación del catálogo: el piloto se enfoca en frescos resistentes y limpieza de marcas emergentes.",
  },
  {
    title: "Una parada por edificio",
    subtitle: "Costo de transporte por pedido",
    img: "08_costo_entrega.png",
    speaker: "Carlos",
    min: 0.75,
    notes:
      "Entregar casa por casa con un courier cuesta entre 8 y 15 soles por pedido. Si el camión hace una sola parada por edificio y deja todo en la portería, el costo baja a entre 0.89 y 2.60 soles. Por eso la zona en Yapa no es un distrito: es un punto de recepción.",
  },
  {
    title: "Zonas creadas por vecinos",
    img: "09_zonas.png",
    speaker: "Carlos",
    min: 0.75,
    notes:
      "Un vecino crea la zona, registra el punto de recepción y a la persona que recibe. Si dos zonas están cerca, pueden unirse para llegar juntas al mínimo de 8 pedidos, pero cada una mantiene su parada. Si una zona está a más de 500 metros, no se une porque el camión perdería tiempo y dinero.",
  },
  {
    title: "Te devolvemos",
    subtitle: "Un pedido real de nuestras pruebas",
    img: "10_te_devolvemos.png",
    speaker: "Kalos",
    min: 1,
    notes:
      "Este es un pedido de nuestras pruebas de aceptación. El vecino pagó 61 soles, el precio máximo. Entre todos se alcanzaron tramos de descuento en papa amarilla, papa blanca y cebolla: 9.86 soles menos. El envío se repartió entre 20 pedidos de la zona: 3 soles menos. El costo real fue 48.14 y le devolvemos 12.86 como saldo. Todos estos números salen del código y los verifica una prueba.",
  },
  {
    title: "Si alguien se retira, Yapa no pierde",
    img: "11_tramos.png",
    speaker: "Kalos",
    min: 1,
    notes:
      "Un riesgo era: si alguien compra con el precio de descuento y luego otros se retiran, ¿quién paga la diferencia? Lo resolvimos en la spec: todos pagan el precio máximo y el precio final se calcula al cierre. Si alguien se retira y bajamos de 100 a 95 kilos, el precio vuelve al máximo, pero nunca lo supera. Esa propiedad está escrita como criterio CL-05 y CL-08 y tiene su prueba.",
  },
  {
    title: "De la regla a la prueba",
    subtitle: "Trazabilidad de una especificación",
    img: "12_trazabilidad.png",
    speaker: "Aaron",
    min: 1.5,
    notes:
      "Así recorremos una especificación de punta a punta, que es lo que pide el curso. La decisión de negocio está en el documento de clarificaciones. La regla RP-10 está en la spec. El criterio CA-11 describe el caso de frontera. El código está en order_registration.py, línea 116. La prueba se llama igual que el criterio. Y se puede ver en vivo con la consola. La matriz completa, con las 24 reglas, está en docs/sdd/06-trazabilidad.md.",
  },
  {
    title: "Diseño en capas",
    img: "13_capas.png",
    speaker: "Aaron",
    min: 1,
    notes:
      "La spec nos llevó a separar responsabilidades. Las reglas del registro y de la liquidación viven en sus propios módulos y no dependen de la consola ni del almacenamiento. El repositorio es en memoria, pero se puede cambiar por una base de datos sin tocar las reglas. Además, como la spec dice que el precio lo pone el sistema, la función de registro ni siquiera recibe precio: es imposible que el cliente lo mande.",
  },
  {
    title: "Spec primero: el historial de Git",
    img: "14_git_historial.png",
    speaker: "Kalos",
    min: 1,
    notes:
      "El historial muestra el orden real del trabajo: primero clarificaciones, especificación, criterios y diseño; después las pruebas; y recién al final el código. Cuando a mitad de camino descubrimos un caso nuevo, por ejemplo un faltante reportado para un pedido que nunca se entregó, primero entró como cambio de spec, luego como prueba y después como código.",
  },
  {
    title: "De rojo a verde",
    subtitle: "Las pruebas se escribieron antes del código",
    img: "15_rojo_verde.png",
    speaker: "Kalos",
    min: 0.75,
    notes:
      "Guardamos la salida de cada momento en docs/evidencia. Primero, las 42 pruebas escritas fallaban porque el código no existía. Luego implementamos el registro y quedó solo la liquidación pendiente. Al final, con la liquidación y la revisión de casos borde, las 45 pruebas pasan. En esa revisión encontramos tres fallos que ninguna prueba cubría, como una cantidad NaN que hacía caer el programa, y los corregimos agregando primero su prueba.",
  },
  {
    title: "Demo en vivo",
    subtitle: "python -m yapa_sdd.cli ciclo ejemplos/ciclo_demo.json",
    img: "16_demo.png",
    speaker: "Kalos",
    min: 3,
    notes:
      "Aquí salimos a la terminal. Primero cotizamos un pedido y lo registramos. Luego mostramos tres rechazos: un pedido a las 20:00 en punto, uno bajo el mínimo que dice cuánto falta, y uno de una zona fuera del piloto. Por último, ejecutamos un ciclo completo: veinte vecinos de Jesús María reciben saldo, el pedido que no verificó su pago queda cancelado, y el grupo de Lince, que no llegó a 8 pedidos, recibe reembolso total. Esta imagen es la salida real, por si falla el proyector.",
  },
  {
    title: "Resultados",
    img: "17_resultados.png",
    speaker: "Carlos",
    min: 0.75,
    notes:
      "En resumen: 24 reglas especificadas, 24 criterios de aceptación, 45 pruebas en verde y 16 commits en el orden docs, test, feat. Lo que no afirmamos: no probamos integración real con Yape o Plin, que no tienen API pública, ni validamos todavía los precios del mercado de barrio, que es el competidor real en frescos.",
  },
  {
    title: "Lo que aprendimos",
    img: "18_lecciones.png",
    speaker: "Carlos",
    min: 1,
    notes:
      "Tres lecciones. Primero, preguntar antes de programar: escribir 12 decisiones y 12 supuestos nos evitó construir un cobro ilegal. Segundo, cada regla con su prueba: así cualquiera puede verificar que el código cumple lo que dice la spec. Tercero, cuando algo cambia, se cambia primero la spec. La dificultad fue el tiempo: especificar bien toma más que programar directo, y una spec equivocada produce código coherente pero equivocado. Lo usaríamos de nuevo en proyectos con reglas de negocio y varias personas involucradas.",
  },
  {
    kind: "closing",
    speaker: "Todos",
    min: 1,
    notes: "Gracias. Quedamos atentos a sus preguntas. (Guía de defensa: docs/07-trazabilidad-defensa.md)",
  },
];

const savings = {
  labels: ["Papel higiénico", "Arroz Costeño", "Aceite Primor", "Leche Gloria", "Detergente", "Azúcar", "Fideos",
    "Atún", "Cebolla", "Limón", "Papa amarilla", "Papa blanca", "Zanahoria", "Camote", "Ajo"],
  marca: [-25, -10.7, -10.6, -9.7, -6.6, -5.2, -5.2, 2.5, 0, 0, 0, 0, 0, 0, 0],
  frescos: [0, 0, 0, 0, 0, 0, 0, 0, 36, 46, 48, 50, 52, 62, 67],
};

function imageBox(file, maxW, maxH) {
  // Las imágenes miden 2460 px de ancho a 200 dpi → 12.3 pulgadas.
  const buf = fs.readFileSync(path.join(IMG, file));
  const w = buf.readUInt32BE(16);
  const h = buf.readUInt32BE(20);
  let width = maxW;
  let height = (h / w) * width;
  if (height > maxH) {
    height = maxH;
    width = (w / h) * height;
  }
  return { w: width, h: height };
}

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.title = "Yapa · SDD · Iteración 2";
pres.author = "Carlos Bravo";

slides.forEach((s, index) => {
  const slide = pres.addSlide();
  if (s.kind === "cover") {
    slide.background = { color: DARK };
    slide.addText("Yapa", { x: 0.8, y: 1.6, w: 11.7, h: 1.4, fontFace: "Cambria", fontSize: 72, bold: true,
      color: "FFFFFF", margin: 0, isTextBox: true });
    slide.addText("Specification-Driven Development aplicado a un proyecto real", { x: 0.8, y: 3.05, w: 11.7,
      h: 0.7, fontFace: "Calibri", fontSize: 26, color: "CFE3D6", margin: 0, isTextBox: true });
    slide.addText("Carlos Bravo · Aaron Gonzales · Kalos Lazo", { x: 0.8, y: 5.3, w: 11.7, h: 0.5,
      fontFace: "Calibri", fontSize: 18, color: "FFFFFF", margin: 0, isTextBox: true });
    slide.addText("Diseño de Software (EL3304) · UTEC 2026-2 · Iteración 2", { x: 0.8, y: 5.8, w: 11.7,
      h: 0.4, fontFace: "Calibri", fontSize: 14, color: "CFE3D6", margin: 0, isTextBox: true });
  } else if (s.kind === "closing") {
    slide.background = { color: DARK };
    slide.addText("¿Preguntas?", { x: 0.8, y: 2.6, w: 11.7, h: 1.4, fontFace: "Cambria", fontSize: 60,
      bold: true, color: "FFFFFF", align: "center", margin: 0, isTextBox: true });
    slide.addText("github.com/kaloslazo/sdd-2026-exposicion · rama carlos/iteracion-2-sdd", { x: 0.8, y: 4.2,
      w: 11.7, h: 0.5, fontFace: "Calibri", fontSize: 16, color: "CFE3D6", align: "center", margin: 0,
      isTextBox: true });
  } else {
    slide.background = { color: "FFFFFF" };
    slide.addText(s.title, { x: 0.5, y: 0.35, w: 12.3, h: 0.75, fontFace: "Cambria", fontSize: 34, bold: true,
      color: DARK, margin: 0, isTextBox: true });
    let top = 1.2;
    if (s.subtitle) {
      slide.addText(s.subtitle, { x: 0.5, y: 1.1, w: 12.3, h: 0.45, fontFace: "Calibri", fontSize: 16,
        color: MUTED, margin: 0, isTextBox: true });
      top = 1.7;
    }
    const maxH = 7.5 - top - 0.35;
    if (s.kind === "chart") {
      slide.addChart(pres.charts.BAR, [
        { name: "Abarrotes de marca", labels: savings.labels, values: savings.marca },
        { name: "Frescos resistentes", labels: savings.labels, values: savings.frescos },
      ], {
        x: 0.5, y: top, w: 12.3, h: maxH, barDir: "bar", barGrouping: "stacked", barGapWidthPct: 45,
        chartColors: [ORANGE, GREEN], showLegend: true, legendPos: "b", legendFontSize: 13,
        legendColor: INK, showValue: true, dataLabelPosition: "inEnd", dataLabelFontSize: 11,
        dataLabelColor: "FFFFFF", dataLabelFormatCode: '0"%";-0"%";;', catAxisLabelColor: INK,
        catAxisLabelFontSize: 12, catAxisLabelPos: "low", valAxisLabelColor: MUTED, valAxisLabelFontSize: 11,
        valAxisLabelFormatCode: '0"%"', valAxisMinVal: -30, valAxisMaxVal: 70,
        valGridLine: { color: "E3E8E5", size: 0.75 }, catGridLine: { style: "none" },
      });
    } else {
      const size = imageBox(s.img, 12.3, maxH);
      slide.addImage({ path: path.join(IMG, s.img), x: 0.5 + (12.3 - size.w) / 2, y: top, w: size.w, h: size.h,
        altText: s.title });
    }
    slide.addText(String(index + 1), { x: 12.3, y: 7.05, w: 0.5, h: 0.3, fontFace: "Calibri", fontSize: 11,
      color: MUTED, align: "right", margin: 0, isTextBox: true });
  }
  slide.addNotes(`[${s.speaker}] ${s.notes}`);
});

// Guion en Markdown, generado de los mismos datos.
const total = slides.reduce((acc, s) => acc + s.min, 0);
let md = "# Guion de la exposición · iteración 2\n\n";
md += `Presentación: \`yapa-sdd-iteracion-2.pptx\` (${slides.length} diapositivas, ~${Math.round(total)} min más preguntas). `;
md += "Las diapositivas solo tienen títulos e imágenes; todo lo que se dice está aquí y en las notas del orador.\n\n";
md += "El reparto de expositores es una propuesta: el curso evalúa que todos participen y dominen el proyecto.\n\n";
md += "| # | Diapositiva | Expositor | Min |\n|---:|---|---|---:|\n";
slides.forEach((s, i) => {
  md += `| ${i + 1} | ${s.title || (s.kind === "cover" ? "Portada" : "Cierre")} | ${s.speaker} | ${s.min} |\n`;
});
slides.forEach((s, i) => {
  md += `\n## ${i + 1}. ${s.title || (s.kind === "cover" ? "Portada" : "Cierre")} · ${s.speaker}\n\n${s.notes}\n`;
});
fs.writeFileSync(path.join(DIR, "guion.md"), md, "utf8");

pres.writeFile({ fileName: path.join(DIR, "yapa-sdd-iteracion-2.pptx") }).then((f) => console.log("ok", f));
