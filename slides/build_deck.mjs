import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const workspaceDir = path.resolve(scriptDir, "..");
const skillDir = "/Users/kalosroots/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations";
const buildDir = path.join(scriptDir, ".build");
const draftPath = path.join(buildDir, "sdd-2026-draft.pptx");

await fs.mkdir(buildDir, { recursive: true });

const { resolvePresentationFont } = await import(
  pathToFileURL(path.join(skillDir, "container_tools/artifact_tool_utils.mjs")).href,
);

const FONT = resolvePresentationFont({ fontFamily: "Helvetica Neue" });
const C = {
  ink: "#0E1B2A",
  ink2: "#203247",
  cream: "#F6F2EA",
  white: "#FFFFFF",
  coral: "#FF6B4A",
  coralSoft: "#FFE0D7",
  teal: "#16A394",
  tealSoft: "#D7F3EF",
  amber: "#F4B740",
  gray: "#6B7785",
  line: "#D7DEE6",
  pale: "#EAF0F5",
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
    typeface: FONT,
    fontSize: opts.fontSize ?? 22,
    color: opts.color ?? C.ink,
    bold: opts.bold ?? false,
    italic: opts.italic ?? false,
    alignment: opts.alignment ?? "left",
    autoFit: "none",
  };
  return shape;
}

function addBox(slide, value, left, top, width, height, opts = {}) {
  const box = slide.shapes.add({
    geometry: opts.geometry ?? "roundRect",
    position: { left, top, width, height },
    fill: opts.fill ?? C.white,
    line: { style: "solid", fill: opts.line ?? C.line, width: opts.lineWidth ?? 1 },
    borderRadius: opts.radius ?? 18,
  });
  box.text = value;
  box.text.style = {
    typeface: FONT,
    fontSize: opts.fontSize ?? 22,
    color: opts.color ?? C.ink,
    bold: opts.bold ?? false,
    alignment: opts.alignment ?? "left",
    autoFit: "none",
  };
  return box;
}

function addTitle(slide, kicker, title, subtitle = "") {
  addText(slide, kicker.toUpperCase(), 72, 42, 700, 24, {
    fontSize: 14, bold: true, color: C.coral,
  });
  addText(slide, title, 72, 74, 1130, 60, {
    fontSize: 39, bold: true, color: C.ink,
  });
  if (subtitle) addText(slide, subtitle, 74, 140, 1080, 42, { fontSize: 20, color: C.gray });
}

function addFooter(slide, number) {
  addText(slide, `SDD · desarrollo de software · 2026`, 72, 686, 420, 18, { fontSize: 12, color: C.gray });
  addText(slide, String(number).padStart(2, "0"), 1170, 686, 38, 18, { fontSize: 12, bold: true, color: C.coral, alignment: "right" });
}

function notes(slide, text) {
  slide.speakerNotes.textFrame.setText(text);
}

function baseSlide(bg = C.cream) {
  const slide = presentation.slides.add();
  slide.background.fill = bg;
  return slide;
}

// 1. Cover
{
  const slide = baseSlide(C.ink);
  addText(slide, "SPEC-DRIVEN DEVELOPMENT", 72, 74, 700, 30, { fontSize: 16, bold: true, color: C.coral });
  addText(slide, "De la intención\na código verificable", 72, 138, 800, 170, { fontSize: 58, bold: true, color: C.cream });
  addText(slide, "Metodología, herramientas y un experimento pequeño con IA de código", 78, 354, 760, 56, { fontSize: 22, color: "#D3DCE5" });
  addBox(slide, "Corte de información\n19 septiembre 2026", 850, 128, 290, 118, { fill: C.coral, line: C.coral, color: C.white, fontSize: 22, bold: true });
  addBox(slide, "spec → plan → tasks → code → evidence", 850, 316, 330, 76, { fill: C.ink2, line: "#52657A", color: C.cream, fontSize: 18, bold: true });
  addText(slide, "Presentación ≤ 20 min", 78, 612, 300, 28, { fontSize: 16, color: "#AEBCC9" });
  notes(slide, "Apertura sugerida: en 2026 los agentes pueden escribir mucho código, pero el reto es conservar la intención, las decisiones y la evidencia. Esta charla muestra SDD con un ejemplo reproducible.\n\nFuente de contexto: https://github.github.com/spec-kit/\nCorte de investigación: 19/09/2026.");
}

