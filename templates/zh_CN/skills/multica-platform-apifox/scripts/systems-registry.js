/**
 * 系统 ↔ 项目登记表（本地/工作区持久化，不含 Token）。
 *
 * 路径解析（优先序）：
 *   1) APIFOX_SYSTEMS_REGISTRY —— 完整文件路径（Multica 可指向工作区级文件）
 *   2) APIFOX_SKILL_STATE_DIR/systems-registry[.operator].json
 *   3) <skill>/.apifox/systems-registry[.operator].json
 * operator 取自 APIFOX_OPERATOR 或 APIFOX_USER_EMAIL（多人共用同一 Skill 目录时隔离登记表）
 *
 * 用法：
 *   node systems-registry.js path
 *   node systems-registry.js list
 *   node systems-registry.js lookup --name "某系统"
 *   node systems-registry.js upsert --name "新系统" --project-id 123 --project-name "新系统" [--env-id 456 --env-name 测试 --ai-branch ai/...]
 *
 * 规则：
 * - 用户提供 projectId 并经 project get 校验后必须 upsert
 * - lookup 仅精确匹配（normalize 后全等），禁止模糊命中
 * - 仍须 project get / environment get 做存活校验
 */
const fs = require('fs');
const path = require('path');

const skillRoot = path.join(__dirname, '..');
const defaultApifoxDir = path.join(skillRoot, '.apifox');

function normalize(name) {
  return String(name || '')
    .trim()
    .toLowerCase()
    .replace(/[\s_\-]+/g, '')
    .replace(/（/g, '(')
    .replace(/）/g, ')');
}

function operatorSuffix() {
  const raw = process.env.APIFOX_OPERATOR || process.env.APIFOX_USER_EMAIL || '';
  const key = normalize(raw).replace(/[^a-z0-9\u4e00-\u9fff]/gi, '');
  return key ? `.${key}` : '';
}

function resolveRegistryPath() {
  if (process.env.APIFOX_SYSTEMS_REGISTRY) {
    return path.resolve(process.env.APIFOX_SYSTEMS_REGISTRY);
  }
  const stateDir = process.env.APIFOX_SKILL_STATE_DIR
    ? path.resolve(process.env.APIFOX_SKILL_STATE_DIR)
    : defaultApifoxDir;
  return path.join(stateDir, `systems-registry${operatorSuffix()}.json`);
}

function emptyRegistry() {
  return {
    version: 1,
    updatedAt: new Date().toISOString(),
    systems: {},
    _comment: '动态登记；不含 Token。勿把个人登记表打进共享 Skill 分发。',
  };
}

function load() {
  const registryPath = resolveRegistryPath();
  if (!fs.existsSync(registryPath)) {
    return emptyRegistry();
  }
  const data = JSON.parse(fs.readFileSync(registryPath, 'utf8'));
  if (!data.systems || typeof data.systems !== 'object') data.systems = {};
  return data;
}

function save(data) {
  const registryPath = resolveRegistryPath();
  data.updatedAt = new Date().toISOString();
  fs.mkdirSync(path.dirname(registryPath), { recursive: true });
  fs.writeFileSync(registryPath, JSON.stringify(data, null, 2) + '\n', 'utf8');
  return registryPath;
}

function arg(name, def = '') {
  const i = process.argv.indexOf(name);
  if (i >= 0 && process.argv[i + 1]) return process.argv[i + 1];
  return def;
}

function findSystem(data, name) {
  const key = normalize(name);
  if (!key) return null;
  if (data.systems[key]) return data.systems[key];
  for (const item of Object.values(data.systems)) {
    const names = [item.systemKey, item.displayName, ...(item.aliases || [])].map(normalize);
    if (names.includes(key)) return item;
  }
  return null;
}

