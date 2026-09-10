/**
 * 发现同模块历史场景目录，供补充用例挂载。
 * 输出：scenario-target.json
 *
 * 策略（WS-40 沉淀）：
 * - 同一 endpoint 默认只挂一个场景（selfHit → append-existing）
 * - 扩充覆盖 = 向该场景追加差异化步骤，禁止擅自 create 同接口多场景
 * - 仅当同接口尚无场景时，才允许 create-in-same-folder 新建一个
 *
 * 环境变量：APIFOX_PROJECT_ID、APIFOX_ENDPOINT_ID、APIFOX_SOURCE_BRANCH
 */
const path = require('path');
const {
  apifoxJson,
  projectId,
  branchName,
  writeJson,
  ensureTls,
  BASE_URL,
} = require('./lib/apifox');

ensureTls();

const endpointId = process.env.APIFOX_ENDPOINT_ID;
if (!endpointId) {
  console.error('请设置 APIFOX_ENDPOINT_ID');
  process.exit(1);
}

const project = projectId();
const branch = branchName();
const common = ['--project', project, '--branch', branch, '--api-base-url', BASE_URL];

function call(args, operation) {
  const result = apifoxJson(args);
  if (!result.success) {
    throw new Error(`${operation} 失败: ${result.error?.message || JSON.stringify(result.error)}`);
  }
  return result.data;
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function walk(value, visitor, seen = new Set()) {
  if (!value || typeof value !== 'object' || seen.has(value)) return;
  seen.add(value);
  visitor(value);
  if (Array.isArray(value)) {
    for (const child of value) walk(child, visitor, seen);
  } else {
    for (const child of Object.values(value)) walk(child, visitor, seen);
  }
}

const endpoint = call(['endpoint', 'get', String(endpointId), ...common], '读取接口');
const moduleId = endpoint.moduleId;
const endpointName = endpoint.name || `endpoint-${endpointId}`;

const moduleEndpoints = moduleId
  ? asArray(call(['endpoint', 'list', ...common, '--module-id', String(moduleId)], '列出同模块接口'))
  : [];
const moduleEndpointIds = new Set(moduleEndpoints.map((item) => String(item.id)));
moduleEndpointIds.add(String(endpointId));

const scenarios = asArray(call(['test-scenario', 'list', ...common], '列出场景'));
const candidates = [];

for (const item of scenarios) {
  const full = call(['test-scenario', 'get', String(item.id), ...common], `读取场景 ${item.id}`);
  let hitCount = 0;
  let selfHit = false;
  walk(full, (node) => {
    const referenced =
      node.apiDetailId ?? node.endpointId ?? node.httpApiCase?.apiDetailId ?? node.httpApiCase?.id;
    if (!referenced) return;
    const id = String(referenced);
    if (moduleEndpointIds.has(id)) hitCount += 1;
    if (id === String(endpointId)) selfHit = true;
  });
  if (!hitCount && !selfHit) continue;
  candidates.push({
    scenarioId: full.id,
    scenarioName: full.name,
    folderId: full.folderId,
    hitCount,
    selfHit,
  });
}

candidates.sort((a, b) => {
  if (a.selfHit !== b.selfHit) return a.selfHit ? -1 : 1;
  return b.hitCount - a.hitCount;
});

const best = candidates[0] || null;
const selfHitCount = candidates.filter((item) => item.selfHit).length;
const warnings = [];
if (selfHitCount > 1) {
  warnings.push(
    `同接口已出现在 ${selfHitCount} 个场景：默认向排序第一的场景 append-existing 追加步骤；禁止再新建同接口场景；除非用户明确要求，否则应收敛到单一场景`
  );
}

const result = {
  endpointId: Number(endpointId),
  endpointName,
  moduleId,
  branch,
  projectId: Number(project),
  policy: {
    oneEndpointOneScenario: true,
    expandByAppendingSteps: true,
    forbidCreateExtraScenarioWhenSelfHit: true,
    note: '用户说「扩充场景」默认=同场景加步骤，不是 create 多个场景',
  },
  warnings,
  recommended: best
    ? {
        mode: best.selfHit ? 'append-existing' : 'create-in-same-folder',
        scenarioId: best.selfHit ? best.scenarioId : null,
        folderId: best.folderId,
        scenarioName: best.selfHit ? best.scenarioName : `${endpointName}-自动化补充`,
        reason: best.selfHit
          ? '目标接口已出现在该场景：必须 append-existing 追加差异化步骤；禁止再 create 同接口多场景'
          : '同接口尚无场景；可在同模块历史目录新建【一个】补充场景，之后扩充继续追加到该场景',
      }
    : {
        mode: 'need-manual-folder',
        scenarioId: null,
        folderId: null,
        scenarioName: `${endpointName}-自动化补充`,
        reason: '未发现同模块历史场景，请人工指定 scenarioTarget.folderId',
      },
  candidates: candidates.slice(0, 20),
};

const outPath =
  process.env.APIFOX_SCENARIO_TARGET_OUT ||
  path.join(process.env.TEMP || '.', `apifox-scenario-target-${endpointId}.json`);
writeJson(outPath, result);
console.log(
  JSON.stringify(
    {
      outPath,
      recommended: result.recommended,
      policy: result.policy,
      warnings: result.warnings,
      candidateCount: candidates.length,
      selfHitCount,
    },
    null,
    2
  )
);
if (!result.recommended.folderId && !result.recommended.scenarioId) process.exitCode = 2;
