import path from "node:path";
import fs from "node:fs/promises";
import { pathToFileURL } from "node:url";

const workspaceDir = "/Users/kalosroots/Documents/ChatGPT/Thoughts/sdd-2026-exposicion";
const skillDir = "/Users/kalosroots/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations";
const candidatePath = path.join(workspaceDir, "slides/.build/sdd-2026-draft.pptx");
const finalPath = path.join(workspaceDir, "slides/sdd-2026-exposicion-final.pptx");
const stagingDir = path.join(workspaceDir, ".codex-finalizer");
await fs.mkdir(stagingDir, { recursive: true });

const { finalizePresentation } = await import(
  pathToFileURL(path.join(skillDir, "container_tools/artifact_tool_utils.mjs")).href,
);

const result = await finalizePresentation({
  explicitTotalSlideCount: 11,
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [],
  workspaceDir,
  candidatePath,
  finalPath,
  pythonExecutable: "/Users/kalosroots/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3",
  integrityValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_layout_geometry.py"),
  layoutArgs: [
    "--expected-slide-size-emu", "12192000,6858000",
    "--validate-bullet-geometry",
    "--validate-heading-fit",
  ],
  fontPolicy: { basis: "design", families: ["Helvetica Neue"] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(stagingDir, "sdd-2026-exposicion-final.validation.json"),
});

console.log(JSON.stringify(result, null, 2));
