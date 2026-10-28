// Costruisce il sito statico per Vercel in ./site partendo da ./viewer.
// - avvolge viewer/index.html in un documento HTML completo (head con meta, title, stili)
// - copia gli STL/STEP da ./out in site/files/ e attiva la sezione download (window.SITE)
// Uso: node build-site.mjs
import { cpSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";

const OUT = "site";
rmSync(OUT, { recursive: true, force: true });
mkdirSync(`${OUT}/files`, { recursive: true });

cpSync("viewer", OUT, { recursive: true, filter: (p) => !p.endsWith("_tmp.stl") });
for (const f of readdirSync("out")) {
  if (/\.(stl|step)$/i.test(f)) cpSync(`out/${f}`, `${OUT}/files/${f}`);
}

const src = readFileSync("viewer/index.html", "utf8");
const cut = src.indexOf('<div class="app">');
const head = src.slice(0, cut).replace('<meta charset="utf-8">', "").replace(/<meta name="claude:[^>]*>\s*/, "");
const body = src.slice(cut);

writeFileSync(`${OUT}/index.html`, `<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="Cockpit triathlon stampabile in 3D per Canyon Speedmax CF: modello 3D, disegni tecnici e file STL/STEP.">
<script>window.SITE = true;</script>
${head.trim()}
</head>
<body>
${body.trim()}
</body>
</html>
`);

console.log(`sito in ./${OUT}: ${readdirSync(`${OUT}/files`).length} file di stampa`);
