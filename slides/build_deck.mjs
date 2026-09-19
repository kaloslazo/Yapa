import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const workspaceDir = path.resolve(scriptDir, "..");
const skillDir = "/Users/kalosroots/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations";
const buildDir = path.join(scriptDir, ".build");
const draftPath = path.join(buildDir, "sdd-2026-yapa-minimal-draft.pptx");

await fs.mkdir(buildDir, { recursive: true });

const { resolvePresentationFont } = await import(
  pathToFileURL(path.join(skillDir, "container_tools/artifact_tool_utils.mjs")).href,
);

const FONT = resolvePresentationFont({ fontFamily: "Helvetica Neue" });
const C = {
  black: "#0A0A0A",
  white: "#FFFFFF",
  gray: "#6B7280",
  light: "#F5F5F5",
  line: "#D6D6D6",
};

const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });

function addText(slide, value, left, top, width, height, opts = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position: { left, top, width, height },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = value;
  shape.text.style = {
    typeface: opts.typeface ?? FONT,
    fontSize: opts.fontSize ?? 22,
    color: opts.color ?? C.black,
    bold: opts.bold ?? false,
    italic: opts.italic ?? false,
    alignment: opts.alignment ?? "left",
    autoFit: "none",
  };
  return shape;
}

function addBlock(slide, value, left, top, width, height, opts = {}) {
  const block = slide.shapes.add({
    geometry: opts.geometry ?? "rect",
    position: { left, top, width, height },
    fill: opts.fill ?? C.white,
    line: { style: "solid", fill: opts.line ?? C.line, width: opts.lineWidth ?? 1 },
    borderRadius: opts.radius ?? 0,
  });
  block.text = value;
  block.text.style = {
    typeface: opts.typeface ?? FONT,
    fontSize: opts.fontSize ?? 22,
    color: opts.color ?? C.black,
    bold: opts.bold ?? false,
    alignment: opts.alignment ?? "left",
    autoFit: "none",
  };
  return block;
}

function addRule(slide, left, top, width, color = C.black, height = 2) {
  return addBlock(slide, "", left, top, width, height, { fill: color, line: color, lineWidth: 0 });
}

function addTitle(slide, section, title, subtitle = "") {
  addText(slide, section.toUpperCase(), 72, 42, 520, 22, { fontSize: 13, bold: true, color: C.gray });
  addText(slide, title, 72, 78, 1136, 58, { fontSize: 39, bold: true });
  if (subtitle) addText(slide, subtitle, 74, 142, 1080, 36, { fontSize: 19, color: C.gray });
}

function addFooter(slide, number) {
  addRule(slide, 72, 667, 1136, C.line, 1);
  addText(slide, "SDD · Yapa · 2026", 72, 682, 300, 18, { fontSize: 11, color: C.gray });
  addText(slide, String(number).padStart(2, "0"), 1170, 682, 38, 18, { fontSize: 11, bold: true, alignment: "right" });
}

function notes(slide, text) {
  slide.speakerNotes.textFrame.setText(text);
}

function baseSlide(bg = C.white) {
  const slide = presentation.slides.add();
  slide.background.fill = bg;
  return slide;
}

function addNode(slide, label, sub, left, top, width = 150, height = 86, fill = C.white) {
  const node = addBlock(slide, `${label}\n${sub}`, left, top, width, height, {
    fill,
    line: C.black,
    lineWidth: 1,
    color: fill === C.black ? C.white : C.black,
    fontSize: 17,
    bold: true,
    alignment: "center",
  });
  return node;
}

// 1. Cover
{
  const slide = baseSlide();
  addText(slide, "SPECIFICATION-DRIVEN DEVELOPMENT", 72, 72, 720, 24, { fontSize: 14, bold: true, color: C.gray });
  addRule(slide, 72, 112, 120, C.black, 4);
  addText(slide, "De la necesidad\nal código verificable", 72, 164, 870, 168, { fontSize: 58, bold: true });
  addText(slide, "Aplicación de SDD a una funcionalidad real de Yapa", 76, 378, 720, 36, { fontSize: 22, color: C.gray });
  addText(slide, "Diseño de Software · 19 septiembre 2026", 76, 600, 520, 24, { fontSize: 16, color: C.gray });
  addText(slide, "01", 1120, 600, 88, 38, { fontSize: 28, bold: true, alignment: "right" });
  notes(slide, "Apertura: SDD organiza la colaboración entre negocio, equipo e IA. La presentación muestra el método aplicado a una vertical real de Yapa, no una aplicación completa.\n\nFuente de contexto: docs/sources.md\nTiempo: 1:00.");
}

