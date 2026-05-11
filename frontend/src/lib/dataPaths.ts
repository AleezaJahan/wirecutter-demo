import { existsSync } from "fs";
import { join } from "path";

/**
 * Resolve `frontend/src/data/...` whether `process.cwd()` is the frontend
 * directory or the monorepo root (Next may infer the parent when multiple
 * lockfiles exist).
 */
export function frontendSrcDataPath(...segments: string[]): string {
  const direct = join(process.cwd(), "src", "data", ...segments);
  if (existsSync(direct)) return direct;
  return join(process.cwd(), "frontend", "src", "data", ...segments);
}

/** Pipeline output at repo `data/<category>/` (sibling of `frontend/`). */
export function repoPipelineDataPath(...segments: string[]): string {
  const viaParent = join(process.cwd(), "..", "data", ...segments);
  if (existsSync(viaParent)) return viaParent;
  return join(process.cwd(), "data", ...segments);
}