// 2. Why now
{
  const slide = baseSlide();
  addTitle(slide, "Contexto", "El cuello de botella cambió", "El agente escribe; el equipo debe orientar, revisar y demostrar.");
  addBox(slide, "Prompt corto\n“Haz una app de tareas”", 80, 246, 300, 124, { fill: C.pale, line: C.line, fontSize: 24, bold: true });
  addBox(slide, "Supuestos ocultos\nID · persistencia · errores · límites", 490, 246, 300, 124, { fill: C.coralSoft, line: C.coral, color: C.ink, fontSize: 22, bold: true });
  addBox(slide, "Código que compila\npero quizá no cumple", 900, 246, 300, 124, { fill: C.tealSoft, line: C.teal, fontSize: 22, bold: true });
  // Thin visual dividers keep the narrative linear without adding copy.
  addText(slide, "La práctica SDD hace persistentes las decisiones que normalmente se pierden en el chat.", 110, 470, 1050, 50, { fontSize: 28, bold: true, color: C.ink, alignment: "center" });
  addText(slide, "La unidad de trabajo deja de ser solo el prompt: pasa a ser un conjunto revisable de artefactos.", 170, 540, 930, 36, { fontSize: 20, color: C.gray, alignment: "center" });
  addFooter(slide, 2);
  notes(slide, "Mensaje: el riesgo no es solo que el agente cometa un error de sintaxis. Es que complete silenciosamente decisiones de producto o arquitectura. SDD hace esas decisiones visibles.\n\nFuente: GitHub Spec Kit, What is SDD? https://github.com/github/spec-kit/blob/main/docs/concepts/sdd.md\nFuente: Kiro, What is spec-driven development? https://kiro.dev/\nTiempo: 1:30.");
}

// 3. Definition
{
  const slide = baseSlide();
  addTitle(slide, "Definición", "La spec conserva la intención", "Describe comportamiento observable antes de fijar el detalle de implementación.");
  addBox(slide, "QUÉ\nusuarios · reglas · casos límite\ncriterios de aceptación", 90, 235, 300, 190, { fill: C.coral, line: C.coral, color: C.white, fontSize: 25, bold: true });
  addBox(slide, "CÓMO\narquitectura · datos · interfaces\nrestricciones técnicas", 490, 235, 300, 190, { fill: C.teal, line: C.teal, color: C.white, fontSize: 25, bold: true });
  addBox(slide, "EVIDENCIA\npruebas · diff · convergencia\npendientes y riesgos", 890, 235, 300, 190, { fill: C.ink, line: C.ink, color: C.cream, fontSize: 25, bold: true });
  addText(slide, "En 2026 conviven niveles de rigor: spec-first, spec-anchored y spec-as-source.", 150, 502, 980, 42, { fontSize: 25, bold: true, color: C.ink, alignment: "center" });
  addText(slide, "El objetivo no es escribir más documentos. Es cerrar ambigüedad con trazabilidad.", 190, 562, 900, 34, { fontSize: 20, color: C.gray, alignment: "center" });
  addFooter(slide, 3);
  notes(slide, "Explicar la separación entre qué, cómo y evidencia. La spec puede ser lenguaje natural estructurado, contratos o modelos más formales. Para una charla de 20 minutos conviene presentar una adopción gradual: empezar con spec-first y subir el rigor cuando el riesgo lo justifique.\n\nFuente: Piskala, 2026, https://arxiv.org/abs/2602.00180\nFuente: GitHub, https://github.com/github/spec-kit/blob/main/docs/concepts/sdd.md\nTiempo: 2:00.");
}

