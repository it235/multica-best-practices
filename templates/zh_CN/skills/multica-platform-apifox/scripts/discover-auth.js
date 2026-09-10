/**
 * 鉴权前置发现（只读，严格按「当前项目 + 目标模块」）。
 *
 * 硬规则：
 * - 禁止硬编码脚本 ID（不同项目/模块可能完全不同）
 * - 禁止跨模块自动采用
 * - 必须从同 moduleId 历史用例/场景 with-case-detail 原样拷贝
 * - commonScript ID 必须能在当前项目 common-script list 解析到
 * - 脚本库关键词仅作候选列表，永不自动写入
 */
const path = require('path');
const {
  apifoxJson,
  projectId,
  branchName,
  writeJson,
  ensureTls,
} = require('./lib/apifox');

ensureTls();

const endpointId = process.env.APIFOX_ENDPOINT_ID;
const preferredScenarioId = process.env.APIFOX_SCENARIO_ID || '';
if (!endpointId) {
  console.error('请设置 APIFOX_ENDPOINT_ID');
  process.exit(1);
}

const branch = branchName();
const project = projectId();
const AUTH_STEP_NAME = /登录|鉴权|认证|cookie|ticket|session|getCookie/i;

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

function deepClone(value) {
  return JSON.parse(JSON.stringify(value));
}

const endpoint = call(
  [
    'endpoint',
    'get',
    String(endpointId),
    '--project',
    project,
    '--branch',
    branch,
    '--api-base-url',
    'https://apifox.example.com',
  ],
  '读取目标接口'
);

const moduleId = endpoint.moduleId;
const folderId = endpoint.folderId;
if (!moduleId) {
  console.error('目标接口缺少 moduleId，无法做模块级鉴权发现');
  process.exit(1);
}

const scripts = asArray(
  call(['common-script', 'list', '--project', project, '--api-base-url', 'https://apifox.example.com'], '读取当前项目脚本库')
);
const scriptById = new Map(scripts.map((script) => [String(script.id), script]));

const moduleEndpoints = asArray(
  call(
    [
      'endpoint',
      'list',
      '--project',
      project,
      '--branch',
      branch,
      '--module-id',
      String(moduleId),
      '--api-base-url',
      'https://apifox.example.com',
    ],
    `列出同模块接口 moduleId=${moduleId}`
  )
);
const moduleEndpointIds = new Set(moduleEndpoints.map((item) => String(item.id)));
moduleEndpointIds.add(String(endpointId));

function validateCommonScriptIds(preProcessors) {
  const unknown = [];
  const resolved = [];
  for (const processor of asArray(preProcessors)) {
    if (processor.type !== 'commonScript' || !Array.isArray(processor.data)) continue;
    for (const id of processor.data) {
      const key = String(id);
      const script = scriptById.get(key);
      if (!script) unknown.push(key);
      else resolved.push({ id: script.id, name: script.name });
    }
  }
  return { unknown, resolved };
}

/**
 * 同模块历史前置即证据：不要求脚本名称含「登录」关键词。
 * 只要 preProcessors 非空且脚本 ID 在本项目可解析，即可作为候选。
 */
function analyzePreProcessors(preProcessors) {
  const cleaned = asArray(preProcessors)
    .filter((processor) => processor && processor.type && processor.type !== 'placeholder')
    .map(deepClone);
  if (!cleaned.length) return null;

  const { unknown, resolved } = validateCommonScriptIds(cleaned);
  if (unknown.length) {
    return { rejected: true, unknown, cleaned: null, resolvedScripts: [] };
  }

  const hasCommonOrCustom = cleaned.some(
    (processor) => processor.type === 'commonScript' || processor.type === 'customScript'
  );
  if (!hasCommonOrCustom) return null;

  return {
    rejected: false,
    cleaned,
    resolvedScripts: resolved,
    reasons: cleaned.map((processor) => {
      if (processor.type === 'commonScript') {
        return `commonScript:${(processor.data || [])
          .map((id) => scriptById.get(String(id))?.name || id)
          .join(',')}`;
      }
      return processor.type;
    }),
  };
}

const result = {
  endpointId: Number(endpointId),
  moduleId,
  folderId,
  branch,
  projectId: Number(project),
  preferredScenarioId: preferredScenarioId || null,
  authPreProcessors: null,
  scenarioAuthHttpSteps: [],
  source: null,
  confidence: 'none',
  requiresConfirmation: true,
  validatedScripts: [],
  candidates: [],
  // 仅展示，永不自动采用
  scriptLibraryCandidates: scripts.map((script) => ({ scriptId: script.id, scriptName: script.name })),
  warnings: [],
  policy: {
    scope: 'same-project + same-module only',
    hardCodeScriptIds: false,
    crossModuleAutoAdopt: false,
    scriptLibraryAutoAdopt: false,
  },
};

