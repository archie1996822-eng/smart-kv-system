// Memory auto-generation pipeline
// Run: node .claude/memory/generate.mjs
import { readdirSync, readFileSync, writeFileSync, statSync } from 'fs';
import { join, relative, dirname } from 'path';
import { createHash } from 'crypto';

const ROOT = process.cwd();
const SRC = join(ROOT, 'src');
const MEMORY = join(ROOT, '.claude/memory/projects/smart-kv-system');
const GENERATED = join(MEMORY, 'generated');

function sha256(content) {
  return createHash('sha256').update(content).digest('hex').substring(0, 16);
}

function scanFiles(dir, ext = '.jsx,.js') {
  const exts = ext.split(',');
  const results = [];
  const queue = [dir];
  while (queue.length) {
    const current = queue.shift();
    const entries = readdirSync(current, { withFileTypes: true });
    for (const e of entries) {
      const full = join(current, e.name);
      if (e.isDirectory() && !e.name.startsWith('__')) queue.push(full);
      else if (e.isFile() && exts.some(x => e.name.endsWith(x.trim()))) {
        results.push(relative(ROOT, full));
      }
    }
  }
  return results.sort();
}

function extractExports(content) {
  const exports = [];
  const lines = content.split('\n');
  for (const line of lines) {
    const defExports = line.match(/export\s+default\s+function\s+(\w+)/);
    const namedExports = line.match(/export\s+(?:async\s+)?function\s+(\w+)/);
    const constExports = line.match(/export\s+(?:const|let|var)\s+(\w+)/);
    if (defExports) exports.push({ name: defExports[1], type: 'default' });
    else if (namedExports) exports.push({ name: namedExports[1], type: 'named' });
    else if (constExports) exports.push({ name: constExports[1], type: 'const' });
  }
  return exports;
}

function extractImports(content) {
  const imports = [];
  const lines = content.split('\n');
  for (const line of lines) {
    const m = line.match(/import\s+\{([^}]+)\}\s+from\s+['"]([^'"]+)['"]/);
    if (m) {
      imports.push({ names: m[1].split(',').map(s => s.trim()).filter(Boolean), from: m[2] });
    }
  }
  return imports;
}

function extractRoutes(content) {
  const routes = [];
  const lines = content.split('\n');
  for (const line of lines) {
    const m = line.match(/<Route\s+path="([^"]+)"\s+element=\{/);
    if (m) routes.push(m[1]);
  }
  return routes;
}

// === MAIN ===
console.log('🔍 Scanning source files...');
const files = scanFiles(SRC);
console.log(`   Found ${files.length} source files`);

// Generate manifest
const manifest = [];
const deps = {};
const checksums = {};

for (const file of files) {
  const content = readFileSync(join(ROOT, file), 'utf8');
  const hash = sha256(content);
  checksums[file] = hash;

  const exports = extractExports(content);
  const imports = extractImports(content);

  manifest.push({
    file,
    hash,
    size: statSync(join(ROOT, file)).size,
    exports: exports.map(e => e.name),
    imports_from: imports.map(i => i.from).filter(f => f.startsWith('.')),
  });

  // Build dependency graph
  deps[file] = imports.filter(i => i.from.startsWith('.')).map(i => i.from);
}

// Write manifest
writeFileSync(
  join(GENERATED, 'manifest.md'),
  `# Auto-Generated Manifest\n> Generated: ${new Date().toISOString()}\n> Files: ${files.length}\n\n` +
  `| File | Exports | Internal Imports | Size | Hash |\n` +
  `|------|---------|-----------------|------|------|\n` +
  manifest.map(m =>
    `| ${m.file} | ${m.exports.join(', ') || '—'} | ${m.imports_from.length} | ${(m.size / 1024).toFixed(1)}KB | ${m.hash} |`
  ).join('\n')
);

// Write dependencies
const depLines = ['# Module Dependency Graph', `> Generated: ${new Date().toISOString()}`, ''];
for (const [file, fileDeps] of Object.entries(deps).sort()) {
  if (fileDeps.length === 0) continue;
  depLines.push(`### ${file}`);
  for (const d of fileDeps) depLines.push(`- → ${d}`);
  depLines.push('');
}
writeFileSync(join(GENERATED, 'dependencies.md'), depLines.join('\n'));

// Extract routes
try {
  const appContent = readFileSync(join(ROOT, 'src/App.jsx'), 'utf8');
  const routes = extractRoutes(appContent);
  writeFileSync(
    join(GENERATED, 'routes.md'),
    `# Auto-Generated Routes\n> Generated: ${new Date().toISOString()}\n\n` +
    `| Route | Page Component | Auth Required |\n` +
    `|-------|---------------|---------------|\n` +
    routes.map(r => `| \`${r}\` | — | ${r === '/' || r === '/login' || r.startsWith('/share') ? 'No' : 'Yes'} |`).join('\n')
  );
} catch (e) { console.warn('Route extraction failed:', e.message); }

// Extract APIs
const apiFiles = files.filter(f => f.includes('Api') || f.includes('api'));
const apiLines = ['# Auto-Generated API Status', `> Generated: ${new Date().toISOString()}`, ''];
for (const file of apiFiles) {
  const content = readFileSync(join(ROOT, file), 'utf8');
  const urls = content.match(/https?:\/\/[^\s'"]+/g) || [];
  apiLines.push(`### ${file}`);
  for (const url of [...new Set(urls)]) apiLines.push(`- \`${url}\``);
  apiLines.push('');
}
writeFileSync(join(GENERATED, 'apis.md'), apiLines.join('\n'));

// Write integrity
const integrityData = {
  generated_at: new Date().toISOString(),
  version: Date.now(),
  total_files: files.length,
  total_size: Object.values(manifest).reduce((s, m) => s + m.size, 0),
};
writeFileSync(join(GENERATED, 'integrity.json'), JSON.stringify(integrityData, null, 2));

// Write checksums
writeFileSync(join(MEMORY, '.checksums'), JSON.stringify(checksums, null, 2));

// Update .config.json
const configPath = join(MEMORY, '.config.json');
const config = JSON.parse(readFileSync(configPath, 'utf8'));
config.memory_meta.version = integrityData.version;
config.memory_meta.total_files = files.length;
config.memory_meta.last_verified = new Date().toISOString();
writeFileSync(configPath, JSON.stringify(config, null, 2));

console.log('✅ Memory generation complete!');
console.log(`   Manifest: ${files.length} files`);
console.log(`   Routes: extracted`);
console.log(`   Dependencies: mapped`);
console.log(`   APIs: extracted`);
console.log(`   Checksums: ${Object.keys(checksums).length} files`);
console.log(`   Config: updated to v${integrityData.version}`);