// 4. Artifact chain
{
  const slide = baseSlide(C.ink);
  addText(slide, "CADENA DE ARTEFACTOS", 72, 42, 600, 24, { fontSize: 14, bold: true, color: C.coral });
  addText(slide, "Cada etapa responde una pregunta distinta", 72, 76, 1120, 60, { fontSize: 39, bold: true, color: C.cream });
  const labels = [
    ["Constitución", "¿qué límites?", C.coral],
    ["Spec", "¿qué debe pasar?", C.coralSoft],
    ["Plan", "¿cómo y por qué?", C.tealSoft],
    ["Tareas", "¿qué cambio?", C.amber],
    ["Código", "¿qué ejecuta?", C.teal],
    ["Pruebas", "¿qué evidencia?", C.cream],
  ];
  const boxes = [];
  let x = 72;
  for (const [head, sub, fill] of labels) {
    const box = addBox(slide, `${head}\n${sub}`, x, 246, 164, 112, { fill, line: fill, color: fill === C.ink ? C.cream : C.ink, fontSize: 20, bold: true, alignment: "center" });
    boxes.push(box);
    x += 190;
  }
  for (let i = 0; i < boxes.length - 1; i++) {
    slide.shapes.connect(boxes[i], boxes[i + 1], { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: "#7E93A9", width: 2 }, tail: { type: "triangle", width: "sm", length: "sm" } });
  }
  addBox(slide, "Convergencia\n¿qué quedó alineado?", 395, 480, 310, 94, { fill: C.coral, line: C.coral, color: C.white, fontSize: 22, bold: true, alignment: "center" });
  addText(slide, "La especificación no desaparece cuando empieza el código: se usa para revisar el resultado.", 170, 630, 940, 32, { fontSize: 20, color: "#C3D0DC", alignment: "center" });
  addFooter(slide, 4);
  notes(slide, "Recorrer la cadena. Constitución: reglas del proyecto. Spec: comportamiento. Plan: decisiones técnicas. Tareas: unidades ejecutables. Código y pruebas: implementación y evidencia. Convergencia: comparar lo que se construyó con lo que se pidió.\n\nFuente: GitHub Agentic SDD https://github.github.com/spec-kit/reference/agentic-sdd.html\nTiempo: 2:00.");
}

// 5. Workflow
{
  const slide = baseSlide();
  addTitle(slide, "Flujo", "La iteración buena cambia artefactos en orden", "Aclarar antes de diseñar; verificar después de implementar.");
  const steps = [
    ["1", "Aclarar", "supuestos y dudas"],
    ["2", "Especificar", "reglas observables"],
    ["3", "Planificar", "decisiones técnicas"],
    ["4", "Implementar", "tarea pequeña + test"],
    ["5", "Converger", "gaps y siguiente paso"],
  ];
  const boxes = [];
  let x = 78;
  for (const [n, h, s] of steps) {
    const box = addBox(slide, `${n}\n${h}\n${s}`, x, 242, 190, 144, { fill: n === "4" ? C.tealSoft : C.white, line: n === "4" ? C.teal : C.line, fontSize: 20, bold: true, alignment: "center" });
    boxes.push(box);
    x += 226;
  }
  for (let i = 0; i < boxes.length - 1; i++) {
    slide.shapes.connect(boxes[i], boxes[i + 1], { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.coral, width: 2 }, tail: { type: "triangle", width: "sm", length: "sm" } });
  }
  addBox(slide, "Quality gates opcionales\nchecklist · analyze · revisión humana", 300, 500, 680, 80, { fill: C.ink, line: C.ink, color: C.cream, fontSize: 22, bold: true, alignment: "center" });
  addFooter(slide, 5);
  notes(slide, "No todo cambio necesita la cadena completa. GitHub Spec Kit señala que specify antes de plan es el requisito mínimo; clarify, checklist y analyze son gates de calidad para trabajo ambiguo o de mayor riesgo.\n\nFuente: https://github.github.com/spec-kit/reference/agentic-sdd.html\nTiempo: 2:00.");
}