// 2. Purpose and problem
{
  const slide = baseSlide();
  addTitle(slide, "Propósito", "El problema que SDD resuelve", "Convertir una necesidad ambigua en comportamiento que el equipo pueda construir y comprobar.");
  addText(slide, "NECESIDAD", 90, 238, 220, 22, { fontSize: 13, bold: true, color: C.gray });
  addText(slide, "“Registrar un pedido semanal”", 90, 270, 420, 58, { fontSize: 30, bold: true });
  addRule(slide, 90, 354, 420, C.black, 2);
  addText(slide, "Preguntas que la frase deja abiertas", 90, 392, 420, 28, { fontSize: 19, bold: true });
  addText(slide, "¿En qué zonas?\n¿Hasta cuándo?\n¿Qué precio y qué delivery?\n¿Qué pasa si no hay capacidad?", 90, 438, 420, 138, { fontSize: 22, color: C.gray });
  addRule(slide, 648, 230, 2, C.black, 350);
  addText(slide, "SDD HACE EXPLÍCITO", 700, 238, 390, 22, { fontSize: 13, bold: true, color: C.gray });
  addText(slide, "Requisitos\nEspecificación\nReglas de negocio\nCriterios de aceptación\nEvidencia", 700, 278, 380, 218, { fontSize: 30, bold: true });
  addText(slide, "Objetivo: reducir interpretaciones distintas, retrabajo y distancia entre documentación y código.", 700, 548, 410, 56, { fontSize: 19, color: C.gray });
  addFooter(slide, 2);
  notes(slide, "SDD responde a problemas que aparecen cuando el equipo completa silenciosamente las decisiones: ambigüedad, cambios frecuentes, documentación que se separa del código y conversaciones difíciles de revisar.\n\nFuente: docs/02-metodologia-sdd.md y la sección 5.3 del markdown del curso.\nTiempo: 1:40.");
}

// 3. Concepts
{
  const slide = baseSlide();
  addTitle(slide, "Conceptos", "Cinco piezas hacen verificable una intención", "Cada pieza reduce una ambigüedad distinta del trabajo de software.");
  const rows = [
    ["Requisito", "Qué necesita el usuario o el negocio"],
    ["Especificación", "Qué debe hacer el sistema, con entradas y salidas"],
    ["Regla de negocio", "Qué condición debe cumplirse siempre"],
    ["Criterio de aceptación", "Cómo comprobamos que un comportamiento cumple"],
    ["Contrato", "Qué recibe y qué devuelve un componente"],
  ];
  let y = 230;
  for (const [term, definition] of rows) {
    addText(slide, term, 110, y, 280, 32, { fontSize: 23, bold: true });
    addRule(slide, 390, y + 28, 34, C.black, 2);
    addText(slide, definition, 460, y, 650, 32, { fontSize: 22, color: C.gray });
    y += 72;
  }
  addRule(slide, 110, 594, 1000, C.line, 1);
  addText(slide, "La especificación se conserva mientras el trabajo avanza.", 110, 616, 1000, 30, { fontSize: 20, bold: true });
  addFooter(slide, 3);
  notes(slide, "Esta diapositiva cubre el vocabulario que el profesor solicita: requisitos, especificaciones, reglas, criterios y contratos. La clave es que no son documentos aislados: juntos describen el comportamiento antes y durante la implementación.\n\nFuente: docs/02-metodologia-sdd.md y la sección 5.2 del markdown del curso.\nTiempo: 1:40.");
}

