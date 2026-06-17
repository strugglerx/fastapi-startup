import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const staticDir = resolve(process.cwd(), "../backend/app/public");
await mkdir(staticDir, { recursive: true });
await writeFile(resolve(staticDir, ".gitkeep"), "\n");