// 6. Tools
{
  const slide = baseSlide();
  addTitle(slide, "Ecosistema", "Herramientas 2026: método, agente y evidencia", "La metodología puede ser portable aunque cambie la interfaz.");
  addBox(slide, "Método\nGitHub Spec Kit\ncomandos y plantillas", 86, 238, 256, 168, { fill: C.coralSoft, line: C.coral, fontSize: 22, bold: true, alignment: "center" });
  addBox(slide, "IDE / agente\nKiro · Copilot · Codex\nClaude Code · Gemini CLI", 376, 238, 256, 168, { fill: C.tealSoft, line: C.teal, fontSize: 22, bold: true, alignment: "center" });
  addBox(slide, "Conocimiento\nTessl\nregistry + specs + tests", 666, 238, 256, 168, { fill: C.pale, line: C.line, fontSize: 22, bold: true, alignment: "center" });
  addBox(slide, "Evidencia\npytest / unittest\nCI · diff · seguridad", 956, 238, 236, 168, { fill: C.ink, line: C.ink, color: C.cream, fontSize: 22, bold: true, alignment: "center" });
  addText(slide, "Recomendación para empezar: Markdown versionado + tests + Git. Automatizar después.", 120, 508, 1040, 44, { fontSize: 27, bold: true, color: C.ink, alignment: "center" });
  addText(slide, "Elegir por integración, persistencia, privacidad, calidad y fricción de mantenimiento.", 180, 570, 920, 34, { fontSize: 20, color: C.gray, alignment: "center" });
  addFooter(slide, 6);
  notes(slide, "Presentar las herramientas como capas. Spec Kit estructura el flujo. Kiro ofrece una experiencia guiada con requisitos, diseño y tareas. Tessl añade specs vinculadas a tests y contexto versionado de librerías. Los agentes ejecutan el proceso. Los tests, CI y revisión prueban el resultado.\n\nFuentes: https://github.github.com/spec-kit/\nhttps://kiro.dev/docs/specs/best-practices/\nhttps://tessl.io/registry/tessl-labs/spec-driven-development/2.0.1/files/docs/index.md\nTiempo: 2:00.");
}

// 7. Example
{
  const slide = baseSlide(C.ink);
  addText(slide, "EJEMPLO", 72, 42, 520, 24, { fontSize: 14, bold: true, color: C.coral });
  addText(slide, "FocusList: una app pequeña, con reglas reales", 72, 76, 1120, 60, { fontSize: 39, bold: true, color: C.cream });
  addBox(slide, "Entrada a la IA\n“Gestiona tareas desde la terminal”", 84, 230, 330, 150, { fill: C.coral, line: C.coral, color: C.white, fontSize: 23, bold: true, alignment: "center" });
  addBox(slide, "Spec\nID incremental\nJSON local\n80 caracteres\nopen / done", 475, 210, 250, 190, { fill: C.cream, line: C.cream, color: C.ink, fontSize: 22, bold: true, alignment: "center" });
  addBox(slide, "Resultado\nCLI + 7 tests\ncomandos reproducibles\nlimitaciones explícitas", 790, 230, 330, 150, { fill: C.teal, line: C.teal, color: C.white, fontSize: 23, bold: true, alignment: "center" });
  addText(slide, "Archivos: spec → plan → tasks → src/ + tests/ → log", 180, 510, 920, 34, { fontSize: 26, bold: true, color: C.cream, alignment: "center" });
  addText(slide, "El documento no describe “una app bonita”; define comportamiento que se puede probar.", 190, 574, 900, 32, { fontSize: 20, color: "#C3D0DC", alignment: "center" });
  addFooter(slide, 7);
  notes(slide, "Explicar que el ejemplo es deliberadamente pequeño y portable. Los archivos están en docs/specs. La IA recibe primero la constitución, luego la spec, el plan y las tareas. El objetivo es mostrar el método, no presumir complejidad técnica.\n\nFuente local del repositorio: docs/specs/01-focuslist-spec.md\nTiempo: 2:00.");
}