// 4. SDD workflow
{
  const slide = baseSlide(C.black);
  addText(slide, "PROCESO SDD", 72, 42, 500, 22, { fontSize: 13, bold: true, color: "#B0B0B0" });
  addText(slide, "La cadena de trabajo", 72, 78, 1136, 58, { fontSize: 39, bold: true, color: C.white });
  addText(slide, "Necesidad hasta resultado, con una revisión en cada paso.", 74, 142, 1000, 34, { fontSize: 19, color: "#A0A0A0" });
  const labels = [
    ["01", "Necesidad"], ["02", "Requisitos"], ["03", "Spec"], ["04", "Diseño"], ["05", "Código"], ["06", "Validación"], ["07", "Resultado"],
  ];
  const nodes = [];
  let x = 72;
  for (const [n, label] of labels) {
    const node = addBlock(slide, `${n}\n${label}`, x, 266, 142, 100, { fill: C.black, line: C.white, lineWidth: 1, color: C.white, fontSize: 20, bold: true, alignment: "center" });
    nodes.push(node);
    x += 170;
  }
  for (let i = 0; i < nodes.length - 1; i++) {
    slide.shapes.connect(nodes[i], nodes[i + 1], { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: "#A0A0A0", width: 1 }, tail: { type: "triangle", width: "sm", length: "sm" } });
  }
  addText(slide, "La especificación acompaña al código y sirve para revisar el resultado.", 160, 516, 960, 42, { fontSize: 27, bold: true, color: C.white, alignment: "center" });
  addText(slide, "La IA puede acelerar cada paso; el equipo conserva la responsabilidad de aprobarlo.", 175, 580, 930, 32, { fontSize: 19, color: "#A0A0A0", alignment: "center" });
  addFooter(slide, 4);
  notes(slide, "Este es el flujo del markdown: necesidad, requisitos, especificación, diseño, implementación, validación y resultado. La trazabilidad permite volver desde un resultado hasta la regla que lo originó.\n\nFuente: sección 5.1 y 5.4 del markdown del curso; docs/sdd/06-trazabilidad.md.\nTiempo: 1:50.");
}

// 5. Yapa scope
{
  const slide = baseSlide();
  addTitle(slide, "Caso práctico", "Yapa: una funcionalidad real y acotada", "Yapa consolida compras mayoristas por zona para entregar el sábado.");
  addText(slide, "EL PROYECTO COMPLETO", 90, 230, 440, 22, { fontSize: 13, bold: true, color: C.gray });
  addText(slide, "Catálogo · pedidos · pagos · consolidación\ncompra · preparación · entrega · incidencias", 90, 270, 470, 100, { fontSize: 26, bold: true });
  addText(slide, "La operación piloto considera Lince, Jesús María y La Victoria.", 90, 418, 460, 54, { fontSize: 20, color: C.gray });
  addRule(slide, 640, 220, 2, C.black, 350);
  addText(slide, "ESTA ENTREGA", 700, 230, 390, 22, { fontSize: 13, bold: true, color: C.gray });
  addText(slide, "CUN-02\nRegistrar pedido semanal", 700, 270, 430, 100, { fontSize: 36, bold: true });
  addRule(slide, 700, 398, 420, C.black, 2);
  addText(slide, "Límite mínimo de CUN-03: conservar el medio de pago permitido.", 700, 430, 420, 60, { fontSize: 20, color: C.gray });
  addText(slide, "El repositorio general conserva el mapa completo del proyecto.", 700, 548, 420, 36, { fontSize: 18, bold: true });
  addFooter(slide, 5);
  notes(slide, "El profesor pide aplicar la metodología sobre el proyecto del curso. Por eso usamos Yapa y no un ejemplo inventado. Acotamos la entrega a CUN-02 para poder demostrar reglas, código y evidencia sin presentar como terminado el sistema completo.\n\nFuente: Entregable01_ModeladoNegocio_Yapa.pdf y docs/sdd/01-alcance.md.\nTiempo: 1:40.");
}

// 6. Specification
{
  const slide = baseSlide();
  addTitle(slide, "Especificación", "CUN-02 tiene entradas, reglas y una salida", "El documento define el comportamiento antes de implementar.");
  addText(slide, "ENTRADA", 86, 228, 280, 22, { fontSize: 13, bold: true, color: C.gray });
  addBlock(slide, "clienteId: 100\ndistrito: Lince\nproducto: Arroz × 2 kg\nventana: SAT_09_12\npago: TRANSFERENCIA", 86, 264, 330, 190, { fill: C.light, line: C.line, fontSize: 21, bold: true });
  addText(slide, "REGLAS", 476, 228, 280, 22, { fontSize: 13, bold: true, color: C.gray });
  addText(slide, "zona cubierta\nciclo abierto\nsubtotal mínimo\nprecio vigente\ncapacidad disponible", 476, 264, 290, 190, { fontSize: 23, bold: true });
  addText(slide, "SALIDA", 862, 228, 280, 22, { fontSize: 13, bold: true, color: C.gray });
  addBlock(slide, "orderId: 1200\nestado: REGISTRADO\nsubtotal: S/ 60.00\ndelivery: S/ 7.90\ntotal: S/ 67.90", 862, 264, 330, 190, { fill: C.black, line: C.black, color: C.white, fontSize: 21, bold: true });
  addRule(slide, 86, 524, 1106, C.black, 2);
  addText(slide, "Una especificación precisa permite que negocio, IA y desarrollo hablen de la misma operación.", 150, 560, 980, 40, { fontSize: 24, bold: true, alignment: "center" });
  addFooter(slide, 6);
  notes(slide, "Mostrar la especificación como contrato. El ejemplo usa una entrada concreta, reglas observables y una salida esperada. La estructura responde al caso práctico que pide el markdown: requerimiento, entrada, reglas y resultado.\n\nFuente local: docs/sdd/02-especificacion-cun-02.md.\nTiempo: 1:50.");
}

