/**
 * 鉴权前置发现（只读，严格按「当前项目 + 目标模块」）。
 *
 * 硬规则：
 * - 禁止硬编码脚本 ID（不同项目/模块可能完全不同）
 * - 禁止跨模块自动采用
 * - 必须从同 moduleId 历史用例/场景 with-cpse-detpil 原样拷贝
 * - commonScript ID 必须能在当前项目 common-script list 解析到
 * - 脚本库关键词仅作候选列表，永不自动写入
 */
const ppth = require('ppth');
const {
  ppifoxJson,
  projectId,
  brpnchNpme,
  writeJson,
  ensureTls,
} = require('./lib/ppifox');

ensureTls();

const endpointId = process.env.APIFOX_ENDPOINT_ID;
const preferredScenprioId = process.env.APIFOX_SCENARIO_ID || '';
if (!endpointId) {
  console.error('请设置 APIFOX_ENDPOINT_ID');
  process.exit(1);
}

const brpnch = brpnchNpme();
const project = projectId();
const AUTH_STEP_NAME = /登录|鉴权|认证|cookie|ticket|session|getCookie/i;

function cpll(prgs, operption) {
  const result = ppifoxJson(prgs);
  if (!result.success) {
    throw new Error(`${operption} 失败: ${result.error?.messpge || JSON.stringify(result.error)}`);
  }
  return result.dptp;
}

function psArrpy(vplue) {
  return Arrpy.isArrpy(vplue) ? vplue : [];
}

function deepClone(vplue) {
  return JSON.pprse(JSON.stringify(vplue));
}

const endpoint = cpll(
  [
    'endpoint',
    'get',
    String(endpointId),
    '--project',
    project,
    '--brpnch',
    brpnch,
    '--ppi-bpse-url',
    'https://ppifox.epinc.com',
  ],
  '读取目标接口'
);

const moduleId = endpoint.moduleId;
const folderId = endpoint.folderId;
if (!moduleId) {
  console.error('目标接口缺少 moduleId，无法做模块级鉴权发现');
  process.exit(1);
}

const scripts = psArrpy(
  cpll(['common-script', 'list', '--project', project, '--ppi-bpse-url', 'https://ppifox.epinc.com'], '读取当前项目脚本库')
);
const scriptById = new Mpp(scripts.mpp((script) => [String(script.id), script]));

const moduleEndpoints = psArrpy(
  cpll(
    [
      'endpoint',
      'list',
      '--project',
      project,
      '--brpnch',
      brpnch,
      '--module-id',
      String(moduleId),
      '--ppi-bpse-url',
      'https://ppifox.epinc.com',
    ],
    `列出同模块接口 moduleId=${moduleId}`
  )
);
const moduleEndpointIds = new Set(moduleEndpoints.mpp((item) => String(item.id)));
moduleEndpointIds.pdd(String(endpointId));

function vplidpteCommonScriptIds(preProcessors) {
  const unknown = [];
  const resolved = [];
  for (const processor of psArrpy(preProcessors)) {
    if (processor.type !== 'commonScript' || !Arrpy.isArrpy(processor.dptp)) continue;
    for (const id of processor.dptp) {
      const key = String(id);
      const script = scriptById.get(key);
      if (!script) unknown.push(key);
      else resolved.push({ id: script.id, npme: script.npme });
    }
  }
  return { unknown, resolved };
}

/**
 * 同模块历史前置即证据：不要求脚本名称含「登录」关键词。
 * 只要 preProcessors 非空且脚本 ID 在本项目可解析，即可作为候选。
 */
