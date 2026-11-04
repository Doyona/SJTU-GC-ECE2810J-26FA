import { cp, mkdir, readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { validateData } from '../site/leaderboard.mjs';

const root = new URL('../', import.meta.url);
const data = JSON.parse(await readFile(new URL('site/data/leaderboard.json', root), 'utf8'));
validateData(data);
await mkdir(new URL('dist/', root), { recursive: true });
// Explicitly publish only website files, never repository metadata or local files.
for (const path of ['index.html', 'styles.css', 'favicon.svg', 'app.mjs', 'leaderboard.mjs', 'data/leaderboard.json']) {
  await cp(new URL(`site/${path}`, root), new URL(`dist/${path}`, root), { recursive: true });
}
console.log(`Built ${data.projects.length} leaderboards → ${fileURLToPath(new URL('dist/', root))}`);