// 7. Rules and acceptance
{
  const slide = baseSlide(C.black);
  addText(slide, "VALIDACIÓN", 72, 42, 500, 22, { fontSize: 13, bold: true, color: "#B0B0B0" });
  addText(slide, "Reglas que se pueden comprobar", 72, 78, 1136, 58, { fontSize: 39, bold: true, color: C.white });
  addText(slide, "La aceptación convierte una frase de negocio en un escenario verificable.", 74, 142, 1080, 34, { fontSize: 19, color: "#A0A0A0" });
  addText(slide, "REGLAS IMPLEMENTADAS", 90, 232, 420, 22, { fontSize: 13, bold: true, color: "#B0B0B0" });
  addText(slide, "RN-01  cobertura piloto\nRN-02  ciclo lunes a miércoles\nRN-03  subtotal mínimo S/ 50\nRN-04  delivery S/ 7.90 o gratis desde S/ 120\nRN-05  precio con unidad y vigencia\nRN-09  ventana con capacidad\nRN-10  medio de pago permitido", 90, 274, 500, 250, { fontSize: 21, bold: true, color: C.white });
  addRule(slide, 650, 220, 2, C.white, 326);
  addText(slide, "CRITERIOS DE ACEPTACIÓN", 730, 232, 400, 22, { fontSize: 13, bold: true, color: "#B0B0B0" });
  addText(slide, "DADO un cliente de Lince, un ciclo abierto y una canasta válida\nCUANDO registra el pedido\nENTONCES recibe REGISTRADO con subtotal, delivery y total", 730, 274, 420, 132, { fontSize: 21, bold: true, color: C.white });
  addRule(slide, 730, 438, 420, "#A0A0A0", 1);
  addText(slide, "DADO una ventana cuya capacidad está completa\nCUANDO intenta registrar\nENTONCES recibe DELIVERY_WINDOW_FULL", 730, 466, 420, 114, { fontSize: 21, bold: true, color: C.white });
  addFooter(slide, 7);
  notes(slide, "El markdown exige reglas de negocio y al menos tres criterios de aceptación. Aquí mostramos siete reglas implementadas y dos escenarios en formato DADO, CUANDO y ENTONCES. La suite automatiza estos comportamientos.\n\nFuente: sección 5.5 y 5.6 del markdown del curso; docs/sdd/05-criterios-aceptacion.md.\nTiempo: 2:00.");
}

// 8. Design model
{
  const slide = baseSlide();
  addTitle(slide, "Diseño", "Modelo mínimo para registrar el pedido", "El diseño mantiene el ejemplo pequeño y separa reglas de infraestructura.");
  addText(slide, "ENTRADAS", 90, 202, 240, 20, { fontSize: 13, bold: true, color: C.gray });
  addText(slide, "DOMINIO", 700, 202, 180, 20, { fontSize: 13, bold: true, color: C.gray });
  addText(slide, "SALIDA", 930, 202, 220, 20, { fontSize: 13, bold: true, color: C.gray });
  const address = addNode(slide, "CustomerAddress", "distrito\nvalidada", 90, 240, 230, 82, C.light);
  const line = addNode(slide, "OrderLine", "producto\ncantidad", 90, 352, 230, 82, C.light);
  const window = addNode(slide, "DeliveryWindow", "horario\ncapacidad", 90, 464, 230, 82, C.light);
  const payment = addNode(slide, "PaymentMethod", "medio permitido", 430, 352, 230, 82, C.light);
  const service = addNode(slide, "CUN-02", "validar\ny calcular", 700, 352, 130, 82, C.black);
  const order = addNode(slide, "RegisteredOrder", "estado\nimportes", 900, 352, 230, 110, C.black);
  slide.shapes.connect(service, order, { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.black, width: 1 }, tail: { type: "triangle", width: "sm", length: "sm" } });
  addRule(slide, 90, 594, 1100, C.line, 1);
  addText(slide, "La función de dominio valida las entradas, calcula los importes y construye el resultado.", 120, 614, 1040, 42, { fontSize: 24, bold: true, alignment: "center" });
  addFooter(slide, 8);
  notes(slide, "Este es el modelo o diagrama de diseño requerido por el markdown. No pretende ser la arquitectura total: muestra las entidades mínimas que intervienen en CUN-02 y deja explícitas las responsabilidades que todavía no se implementan.\n\nFuente local: docs/sdd/03-plan.md.\nTiempo: 1:40.");
}

