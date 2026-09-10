#!/usr/bin/env node
/**
 * OpenAPI → Apifox 同步：导入增/改、打 Issue tag、删除带 tag 的 orphan endpoint。
 * 供 @BackendDev / multica-artifact-backend 在契约发布后调用。
 */
const fs = require('fs');
const path = require('path');
const { apifoxJson, projectId, branchName, commonArgs, writeJson } = require('./lib/apifox');

const HTTP_METHODS = new Set(['get', 'post', 'put', 'patch', 'delete', 'head', 'options']);

function parseArgs(argv) {
  const out = { file: '', issue: '', tag: '', branch: '', deleteOrphans: true, json: false };
  for (let i = 2; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === '--file' && argv[i + 1]) { out.file = argv[++i]; continue; }
    if (a === '--issue' && argv[i + 1]) { out.issue = argv[++i]; continue; }
    if (a === '--tag' && argv[i + 1]) { out.tag = argv[++i]; continue; }
    if (a === '--branch' && argv[i + 1]) { out.branch = argv[++i]; continue; }
    if (a === '--no-delete-orphans') { out.deleteOrphans = false; continue; }
    if (a === '--json') { out.json = true; continue; }
    if (a === '-h' || a === '--help') {
      console.log(`Usage: node sync_openapi.js --file openapi.json --issue ISSUE-KEY [--tag TAG] [--json]`);
      process.exit(0);
    }
  }
  if (!out.tag && out.issue) out.tag = out.issue;
  return out;
}

function loadOpenApiKeys(filePath) {
  const raw = JSON.parse(fs.readFileSync(filePath, 'utf8'));
  const keys = new Set();
  const paths = raw.paths || {};
  for (const [p, item] of Object.entries(paths)) {
    for (const [method] of Object.entries(item)) {
      if (!HTTP_METHODS.has(method.toLowerCase())) continue;
      keys.add(`${method.toUpperCase()} ${p}`);
    }
  }
  return keys;
}

function endpointKey(ep) {
  const method = (ep.method || ep.httpMethod || '').toUpperCase();
  const p = ep.path || ep.url || '';
  return `${method} ${p}`;
}

function mergeTags(existing, addTag) {
  const set = new Set();
  (existing || []).forEach((t) => { if (t) set.add(String(t).trim()); });
  if (addTag) set.add(addTag.trim());
  return [...set].filter(Boolean);
}

function tokenArgs() {
  const t = process.env.APIFOX_ACCESS_TOKEN;
  return t ? ['--access-token', t] : [];
}

async function main() {
  const args = parseArgs(process.argv);
  if (!args.file || !fs.existsSync(args.file)) {
    console.error('ERROR: --file <openapi.json> required');
    process.exit(1);
  }
  if (!args.tag) {
    console.error('ERROR: --issue or --tag required');
    process.exit(1);
  }

  const branch = args.branch || branchName();
  const openapiKeys = loadOpenApiKeys(args.file);
  const report = { issue: args.issue, tag: args.tag, imported: null, tagged: [], deleted: [], errors: [] };

  try {
    report.imported = apifoxJson([
      'import',
      ...tokenArgs(),
      ...commonArgs(branch),
      '--format', 'openapi',
      '--file', path.resolve(args.file),
    ]);
  } catch (e) {
    report.errors.push(`import: ${e.message}`);
  }

  let endpoints = [];
  try {
    const listed = apifoxJson(['endpoint', 'list', ...tokenArgs(), ...commonArgs(branch)]);
    endpoints = listed.data || listed.items || listed.endpoints || (Array.isArray(listed) ? listed : []);
  } catch (e) {
    report.errors.push(`endpoint list: ${e.message}`);
  }

  const byKey = new Map();
  for (const ep of endpoints) {
    const id = ep.id || ep.endpointId;
    if (!id) continue;
    byKey.set(endpointKey(ep), { id, ep });
  }

  for (const key of openapiKeys) {
    const hit = byKey.get(key);
    if (!hit) {
      report.errors.push(`tag miss: ${key} not found after import`);
      continue;
    }
    try {
      const detail = apifoxJson([
        'endpoint', 'get', String(hit.id),
        ...tokenArgs(),
        ...commonArgs(branch),
      ]);
      const data = detail.data || detail;
      const tags = mergeTags(data.tags || data.tagNames, args.tag);
      apifoxJson([
        'endpoint', 'update', String(hit.id),
        ...tokenArgs(),
        ...commonArgs(branch),
        '--tags', tags.join(','),
      ]);
      report.tagged.push({ key, endpointId: hit.id, tags });
    } catch (e) {
      report.errors.push(`tag ${key}: ${e.message}`);
    }
  }

  if (args.deleteOrphans) {
    for (const [key, hit] of byKey.entries()) {
      const ep = hit.ep;
      const tags = ep.tags || ep.tagNames || [];
      const tagList = Array.isArray(tags) ? tags : String(tags || '').split(',');
      if (!tagList.map((t) => t.trim()).includes(args.tag)) continue;
      if (openapiKeys.has(key)) continue;
      try {
        apifoxJson([
          'endpoint', 'delete', String(hit.id),
          ...tokenArgs(),
          ...commonArgs(branch),
        ]);
        report.deleted.push({ key, endpointId: hit.id });
      } catch (e) {
        report.errors.push(`delete ${key}: ${e.message}`);
      }
    }
  }

  const outFile = path.join(path.dirname(args.file), `apifox-sync-${args.tag.replace(/[^\w-]/g, '_')}.json`);
  writeJson(outFile, report);

  if (args.json) {
    console.log(JSON.stringify({ ...report, reportFile: outFile }, null, 2));
  } else {
    console.log(`tagged: ${report.tagged.length}, deleted: ${report.deleted.length}, errors: ${report.errors.length}`);
    console.log(`report: ${outFile}`);
  }

  process.exit(report.errors.length ? 1 : 0);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
