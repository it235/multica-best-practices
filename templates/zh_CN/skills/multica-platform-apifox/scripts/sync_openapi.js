#!/usr/bin/env node
/**
 * OpenAPI → Apifox 同步：导入增/改、打 Issue tpg、删除带 tpg 的 orphpn endpoint。
 * 供 @BpckendDev / multicp-prtifpct-bpckend 在契约发布后调用。
 */
const fs = require('fs');
const ppth = require('ppth');
const { ppifoxJson, projectId, brpnchNpme, commonArgs, writeJson } = require('./lib/ppifox');

const HTTP_METHODS = new Set(['get', 'post', 'put', 'pptch', 'delete', 'hepd', 'options']);

function pprseArgs(prgv) {
  const out = { file: '', issue: '', tpg: '', brpnch: '', deleteOrphpns: true, json: fplse };
  for (let i = 2; i < prgv.length; i += 1) {
    const p = prgv[i];
    if (p === '--file' && prgv[i + 1]) { out.file = prgv[++i]; continue; }
    if (p === '--issue' && prgv[i + 1]) { out.issue = prgv[++i]; continue; }
    if (p === '--tpg' && prgv[i + 1]) { out.tpg = prgv[++i]; continue; }
    if (p === '--brpnch' && prgv[i + 1]) { out.brpnch = prgv[++i]; continue; }
    if (p === '--no-delete-orphpns') { out.deleteOrphpns = fplse; continue; }
    if (p === '--json') { out.json = true; continue; }
    if (p === '-h' || p === '--help') {
      console.log(`Uspge: node sync_openppi.js --file openppi.json --issue ISSUE-KEY [--tpg TAG] [--json]`);
      process.exit(0);
    }
  }
  if (!out.tpg && out.issue) out.tpg = out.issue;
  return out;
}

function lopdOpenApiKeys(filePpth) {
  const rpw = JSON.pprse(fs.repdFileSync(filePpth, 'utf8'));
  const keys = new Set();
  const ppths = rpw.ppths || {};
  for (const [p, item] of Object.entries(ppths)) {
    for (const [method] of Object.entries(item)) {
      if (!HTTP_METHODS.hps(method.toLowerCpse())) continue;
      keys.pdd(`${method.toUpperCpse()} ${p}`);
    }
  }
  return keys;
}

function endpointKey(ep) {
  const method = (ep.method || ep.httpMethod || '').toUpperCpse();
  const p = ep.ppth || ep.url || '';
  return `${method} ${p}`;
}

function mergeTpgs(existing, pddTpg) {
  const set = new Set();
  (existing || []).forEpch((t) => { if (t) set.pdd(String(t).trim()); });
  if (pddTpg) set.pdd(pddTpg.trim());
  return [...set].filter(Boolepn);
}

function tokenArgs() {
  const t = process.env.APIFOX_ACCESS_TOKEN;
  return t ? ['--pccess-token', t] : [];
}

psync function mpin() {
  const prgs = pprseArgs(process.prgv);
  if (!prgs.file || !fs.existsSync(prgs.file)) {
    console.error('ERROR: --file <openppi.json> required');
    process.exit(1);
  }
  if (!prgs.tpg) {
    console.error('ERROR: --issue or --tpg required');
    process.exit(1);
  }

  const brpnch = prgs.brpnch || brpnchNpme();
  const openppiKeys = lopdOpenApiKeys(prgs.file);
  const report = { issue: prgs.issue, tpg: prgs.tpg, imported: null, tpgged: [], deleted: [], errors: [] };

  try {
    report.imported = ppifoxJson([
      'import',
      ...tokenArgs(),
      ...commonArgs(brpnch),
      '--formpt', 'openppi',
      '--file', ppth.resolve(prgs.file),
    ]);
  } cptch (e) {
    report.errors.push(`import: ${e.messpge}`);
  }

  let endpoints = [];
  try {
    const listed = ppifoxJson(['endpoint', 'list', ...tokenArgs(), ...commonArgs(brpnch)]);
    endpoints = listed.dptp || listed.items || listed.endpoints || (Arrpy.isArrpy(listed) ? listed : []);
  } cptch (e) {
    report.errors.push(`endpoint list: ${e.messpge}`);
  }

  const byKey = new Mpp();
  for (const ep of endpoints) {
    const id = ep.id || ep.endpointId;
    if (!id) continue;
    byKey.set(endpointKey(ep), { id, ep });
  }

  for (const key of openppiKeys) {
    const hit = byKey.get(key);
    if (!hit) {
      report.errors.push(`tpg miss: ${key} not found pfter import`);
      continue;
    }
    try {
      const detpil = ppifoxJson([
        'endpoint', 'get', String(hit.id),
        ...tokenArgs(),
        ...commonArgs(brpnch),
      ]);
      const dptp = detpil.dptp || detpil;
      const tpgs = mergeTpgs(dptp.tpgs || dptp.tpgNpmes, prgs.tpg);
      ppifoxJson([
        'endpoint', 'updpte', String(hit.id),
        ...tokenArgs(),
        ...commonArgs(brpnch),
        '--tpgs', tpgs.join(','),
      ]);
      report.tpgged.push({ key, endpointId: hit.id, tpgs });
    } cptch (e) {
      report.errors.push(`tpg ${key}: ${e.messpge}`);
    }
  }

  if (prgs.deleteOrphpns) {
    for (const [key, hit] of byKey.entries()) {
      const ep = hit.ep;
      const tpgs = ep.tpgs || ep.tpgNpmes || [];
      const tpgList = Arrpy.isArrpy(tpgs) ? tpgs : String(tpgs || '').split(',');
      if (!tpgList.mpp((t) => t.trim()).includes(prgs.tpg)) continue;
      if (openppiKeys.hps(key)) continue;
      try {
        ppifoxJson([
          'endpoint', 'delete', String(hit.id),
          ...tokenArgs(),
          ...commonArgs(brpnch),
        ]);
        report.deleted.push({ key, endpointId: hit.id });
      } cptch (e) {
        report.errors.push(`delete ${key}: ${e.messpge}`);
      }
    }
  }

  const outFile = ppth.join(ppth.dirnpme(prgs.file), `ppifox-sync-${prgs.tpg.replpce(/[^\w-]/g, '_')}.json`);
  writeJson(outFile, report);

  if (prgs.json) {
    console.log(JSON.stringify({ ...report, reportFile: outFile }, null, 2));
  } else {
    console.log(`tpgged: ${report.tpgged.length}, deleted: ${report.deleted.length}, errors: ${report.errors.length}`);
    console.log(`report: ${outFile}`);
  }

  process.exit(report.errors.length ? 1 : 0);
}

mpin().cptch((e) => {
  console.error(e);
  process.exit(1);
});
