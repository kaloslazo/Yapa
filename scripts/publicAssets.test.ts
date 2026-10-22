import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, extname } from 'node:path';
import { describe, expect, it } from 'vitest';

const ROOT = join(__dirname, '..');
const walk = (dir: string): string[] => readdirSync(dir).flatMap((name) => {
  const path = join(dir, name);
  return statSync(path).isDirectory() ? walk(path) : [path];
});

describe('archivos públicos (iteración 47)', () => {
  const images = walk(join(ROOT, 'public', 'images')).filter((path) => ['.png', '.jpg', '.jpeg', '.webp'].includes(extname(path)));

  it('ninguna imagen pesa más de 150 KB (PU-E)', () => {
    expect(images.length).toBeGreaterThan(0);
    for (const path of images) expect(statSync(path).size, path).toBeLessThanOrEqual(150 * 1024);
  });

  it('las imágenes propias son WebP, salvo la vista previa para compartir (PU-E)', () => {
    const notWebp = images.filter((path) => extname(path) !== '.webp').map((path) => path.split(/[\\/]/).pop());
    expect(notWebp).toEqual(['og-yapa.jpg']);
  });

  it('el código solo apunta a imágenes que existen', () => {
    const source = walk(join(ROOT, 'src')).filter((path) => /\.(tsx?|css)$/.test(path) && !path.endsWith('.test.ts')).map((path) => readFileSync(path, 'utf8')).join('\n');
    const used = [...source.matchAll(/\/images\/[\w/-]+\.(?:webp|png|jpg)/g)].map((match) => match[0]);
    expect(used.length).toBeGreaterThan(0);
    for (const url of new Set(used)) expect(() => statSync(join(ROOT, 'public', url)), url).not.toThrow();
  });

  it('la versión desplegada sale del commit de GitHub y va oculta en la página, no en el pie (DA-J)', () => {
    const config = readFileSync(join(ROOT, 'vite.config.ts'), 'utf8');
    expect(config).toContain('GITHUB_SHA');
    expect(config).toContain('yapa-build');
    expect(readFileSync(join(ROOT, 'src', 'App.tsx'), 'utf8')).not.toContain('__BUILD__'); // nadie la ve en la pantalla
  });

  it('index.html tiene favicon y las etiquetas para compartir con la imagen en dirección completa (PU-F)', () => {
    const html = readFileSync(join(ROOT, 'index.html'), 'utf8');
    expect(html).toContain('rel="icon"');
    expect(html).toContain('rel="apple-touch-icon"');
    for (const tag of ['og:title', 'og:description', 'og:image', 'og:url', 'og:type', 'twitter:card']) expect(html, tag).toContain(tag);
    expect(html).toMatch(/og:image" content="https:\/\/[^"]+\.jpg"/);
    for (const file of ['favicon.png', 'apple-touch-icon.png']) expect(() => statSync(join(ROOT, 'public', file)), file).not.toThrow();
  });
});