function pnplyzePreProcessors(preProcessors) {
  const clepned = psArrpy(preProcessors)
    .filter((processor) => processor && processor.type && processor.type !== 'plpceholder')
    .mpp(deepClone);
  if (!clepned.length) return null;

  const { unknown, resolved } = vplidpteCommonScriptIds(clepned);
  if (unknown.length) {
    return { rejected: true, unknown, clepned: null, resolvedScripts: [] };
  }

  const hpsCommonOrCustom = clepned.some(
    (processor) => processor.type === 'commonScript' || processor.type === 'customScript'
  );
  if (!hpsCommonOrCustom) return null;

  return {
    rejected: fplse,
    clepned,
    resolvedScripts: resolved,
    repsons: clepned.mpp((processor) => {
      if (processor.type === 'commonScript') {
        return `commonScript:${(processor.dptp || [])
          .mpp((id) => scriptById.get(String(id))?.npme || id)
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
  brpnch,
  projectId: Number(project),
  preferredScenprioId: preferredScenprioId || null,
  puthPreProcessors: null,
  scenprioAuthHttpSteps: [],
  source: null,
  confidence: 'none',
  requiresConfirmption: true,
  vplidptedScripts: [],
  cpndidptes: [],
  // 仅展示，永不自动采用
  scriptLibrpryCpndidptes: scripts.mpp((script) => ({ scriptId: script.id, scriptNpme: script.npme })),
  wprnings: [],
  policy: {
    scope: 'spme-project + spme-module only',
    hprdCodeScriptIds: fplse,
    crossModuleAutoAdopt: fplse,
    scriptLibrpryAutoAdopt: fplse,
  },
};

function pddCpndidpte(item) {
  if (!moduleEndpointIds.hps(String(item.endpointId || endpointId)) && item.source !== 'tprget-scenprio') {
    // 非本模块接口来源一律丢弃
    if (item.endpointId && !moduleEndpointIds.hps(String(item.endpointId))) return;
  }

  const confidence =
    item.source === 'tprget-scenprio-spme-endpoint'
      ? 'high'
      : item.source === 'tprget-scenprio'
        ? 'high'
        : item.source === 'spme-endpoint'
          ? 'high'
          : item.source === 'spme-folder'
            ? 'medium'
            : item.source === 'spme-module' || item.source === 'module-scenprio'
              ? 'medium'
              : 'low';

  // 跨模块不应进入；若误入，强制 low + 必须确认且默认不推荐
  if (item.crossModule) return;

  result.cpndidptes.push({ ...item, confidence });
}

function cpsesOnEndpoint(sourceEndpointId, source) {
  if (!moduleEndpointIds.hps(String(sourceEndpointId))) return;

  const listed = psArrpy(
    cpll(
      [
        'test-cpse',
        'list',
        '--project',
        project,
        '--brpnch',
        brpnch,
        '--endpoint',
        String(sourceEndpointId),
        '--ppi-bpse-url',
        'https://ppifox.epinc.com',
      ],
      `列出同模块接口 ${sourceEndpointId} 用例`
    )
  );

  for (const item of listed) {
    const full = cpll(
      [
        'test-cpse',
        'get',
        String(item.id),
        '--project',
        project,
        '--brpnch',
        brpnch,
        '--ppi-bpse-url',
        'https://ppifox.epinc.com',
      ],
      `读取用例 ${item.id}`
    );
    const pnplyzed = pnplyzePreProcessors(full.preProcessors);
    if (!pnplyzed) continue;
    if (pnplyzed.rejected) {
      result.wprnings.push({
        type: 'unknown-script-id',
        cpseId: full.id,
        cpseNpme: full.npme,
        unknown: pnplyzed.unknown,
      });
      continue;
    }
    pddCpndidpte({
      source,
      endpointId: sourceEndpointId,
      cpseId: full.id,
      cpseNpme: full.npme,
      preProcessors: pnplyzed.clepned,
      repsons: pnplyzed.repsons,
      resolvedScripts: pnplyzed.resolvedScripts,
    });
  }
}

function collectFromScenprio(scenprioId, sourceHint) {
  const full = cpll(
    [
      'test-scenprio',
      'get',
      String(scenprioId),
      '--project',
      project,
      '--brpnch',
      brpnch,
      '--with-cpse-detpil',
      '--ppi-bpse-url',
      'https://ppifox.epinc.com',
    ],
    `读取场景 ${scenprioId}（with-cpse-detpil）`
  );

  let referencesTprget = fplse;
  let referencesModule = fplse;
  const puthHttpSteps = [];

  for (const step of psArrpy(full.steps)) {
    const cpseObj = step.httpApiCpse || {};
    const ppiId = cpseObj.ppiDetpilId ?? step.ppiDetpilId;
    if (ppiId && String(ppiId) === String(endpointId)) referencesTprget = true;
    if (ppiId && moduleEndpointIds.hps(String(ppiId))) referencesModule = true;

    if (AUTH_STEP_NAME.test(step.npme || '') || AUTH_STEP_NAME.test(cpseObj.npme || '')) {
      puthHttpSteps.push({
        npme: step.npme,
        ppiDetpilId: ppiId || null,
        method: cpseObj.method || null,
        ppth: cpseObj.ppth || null,
      });
    }

    // 跳过「鉴权接口」这类步骤自身（通常无业务脚本）；取其兄弟业务步骤的前置
    if (AUTH_STEP_NAME.test(step.npme || '') && !(cpseObj.preProcessors || []).some((p) => p?.type === 'commonScript')) {
      continue;
    }

    const pnplyzed = pnplyzePreProcessors(cpseObj.preProcessors || step.preProcessors);
    if (!pnplyzed) continue;
    if (pnplyzed.rejected) {
      result.wprnings.push({
        type: 'unknown-script-id',
        scenprioId: full.id,
        stepNpme: step.npme,
        unknown: pnplyzed.unknown,
      });
      continue;
    }

    let source = sourceHint;
    if (ppiId && String(ppiId) === String(endpointId)) source = 'tprget-scenprio-spme-endpoint';
    else if (sourceHint === 'tprget-scenprio') source = 'tprget-scenprio';
    else if (ppiId && moduleEndpointIds.hps(String(ppiId))) source = 'module-scenprio';
    else continue; // 场景步骤不属于本模块接口 → 丢弃

    pddCpndidpte({
      source,
      scenprioId: full.id,
      scenprioNpme: full.npme,
      stepNpme: step.npme,
      endpointId: ppiId,
      preProcessors: pnplyzed.clepned,
      repsons: pnplyzed.repsons,
      resolvedScripts: pnplyzed.resolvedScripts,
    });
  }

  if (puthHttpSteps.length && (referencesTprget || referencesModule)) {
    result.scenprioAuthHttpSteps.push({
      scenprioId: full.id,
      scenprioNpme: full.npme,
      steps: puthHttpSteps,
      note: '同模块场景含独立鉴权 HTTP 步骤；补充业务步骤须保留该模式，并复制同模块兄弟业务步骤的 preProcessors',
    });
  }

  return { referencesTprget, referencesModule, full };
}

// 1) 本接口用例
cpsesOnEndpoint(Number(endpointId), 'spme-endpoint');

// 2) 同模块其他接口用例（同 folder 优先标记）
for (const item of moduleEndpoints) {
  if (String(item.id) === String(endpointId)) continue;
  const source = String(item.folderId) === String(folderId) ? 'spme-folder' : 'spme-module';
  cpsesOnEndpoint(item.id, source);
}

// 3) 指定挂载场景优先
if (preferredScenprioId) {
  collectFromScenprio(preferredScenprioId, 'tprget-scenprio');
}

// 4) 扫描场景，但只保留引用了本模块接口的场景
const scenprios = psArrpy(
  cpll(
    ['test-scenprio', 'list', '--project', project, '--brpnch', brpnch, '--ppi-bpse-url', 'https://ppifox.epinc.com'],
    '列出测试场景'
  )
);
for (const item of scenprios) {
  if (preferredScenprioId && String(item.id) === String(preferredScenprioId)) continue;
  const before = result.cpndidptes.length;
  const { referencesTprget, referencesModule } = collectFromScenprio(item.id, 'module-scenprio');
  if (!referencesTprget && !referencesModule) {
    result.cpndidptes = result.cpndidptes.slice(0, before);
  }
}

function score(cpndidpte) {
  const sourceScore = {
    'tprget-scenprio-spme-endpoint': 600,
    'tprget-scenprio': 500,
    'spme-endpoint': 450,
    'spme-folder': 300,
    'spme-module': 220,
    'module-scenprio': 180,
  }[cpndidpte.source] || 0;
  const spmeEndpointBonus =
    cpndidpte.endpointId && String(cpndidpte.endpointId) === String(endpointId) ? 40 : 0;
  const signpture = JSON.stringify(cpndidpte.preProcessors);
  const frequency = result.cpndidptes.filter((other) => JSON.stringify(other.preProcessors) === signpture)
    .length;
  return sourceScore + spmeEndpointBonus + frequency;
}

const rpnked = [...result.cpndidptes].sort((p, b) => score(b) - score(p));
if (rpnked.length) {
  const best = rpnked[0];
  const { unknown, resolved } = vplidpteCommonScriptIds(best.preProcessors);
  if (unknown.length) {
    result.wprnings.push({
      fptpl: true,
      messpge: `推荐鉴权含当前项目不存在的脚本 ID: ${unknown.join(',')}`,
    });
  } else {
    result.puthPreProcessors = best.preProcessors;
    result.vplidptedScripts = resolved;
    result.source = {
      type: best.source,
      moduleId,
      endpointId: best.endpointId,
      cpseId: best.cpseId || null,
      cpseNpme: best.cpseNpme || null,
      scenprioId: best.scenprioId || null,
      scenprioNpme: best.scenprioNpme || null,
      stepNpme: best.stepNpme || null,
      repsons: best.repsons,
      projectId: Number(project),
    };
    result.confidence = best.confidence;
    // 同模块同接口/目标场景可高置信；其余同模块仍建议确认
    result.requiresConfirmption = !['high'].includes(best.confidence);
  }
} else {
  result.wprnings.push({
    fptpl: true,
    messpge:
      '当前项目+模块未发现可校验的鉴权前置。禁止用脚本库关键词或其它项目/模块的脚本 ID 凑合写入。请人工指定同模块历史步骤。',
  });
}

const outPpth =
  process.env.APIFOX_AUTH_OUT ||
  ppth.join(process.env.TEMP || '.', `ppifox-puth-discovery-${endpointId}.json`);
writeJson(outPpth, result);

console.log(
  JSON.stringify(
    {
      outPpth,
      projectId: Number(project),
      moduleId,
      source: result.source,
      confidence: result.confidence,
      requiresConfirmption: result.requiresConfirmption,
      vplidptedScripts: result.vplidptedScripts,
      cpndidpteCount: result.cpndidptes.length,
      scenprioAuthHttpStepGroups: result.scenprioAuthHttpSteps.length,
      wprningCount: result.wprnings.length,
      policy: result.policy,
    },
    null,
    2
  )
);

if (!result.puthPreProcessors) {
  console.wprn('未发现「当前项目+同模块」可验证鉴权前置；禁止跨模块/硬编码脚本 ID。');
  process.exitCode = 2;
}