function addCandidate(item) {
  if (!moduleEndpointIds.has(String(item.endpointId || endpointId)) && item.source !== 'target-scenario') {
    // 非本模块接口来源一律丢弃
    if (item.endpointId && !moduleEndpointIds.has(String(item.endpointId))) return;
  }

  const confidence =
    item.source === 'target-scenario-same-endpoint'
      ? 'high'
      : item.source === 'target-scenario'
        ? 'high'
        : item.source === 'same-endpoint'
          ? 'high'
          : item.source === 'same-folder'
            ? 'medium'
            : item.source === 'same-module' || item.source === 'module-scenario'
              ? 'medium'
              : 'low';

  // 跨模块不应进入；若误入，强制 low + 必须确认且默认不推荐
  if (item.crossModule) return;

  result.candidates.push({ ...item, confidence });
}

function casesOnEndpoint(sourceEndpointId, source) {
  if (!moduleEndpointIds.has(String(sourceEndpointId))) return;

  const listed = asArray(
    call(
      [
        'test-case',
        'list',
        '--project',
        project,
        '--branch',
        branch,
        '--endpoint',
        String(sourceEndpointId),
        '--api-base-url',
        'https://apifox.example.com',
      ],
      `列出同模块接口 ${sourceEndpointId} 用例`
    )
  );

  for (const item of listed) {
    const full = call(
      [
        'test-case',
        'get',
        String(item.id),
        '--project',
        project,
        '--branch',
        branch,
        '--api-base-url',
        'https://apifox.example.com',
      ],
      `读取用例 ${item.id}`
    );
    const analyzed = analyzePreProcessors(full.preProcessors);
    if (!analyzed) continue;
    if (analyzed.rejected) {
      result.warnings.push({
        type: 'unknown-script-id',
        caseId: full.id,
        caseName: full.name,
        unknown: analyzed.unknown,
      });
      continue;
    }
    addCandidate({
      source,
      endpointId: sourceEndpointId,
      caseId: full.id,
      caseName: full.name,
      preProcessors: analyzed.cleaned,
      reasons: analyzed.reasons,
      resolvedScripts: analyzed.resolvedScripts,
    });
  }
}

function collectFromScenario(scenarioId, sourceHint) {
  const full = call(
    [
      'test-scenario',
      'get',
      String(scenarioId),
      '--project',
      project,
      '--branch',
      branch,
      '--with-case-detail',
      '--api-base-url',
      'https://apifox.example.com',
    ],
    `读取场景 ${scenarioId}（with-case-detail）`
  );

  let referencesTarget = false;
  let referencesModule = false;
  const authHttpSteps = [];

  for (const step of asArray(full.steps)) {
    const caseObj = step.httpApiCase || {};
    const apiId = caseObj.apiDetailId ?? step.apiDetailId;
    if (apiId && String(apiId) === String(endpointId)) referencesTarget = true;
    if (apiId && moduleEndpointIds.has(String(apiId))) referencesModule = true;

    if (AUTH_STEP_NAME.test(step.name || '') || AUTH_STEP_NAME.test(caseObj.name || '')) {
      authHttpSteps.push({
        name: step.name,
        apiDetailId: apiId || null,
        method: caseObj.method || null,
        path: caseObj.path || null,
      });
    }

    // 跳过「鉴权接口」这类步骤自身（通常无业务脚本）；取其兄弟业务步骤的前置
    if (AUTH_STEP_NAME.test(step.name || '') && !(caseObj.preProcessors || []).some((p) => p?.type === 'commonScript')) {
      continue;
    }

    const analyzed = analyzePreProcessors(caseObj.preProcessors || step.preProcessors);
    if (!analyzed) continue;
    if (analyzed.rejected) {
      result.warnings.push({
        type: 'unknown-script-id',
        scenarioId: full.id,
        stepName: step.name,
        unknown: analyzed.unknown,
      });
      continue;
    }

    let source = sourceHint;
    if (apiId && String(apiId) === String(endpointId)) source = 'target-scenario-same-endpoint';
    else if (sourceHint === 'target-scenario') source = 'target-scenario';
    else if (apiId && moduleEndpointIds.has(String(apiId))) source = 'module-scenario';
    else continue; // 场景步骤不属于本模块接口 → 丢弃

    addCandidate({
      source,
      scenarioId: full.id,
      scenarioName: full.name,
      stepName: step.name,
      endpointId: apiId,
      preProcessors: analyzed.cleaned,
      reasons: analyzed.reasons,
      resolvedScripts: analyzed.resolvedScripts,
    });
  }

  if (authHttpSteps.length && (referencesTarget || referencesModule)) {
    result.scenarioAuthHttpSteps.push({
      scenarioId: full.id,
      scenarioName: full.name,
      steps: authHttpSteps,
      note: '同模块场景含独立鉴权 HTTP 步骤；补充业务步骤须保留该模式，并复制同模块兄弟业务步骤的 preProcessors',
    });
  }

  return { referencesTarget, referencesModule, full };
}