// 8. Iteration
{
  const slide = baseSlide();
  addTitle(slide, "Iteración", "El cambio de requisito deja rastro", "Petición nueva: filtrar por estado y hacer idempotente `done`.");
  const rows = [
    ["Spec", "AC-02.3 / AC-02.4 + AC-03.2", C.coralSoft],
    ["Plan", "filtro explícito + retorno de cambio", C.tealSoft],
    ["Tasks", "T4 / T5 / T7", C.pale],
    ["Código", "list_tasks + complete_task", C.ink],
    ["Tests", "filtro + doble done", C.amber],
  ];
  let y = 220;
  for (const [label, body, fill] of rows) {
    addBox(slide, label, 132, y, 160, 54, { fill, line: fill, color: fill === C.ink ? C.cream : C.ink, fontSize: 20, bold: true, alignment: "center" });
    addText(slide, body, 345, y + 10, 700, 34, { fontSize: 23, bold: label === "Tests", color: C.ink });
    y += 78;
  }
  addBox(slide, "Orden de actualización", 860, 220, 270, 54, { fill: C.coral, line: C.coral, color: C.white, fontSize: 18, bold: true, alignment: "center" });
  addText(slide, "1  especificar\n2  planificar\n3  implementar\n4  verificar", 900, 300, 210, 150, { fontSize: 23, bold: true, color: C.ink });
  addText(slide, "La iteración es útil cuando reduce una incertidumbre y añade evidencia.", 185, 630, 900, 30, { fontSize: 20, color: C.gray, alignment: "center" });
  addFooter(slide, 8);
  notes(slide, "Este es el punto central de la demo. La petición nueva no se añade solo al código. Primero se actualizan los criterios de aceptación; luego plan y tareas; finalmente código y pruebas. La spec se convierte en memoria del cambio.\n\nFuente local: docs/iteration-log.md\nTiempo: 2:30.");
}

// 9. Evidence
{
  const slide = baseSlide();
  addTitle(slide, "Resultado", "Funcionó en el alcance que definimos", "La evidencia es suficiente para un piloto, no para prometer producción.");
  addBox(slide, "7", 120, 240, 180, 145, { fill: C.teal, line: C.teal, color: C.white, fontSize: 64, bold: true, alignment: "center" });
  addText(slide, "pruebas pasan", 115, 405, 190, 30, { fontSize: 20, bold: true, color: C.ink, alignment: "center" });
  addBox(slide, "0", 390, 240, 180, 145, { fill: C.coral, line: C.coral, color: C.white, fontSize: 64, bold: true, alignment: "center" });
  addText(slide, "dependencias runtime", 365, 405, 230, 30, { fontSize: 20, bold: true, color: C.ink, alignment: "center" });
  addBox(slide, "1", 660, 240, 180, 145, { fill: C.amber, line: C.amber, color: C.ink, fontSize: 64, bold: true, alignment: "center" });
  addText(slide, "cambio trazable", 645, 405, 210, 30, { fontSize: 20, bold: true, color: C.ink, alignment: "center" });
  addBox(slide, "Sí", 930, 240, 180, 145, { fill: C.ink, line: C.ink, color: C.cream, fontSize: 54, bold: true, alignment: "center" });
  addText(slide, "demo reproducible", 905, 405, 230, 30, { fontSize: 20, bold: true, color: C.ink, alignment: "center" });
  addText(slide, "Conclusión defendible: SDD redujo ambigüedad y facilitó revisión.", 150, 545, 980, 38, { fontSize: 27, bold: true, color: C.ink, alignment: "center" });
  addText(slide, "No medimos productividad comparativa ni calidad de producción.", 230, 602, 820, 28, { fontSize: 20, color: C.gray, alignment: "center" });
  addFooter(slide, 9);
  notes(slide, "Aclarar la diferencia entre evidencia local y generalización. Pasar tests confirma esos comportamientos. No confirma rendimiento, seguridad, operación ni valor de negocio. Thoughtworks clasifica Spec Kit como Assess y reporta beneficios junto con problemas como instruction bloat y context rot.\n\nFuentes: docs/05-resultados-experimento.md\nhttps://www.thoughtworks.com/content/dam/thoughtworks/documents/radar/2026/04/tr_technology_radar_vol_34_en.pdf\nTiempo: 2:00.");
}

