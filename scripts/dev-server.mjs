import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';

const root = process.argv[2] ?? '.';
const types = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css' };
createServer(async (req, res) => {
  const urlPath = normalize(decodeURIComponent(new URL(req.url, 'http://localhost').pathname)).replace(/^[/\\]+/, '');
  const file = join(root, urlPath || 'index.html');
  try {
    const body = await readFile(file);
    res.writeHead(200, { 'content-type': types[extname(file)] ?? 'application/octet-stream' });
    res.end(body);
  } catch {
    res.writeHead(404);
    res.end('Not found');
  }
}).listen(5173, '0.0.0.0', () => console.log(`Serving ${root} on http://localhost:5173`));