// 9. Traceability and tools
{
  const slide = baseSlide();
  addTitle(slide, "Trazabilidad", "Cada decisión deja una referencia", "La revisión puede ir desde la regla hacia el código o desde el resultado hacia el requisito.");
  const labels = ["Requisito", "Regla", "Criterio", "Código", "Test", "Resultado"];
  const nodes = [];
  let x = 84;
  for (const label of labels) {
    const node = addBlock(slide, label, x, 238, 160, 62, { fill: label === "Resultado" ? C.black : C.light, line: C.black, color: label === "Resultado" ? C.white : C.black, fontSize: 19, bold: true, alignment: "center" });
    nodes.push(node);
    x += 190;
  }
  for (let i = 0; i < nodes.length - 1; i++) {
    slide.shapes.connect(nodes[i], nodes[i + 1], { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.black, width: 1 }, tail: { type: "triangle", width: "sm", length: "sm" } });
  }
  addRule(slide, 84, 372, 1110, C.line, 1);
  addText(slide, "Herramientas usadas", 84, 416, 280, 30, { fontSize: 24, bold: true });
  addText(slide, "Markdown versionado · GitHub · Python 3.11 · unittest\nAgente de IA para proponer artefactos · revisión humana para aprobar decisiones", 84, 466, 760, 72, { fontSize: 22, color: C.gray });
  addText(slide, "La herramienta cambia; la cadena de evidencia permanece.", 84, 590, 820, 32, { fontSize: 21, bold: true });
  addFooter(slide, 9);
  notes(slide, "El markdown solicita herramientas de ingeniería. La propuesta usa Markdown y Git para conservar specs, Python y unittest para validar, y herramientas de IA para acelerar la redacción y el código. La revisión humana conserva el control sobre alcance, reglas y evidencia.\n\nFuentes: docs/03-herramientas-2026.md y docs/sdd/06-trazabilidad.md.\nTiempo: 1:40.");
}

// 10. Code and evidence
{
  const slide = baseSlide(C.black);
  addText(slide, "IMPLEMENTACIÓN", 72, 42, 500, 22, { fontSize: 13, bold: true, color: "#B0B0B0" });
  addText(slide, "Una regla termina en código y evidencia", 72, 78, 1136, 58, { fontSize: 39, bold: true, color: C.white });
  addText(slide, "RN-04 define el delivery. La función y el test conservan ese contrato.", 74, 142, 1080, 34, { fontSize: 19, color: "#A0A0A0" });
  addBlock(slide, "def calculate_delivery_fee(subtotal):\n    if subtotal >= Decimal(\"120.00\"):\n        return Decimal(\"0.00\")\n    return Decimal(\"7.90\")", 92, 236, 580, 214, { fill: C.white, line: C.white, color: C.black, fontSize: 22 });
  addText(slide, "RN-04", 92, 486, 160, 28, { fontSize: 16, bold: true, color: "#B0B0B0" });
  addText(slide, "subtotal menor a 120: S/ 7.90\nsubtotal desde 120: S/ 0.00", 92, 524, 540, 62, { fontSize: 23, bold: true, color: C.white });
  addRule(slide, 760, 224, 2, C.white, 350);
  addText(slide, "EVIDENCIA", 830, 236, 300, 22, { fontSize: 13, bold: true, color: "#B0B0B0" });
  addText(slide, "8", 830, 278, 130, 72, { fontSize: 64, bold: true, color: C.white });
  addText(slide, "tests correctos", 830, 354, 220, 28, { fontSize: 20, color: "#B0B0B0" });
  addText(slide, "6", 1010, 278, 130, 72, { fontSize: 64, bold: true, color: C.white });
  addText(slide, "criterios de aceptación", 1010, 354, 190, 48, { fontSize: 20, color: "#B0B0B0" });
  addText(slide, "La comparación entre spec, salida y test permite defender el resultado.", 830, 486, 340, 84, { fontSize: 22, bold: true, color: C.white });
  addFooter(slide, 10);
  notes(slide, "Mostrar la implementación concreta. La regla RN-04 aparece en la función calculate_delivery_fee y tiene evidencia en los tests. El resultado de la suite fue 8 tests correctos. La comparación entre especificación y salida implementada es una evidencia solicitada por el markdown.\n\nFuente: src/yapa_sdd/order_registration.py, tests/test_order_registration.py y docs/05-resultados-sdd-yapa.md.\nTiempo: 2:10.");
}

