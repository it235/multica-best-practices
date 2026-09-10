/**
 * 将单接口测试用例导入到场景用例（历史自动化落盘位置）。
 *
 * 默认 dry-run；显式 --apply 才写入。
 * 只允许 ai/ 分支。
 *
 * 用法：
 *   node append-to-scenario.js --branch ai/xxx --endpoint-id 3506053 --case-ids 1,2,3
 *   node append-to-scenario.js --branch ai/xxx --endpoint-id 3506053 --manifest <dir>/manifest.json --apply
 *
 * 场景目标（优先 config / 环境变量）：
 *   APIFOX_SCENARIO_ID  或  scenarioTarget.scenarioId  → 追加到已有场景
 *   APIFOX_SCENARIO_FOLDER_ID + 场景名                → 同目录下找同名，没有则新建
 */
const fs = require('fs');
const path = require('path');
const {
  apifoxJson,
  projectId,
  writeJson,
  ensureTls,
  BASE_URL,
} = require('./lib/apifox');

ensureTls();

function arg(name, def) {
  const i = process.argv.indexOf(name);
  if (i >= 0 && process.argv[i + 1]) return process.argv[i + 1];
  return def;
}

function die(message) {
  console.error(message);
  process.exit(1);
}

const branch = arg('--branch', process.env.APIFOX_BRANCH);
const endpointId = String(arg('--endpoint-id', process.env.APIFOX_ENDPOINT_ID || ''));
const apply = process.argv.includes('--apply');
const manifestPath = arg('--manifest', '');
const caseIdsArg = arg('--case-ids', '');
const scenarioIdArg = arg('--scenario-id', process.env.APIFOX_SCENARIO_ID || '');
const folderIdArg = arg('--folder-id', process.env.APIFOX_SCENARIO_FOLDER_ID || '');
const scenarioNameArg = arg('--scenario-name', process.env.APIFOX_SCENARIO_NAME || '');
const configPath = arg('--config', path.join(__dirname, 'config.json'));

if (!branch) die('缺少 --branch');
if (!branch.startsWith('ai/')) die(`拒绝分支 "${branch}"：只允许 ai/ 分支`);
if (!endpointId) die('缺少 --endpoint-id');

let config = {};
if (fs.existsSync(configPath)) {
  config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
}
const scenarioTarget = config.scenarioTarget || {};

const project = projectId();
const common = ['--project', project, '--branch', branch, '--api-base-url', BASE_URL];

function call(args, operation) {
  const result = apifoxJson(args);
  if (!result.success) {
    die(`${operation} 失败: ${result.error?.message || JSON.stringify(result.error)}`);
  }
  return result.data;
}

function parseCaseIds() {
  if (caseIdsArg) {
    return caseIdsArg
      .split(',')
      .map((id) => id.trim())
      .filter(Boolean);
  }
  if (manifestPath) {
    const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
    const created = Array.isArray(manifest.created) ? manifest.created : [];
    const ids = created.map((item) => String(item.id || item)).filter(Boolean);
    if (!ids.length) die(`manifest 未包含 created 用例: ${manifestPath}`);
    return ids;
  }
  die('请提供 --case-ids 或 --manifest');
}

function resolveScenarioMeta() {
  const scenarioId = scenarioIdArg || scenarioTarget.scenarioId || '';
  const folderId = folderIdArg || scenarioTarget.folderId || '';
  const scenarioName =
    scenarioNameArg ||
    scenarioTarget.scenarioName ||
    `${config.namePrefix || '接口'}-自动化补充`;

  if (scenarioId) {
    return { mode: 'append', scenarioId: String(scenarioId), folderId: folderId || null, scenarioName };
  }
  if (!folderId) {
    die(
      '缺少场景目标：请设置 scenarioTarget.scenarioId，或 scenarioTarget.folderId + scenarioName。\n' +
        'folderId 应取自同模块历史场景目录，保证与历史用例在同一目录树下。'
    );
  }
  return { mode: 'find-or-create', scenarioId: null, folderId: String(folderId), scenarioName };
}

function listScenariosInFolder(folderId) {
  const all = call(['test-scenario', 'list', ...common], '列出场景') || [];
  return (Array.isArray(all) ? all : []).filter((item) => String(item.folderId) === String(folderId));
}

function getScenario(id) {
  return call(['test-scenario', 'get', String(id), ...common], `读取场景 ${id}`);
}

function existingBoundCaseIds(scenario) {
  const ids = new Set();
  const walk = (node) => {
    if (!node || typeof node !== 'object') return;
    if (Array.isArray(node)) {
      node.forEach(walk);
      return;
    }
    const bound =
      node.testCaseId ||
      node.httpApiCase?.testCaseId ||
      node.bindTestCaseId ||
      (node.bindType === 'TEST_CASE' && (node.bindId || node.resourceId));
    if (bound) ids.add(String(bound));
    Object.values(node).forEach(walk);
  };
  walk(scenario.steps || scenario);
  return ids;
}

const caseIds = parseCaseIds();
const target = resolveScenarioMeta();

let scenarioId = target.scenarioId;
let createdScenario = false;

if (!scenarioId) {
  const listed = listScenariosInFolder(target.folderId);
  const hit = listed.find((item) => item.name === target.scenarioName);
  if (hit) {
    scenarioId = String(hit.id);
  } else if (apply) {
    const created = call(
      [
        'test-scenario',
        'create',
        ...common,
        '--name',
        target.scenarioName,
        '--folder-id',
        target.folderId,
        '--priority',
        String(scenarioTarget.priority ?? 2),
      ],
      '创建场景'
    );
    scenarioId = String(created.id || created.scenarioId || created);
    createdScenario = true;
  } else {
    console.log(
      JSON.stringify(
        {
          dryRun: true,
          action: 'would-create-scenario',
          folderId: target.folderId,
          scenarioName: target.scenarioName,
          caseIds,
          endpointId,
        },
        null,
        2
      )
    );
    process.exit(0);
  }
}

const scenario = getScenario(scenarioId);
const already = existingBoundCaseIds(scenario);
const toImport = caseIds.filter((id) => !already.has(String(id)));
const skipped = caseIds.filter((id) => already.has(String(id)));

console.log(
  JSON.stringify(
    {
      dryRun: !apply,
      branch,
      endpointId,
      scenarioId,
      scenarioName: scenario.name || target.scenarioName,
      folderId: scenario.folderId || target.folderId,
      createdScenario,
      total: caseIds.length,
      toImport,
      skipped,
    },
    null,
    2
  )
);

if (!apply) {
  console.log('DRY-RUN 完成；确认后追加 --apply');
  process.exit(0);
}

if (!toImport.length) {
  console.log('无可导入用例（均已绑定到该场景）');
  process.exit(0);
}

const imported = call(
  [
    'test-scenario',
    'import-steps',
    String(scenarioId),
    ...common,
    '--source',
    'test-case',
    '--endpoint',
    String(endpointId),
    '--ids',
    toImport.join(','),
    '--sync',
    'manual',
  ],
  '导入用例到场景'
);

const outPath =
  process.env.APIFOX_SCENARIO_OUT ||
  path.join(process.env.TEMP || '.', `apifox-scenario-append-${scenarioId}.json`);
writeJson(outPath, {
  ok: true,
  branch,
  scenarioId,
  endpointId,
  importedCaseIds: toImport,
  skippedCaseIds: skipped,
  createdScenario,
  result: imported,
});
console.log(JSON.stringify({ ok: true, outPath, scenarioId, imported: toImport.length }, null, 2));
