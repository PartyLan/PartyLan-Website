import { cp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';

const outDir = 'dist';
await rm(outDir, { recursive: true, force: true });
await mkdir(join(outDir, 'src'), { recursive: true });
for (const file of ['index.html', 'src/main.js', 'src/content.js', 'src/styles.css']) {
  await mkdir(join(outDir, dirname(file)), { recursive: true });
  await cp(file, join(outDir, file));
}
const html = await readFile(join(outDir, 'index.html'), 'utf8');
await writeFile(join(outDir, 'index.html'), html.replace('/src/main.js', './src/main.js'));
console.log('Built static prototype to dist/');