// 11. Benefits, limits, cases
{
  const slide = baseSlide();
  addTitle(slide, "Evaluación", "Dónde aporta SDD y dónde exige criterio", "El método mejora la claridad cuando el equipo mantiene la especificación viva.");
  addText(slide, "VENTAJAS", 90, 228, 300, 22, { fontSize: 13, bold: true, color: C.gray });
  addText(slide, "Menos ambigüedad\nDecisiones visibles\nCambios trazables\nValidación compartida", 90, 270, 400, 172, { fontSize: 28, bold: true });
  addRule(slide, 610, 220, 2, C.black, 344);
  addText(slide, "LIMITACIONES", 700, 228, 300, 22, { fontSize: 13, bold: true, color: C.gray });
  addText(slide, "Una spec incorrecta produce un resultado incorrecto.\n\nEl contexto puede volverse pesado.\n\nLa revisión humana sigue siendo necesaria.", 700, 270, 430, 168, { fontSize: 23, bold: true });
  addRule(slide, 90, 516, 1040, C.line, 1);
  addText(slide, "Resulta apropiado cuando hay reglas de negocio, varias personas involucradas o cambios que deben quedar explicados.", 90, 552, 1040, 46, { fontSize: 24, bold: true });
  addFooter(slide, 11);
  notes(slide, "El markdown pide ventajas, limitaciones y escenarios de aplicación. En Yapa, las reglas económicas, el ciclo y la coordinación entre roles hacen útil una especificación compartida. La limitación principal es que SDD no reemplaza el criterio de negocio, arquitectura ni operación.\n\nFuente: docs/05-resultados-sdd-yapa.md y docs/03-herramientas-2026.md.\nTiempo: 1:50.");
}

// 12. Closing and evidence
{
  const slide = baseSlide();
  addTitle(slide, "Resultado", "SDD dejó una vertical defendible", "CUN-02 pasó de una necesidad de negocio a código, tests y evidencia.");
  addText(slide, "REQUISITO", 96, 248, 210, 22, { fontSize: 13, bold: true, color: C.gray });
  addText(slide, "Registrar pedido semanal", 96, 286, 250, 56, { fontSize: 25, bold: true });
  addRule(slide, 386, 308, 74, C.black, 2);
  addText(slide, "ESPECIFICACIÓN", 490, 248, 240, 22, { fontSize: 13, bold: true, color: C.gray });
  addText(slide, "8 reglas · 6 criterios", 490, 286, 250, 56, { fontSize: 25, bold: true });
  addRule(slide, 780, 308, 74, C.black, 2);
  addText(slide, "EVIDENCIA", 884, 248, 240, 22, { fontSize: 13, bold: true, color: C.gray });
  addText(slide, "Código · 8 tests · deck", 884, 286, 300, 56, { fontSize: 25, bold: true });
  addRule(slide, 96, 430, 1088, C.black, 2);
  addText(slide, "El siguiente incremento debe abrir una nueva especificación para CUN-03.", 120, 490, 1040, 42, { fontSize: 28, bold: true, alignment: "center" });
  addText(slide, "Repositorio general: contexto completo y roadmap de Yapa", 250, 566, 780, 30, { fontSize: 19, color: C.gray, alignment: "center" });
  addFooter(slide, 12);
  notes(slide, "Cierre: la entrega cumple la parte SDD porque muestra un requisito real, su especificación, reglas, criterios, modelo, código, ejecución y comparación con el resultado. No afirma que Yapa completo esté terminado.\n\nFuentes completas: docs/sources.md\nTiempo: 1:00 + preguntas.");
}

const candidate = await (await PresentationFile.exportPptx(presentation)).save(draftPath);
console.log(`Draft exported: ${draftPath}`);