// 10. Limits
{
  const slide = baseSlide(C.ink);
  addText(slide, "LÍMITES", 72, 42, 500, 24, { fontSize: 14, bold: true, color: C.coral });
  addText(slide, "Dónde SDD todavía necesita criterio", 72, 76, 1120, 60, { fontSize: 39, bold: true, color: C.cream });
  addBox(slide, "Context rot\nMás instrucciones no siempre ayudan.", 100, 220, 320, 142, { fill: C.coral, line: C.coral, color: C.white, fontSize: 23, bold: true, alignment: "center" });
  addBox(slide, "Falsa precisión\nUna spec incorrecta sigue siendo incorrecta.", 480, 220, 320, 142, { fill: C.amber, line: C.amber, color: C.ink, fontSize: 23, bold: true, alignment: "center" });
  addBox(slide, "Burocracia\nSi no decide ni se prueba, sobra.", 860, 220, 320, 142, { fill: C.teal, line: C.teal, color: C.white, fontSize: 23, bold: true, alignment: "center" });
  addText(slide, "La persona responsable sigue aprobando alcance, arquitectura, riesgos y aceptación.", 145, 505, 990, 46, { fontSize: 27, bold: true, color: C.cream, alignment: "center" });
  addText(slide, "La IA puede producir artefactos. El equipo decide si esos artefactos describen el producto correcto.", 185, 580, 910, 34, { fontSize: 20, color: "#C3D0DC", alignment: "center" });
  addFooter(slide, 10);
  notes(slide, "Thoughtworks reporta instruction bloat, context rot, validaciones defensivas innecesarias y Markdown verboso. La respuesta no es abandonar SDD sino simplificar plantillas, cargar contexto bajo demanda y revisar con experiencia de arquitectura.\n\nFuente: Thoughtworks Technology Radar Vol. 34, entrada GitHub Spec Kit, abril 2026.\nTiempo: 1:45.");
}

// 11. Close
{
  const slide = baseSlide();
  addTitle(slide, "Cierre", "Empezar pequeño, medir y mantener la cadena", "SDD es una forma de hacer explícita la colaboración entre producto, ingeniería e IA.");
  addBox(slide, "1\nUna funcionalidad\ncon reglas reales", 160, 250, 250, 160, { fill: C.coralSoft, line: C.coral, fontSize: 24, bold: true, alignment: "center" });
  addBox(slide, "2\nSpec versionada\ncon aceptación", 515, 250, 250, 160, { fill: C.tealSoft, line: C.teal, fontSize: 24, bold: true, alignment: "center" });
  addBox(slide, "3\nTests y diff\ncomo evidencia", 870, 250, 250, 160, { fill: C.ink, line: C.ink, color: C.cream, fontSize: 24, bold: true, alignment: "center" });
  addText(slide, "La velocidad de la IA vale más cuando el equipo puede explicar qué construyó y por qué.", 150, 535, 980, 52, { fontSize: 30, bold: true, color: C.ink, alignment: "center" });
  addText(slide, "Fuentes y material completo: docs/ · código: src/ · pruebas: tests/", 220, 620, 840, 28, { fontSize: 18, color: C.gray, alignment: "center" });
  addFooter(slide, 11);
  notes(slide, "Cierre: invitar a probar el flujo con una funcionalidad acotada y medir retrabajo, defectos y coste de mantenimiento de las specs.\n\nFuentes completas: docs/sources.md\nTiempo: 1:00 + preguntas.");
}

const candidate = await (await PresentationFile.exportPptx(presentation)).save(draftPath);
console.log(`Draft exported: ${draftPath}`);