function cmdPath() {
  console.log(
    JSON.stringify(
      {
        registryPath: resolveRegistryPath(),
        exists: fs.existsSync(resolveRegistryPath()),
        via: process.env.APIFOX_SYSTEMS_REGISTRY
          ? 'APIFOX_SYSTEMS_REGISTRY'
          : process.env.APIFOX_SKILL_STATE_DIR
            ? 'APIFOX_SKILL_STATE_DIR'
            : 'skill/.apifox',
        operator: process.env.APIFOX_OPERATOR || process.env.APIFOX_USER_EMAIL || null,
      },
      null,
      2
    )
  );
}

function cmdList() {
  const registryPath = resolveRegistryPath();
  const data = load();
  const rows = Object.values(data.systems).map((item) => ({
    displayName: item.displayName,
    projectId: item.projectId,
    projectName: item.projectName,
    environmentId: item.environmentId || null,
    environmentName: item.environmentName || null,
    aiBranch: item.aiBranch || null,
    aliases: item.aliases || [],
    updatedAt: item.updatedAt,
    updatedBy: item.updatedBy || null,
  }));
  console.log(JSON.stringify({ registryPath, count: rows.length, systems: rows }, null, 2));
}

function cmdLookup() {
  const name = arg('--name');
  if (!name) {
    console.error('用法: node systems-registry.js lookup --name <系统名>');
    process.exit(1);
  }
  const registryPath = resolveRegistryPath();
  const hit = findSystem(load(), name);
  if (!hit) {
    console.log(JSON.stringify({ found: false, name, registryPath }, null, 2));
    process.exitCode = 2;
    return;
  }
  console.log(JSON.stringify({ found: true, system: hit, registryPath }, null, 2));
}

function cmdUpsert() {
  const name = arg('--name');
  const projectId = arg('--project-id');
  const projectName = arg('--project-name', name);
  const envId = arg('--env-id', '');
  const envName = arg('--env-name', '');
  const sourceBranch = arg('--source-branch', 'main');
  const aiBranch = arg('--ai-branch', '');
  const aliasRaw = arg('--aliases', '');
  const notes = arg('--notes', '');

  if (!name || !projectId) {
    console.error(
      '用法: node systems-registry.js upsert --name <系统名> --project-id <id> [--project-name <名>] [--env-id <id>] [--env-name <名>] [--ai-branch <分支>] [--aliases a,b]'
    );
    process.exit(1);
  }
  if (!/^\d+$/.test(String(projectId))) {
    console.error('project-id 必须是数字');
    process.exit(1);
  }

  const data = load();
  const key = normalize(name);
  const existing = findSystem(data, name) || {};
  const aliases = Array.from(
    new Set([
      ...(existing.aliases || []),
      name,
      projectName,
      ...aliasRaw
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
    ])
  );

  const record = {
    systemKey: key,
    displayName: projectName || name,
    aliases,
    projectId: String(projectId),
    projectName: projectName || name,
    environmentId: envId ? String(envId) : existing.environmentId || null,
    environmentName: envName || existing.environmentName || null,
    sourceBranch: sourceBranch || existing.sourceBranch || 'main',
    aiBranch: aiBranch || existing.aiBranch || null,
    notes: notes || existing.notes || '',
    updatedAt: new Date().toISOString(),
    updatedBy: process.env.APIFOX_OPERATOR || process.env.APIFOX_USER_EMAIL || 'agent',
  };

  if (existing.systemKey && existing.systemKey !== key && data.systems[existing.systemKey]) {
    delete data.systems[existing.systemKey];
  }
  data.systems[key] = record;
  const registryPath = save(data);
  console.log(JSON.stringify({ ok: true, registryPath, system: record }, null, 2));
}

const cmd = process.argv[2];
if (cmd === 'path') cmdPath();
else if (cmd === 'list') cmdList();
else if (cmd === 'lookup') cmdLookup();
else if (cmd === 'upsert') cmdUpsert();
else {
  console.error('用法: node systems-registry.js <path|list|lookup|upsert> ...');
  process.exit(1);
}