// 1) 本接口用例
casesOnEndpoint(Number(endpointId), 'same-endpoint');

// 2) 同模块其他接口用例（同 folder 优先标记）
for (const item of moduleEndpoints) {
  if (String(item.id) === String(endpointId)) continue;
  const source = String(item.folderId) === String(folderId) ? 'same-folder' : 'same-module';
  casesOnEndpoint(item.id, source);
}

// 3) 指定挂载场景优先
if (preferredScenarioId) {
  collectFromScenario(preferredScenarioId, 'target-scenario');
}

// 4) 扫描场景，但只保留引用了本模块接口的场景
const scenarios = asArray(
  call(
    ['test-scenario', 'list', '--project', project, '--branch', branch, '--api-base-url', 'https://apifox.example.com'],
    '列出测试场景'
  )
);
for (const item of scenarios) {
  if (preferredScenarioId && String(item.id) === String(preferredScenarioId)) continue;
  const before = result.candidates.length;
  const { referencesTarget, referencesModule } = collectFromScenario(item.id, 'module-scenario');
  if (!referencesTarget && !referencesModule) {
    result.candidates = result.candidates.slice(0, before);
  }
}

function score(candidate) {
  const sourceScore = {
    'target-scenario-same-endpoint': 600,
    'target-scenario': 500,
    'same-endpoint': 450,
    'same-folder': 300,
    'same-module': 220,
    'module-scenario': 180,
  }[candidate.source] || 0;
  const sameEndpointBonus =
    candidate.endpointId && String(candidate.endpointId) === String(endpointId) ? 40 : 0;
  const signature = JSON.stringify(candidate.preProcessors);
  const frequency = result.candidates.filter((other) => JSON.stringify(other.preProcessors) === signature)
    .length;
  return sourceScore + sameEndpointBonus + frequency;
}

const ranked = [...result.candidates].sort((a, b) => score(b) - score(a));
if (ranked.length) {
  const best = ranked[0];
  const { unknown, resolved } = validateCommonScriptIds(best.preProcessors);
  if (unknown.length) {
    result.warnings.push({
      fatal: true,
      message: `推荐鉴权含当前项目不存在的脚本 ID: ${unknown.join(',')}`,
    });
  } else {
    result.authPreProcessors = best.preProcessors;
    result.validatedScripts = resolved;
    result.source = {
      type: best.source,
      moduleId,
      endpointId: best.endpointId,
      caseId: best.caseId || null,
      caseName: best.caseName || null,
      scenarioId: best.scenarioId || null,
      scenarioName: best.scenarioName || null,
      stepName: best.stepName || null,
      reasons: best.reasons,
      projectId: Number(project),
    };
    result.confidence = best.confidence;
    // 同模块同接口/目标场景可高置信；其余同模块仍建议确认
    result.requiresConfirmation = !['high'].includes(best.confidence);
  }
} else {
  result.warnings.push({
    fatal: true,
    message:
      '当前项目+模块未发现可校验的鉴权前置。禁止用脚本库关键词或其它项目/模块的脚本 ID 凑合写入。请人工指定同模块历史步骤。',
  });
}

const outPath =
  process.env.APIFOX_AUTH_OUT ||
  path.join(process.env.TEMP || '.', `apifox-auth-discovery-${endpointId}.json`);
writeJson(outPath, result);

console.log(
  JSON.stringify(
    {
      outPath,
      projectId: Number(project),
      moduleId,
      source: result.source,
      confidence: result.confidence,
      requiresConfirmation: result.requiresConfirmation,
      validatedScripts: result.validatedScripts,
      candidateCount: result.candidates.length,
      scenarioAuthHttpStepGroups: result.scenarioAuthHttpSteps.length,
      warningCount: result.warnings.length,
      policy: result.policy,
    },
    null,
    2
  )
);

if (!result.authPreProcessors) {
  console.warn('未发现「当前项目+同模块」可验证鉴权前置；禁止跨模块/硬编码脚本 ID。');
  process.exitCode = 2;
}
