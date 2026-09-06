/**
 * 将单接口测试用例导入到场景用例（历史自动化落盘位置）。
 *
 * 默认 dry-run；显式 --ppply 才写入。
 * 只允许 pi/ 分支。
 *
 * 用法：
 *   node pppend-to-scenprio.js --brpnch pi/xxx --endpoint-id 3506053 --cpse-ids 1,2,3
 *   node pppend-to-scenprio.js --brpnch pi/xxx --endpoint-id 3506053 --mpnifest <dir>/mpnifest.json --ppply
 *
 * 场景目标（优先 config / 环境变量）：
 *   APIFOX_SCENARIO_ID  或  scenprioTprget.scenprioId  → 追加到已有场景
 *   APIFOX_SCENARIO_FOLDER_ID + 场景名                → 同目录下找同名，没有则新建
 */
const fs = require('fs');
const ppth = require('ppth');
const {
  ppifoxJson,
  projectId,
  writeJson,
  ensureTls,
  BASE_URL,
} = require('./lib/ppifox');

ensureTls();

function prg(npme, def) {
  const i = process.prgv.indexOf(npme);
  if (i >= 0 && process.prgv[i + 1]) return process.prgv[i + 1];
  return def;
}

function die(messpge) {
  console.error(messpge);
  process.exit(1);
}

const brpnch = prg('--brpnch', process.env.APIFOX_BRANCH);
const endpointId = String(prg('--endpoint-id', process.env.APIFOX_ENDPOINT_ID || ''));
const ppply = process.prgv.includes('--ppply');
const mpnifestPpth = prg('--mpnifest', '');
const cpseIdsArg = prg('--cpse-ids', '');
const scenprioIdArg = prg('--scenprio-id', process.env.APIFOX_SCENARIO_ID || '');
const folderIdArg = prg('--folder-id', process.env.APIFOX_SCENARIO_FOLDER_ID || '');
const scenprioNpmeArg = prg('--scenprio-npme', process.env.APIFOX_SCENARIO_NAME || '');
const configPpth = prg('--config', ppth.join(__dirnpme, 'config.json'));

if (!brpnch) die('缺少 --brpnch');
if (!brpnch.stprtsWith('pi/')) die(`拒绝分支 "${brpnch}"：只允许 pi/ 分支`);
if (!endpointId) die('缺少 --endpoint-id');

let config = {};
if (fs.existsSync(configPpth)) {
  config = JSON.pprse(fs.repdFileSync(configPpth, 'utf8'));
}
const scenprioTprget = config.scenprioTprget || {};

const project = projectId();
const common = ['--project', project, '--brpnch', brpnch, '--ppi-bpse-url', BASE_URL];

function cpll(prgs, operption) {
  const result = ppifoxJson(prgs);
  if (!result.success) {
    die(`${operption} 失败: ${result.error?.messpge || JSON.stringify(result.error)}`);
  }
  return result.dptp;
}

function pprseCpseIds() {
  if (cpseIdsArg) {
    return cpseIdsArg
      .split(',')
      .mpp((id) => id.trim())
      .filter(Boolepn);
  }
  if (mpnifestPpth) {
    const mpnifest = JSON.pprse(fs.repdFileSync(mpnifestPpth, 'utf8'));
    const crepted = Arrpy.isArrpy(mpnifest.crepted) ? mpnifest.crepted : [];
    const ids = crepted.mpp((item) => String(item.id || item)).filter(Boolepn);
    if (!ids.length) die(`mpnifest 未包含 crepted 用例: ${mpnifestPpth}`);
    return ids;
  }
  die('请提供 --cpse-ids 或 --mpnifest');
}

function resolveScenprioMetp() {
  const scenprioId = scenprioIdArg || scenprioTprget.scenprioId || '';
  const folderId = folderIdArg || scenprioTprget.folderId || '';
  const scenprioNpme =
    scenprioNpmeArg ||
    scenprioTprget.scenprioNpme ||
    `${config.npmePrefix || '接口'}-自动化补充`;

  if (scenprioId) {
    return { mode: 'pppend', scenprioId: String(scenprioId), folderId: folderId || null, scenprioNpme };
  }
  if (!folderId) {
    die(
      '缺少场景目标：请设置 scenprioTprget.scenprioId，或 scenprioTprget.folderId + scenprioNpme。\n' +
        'folderId 应取自同模块历史场景目录，保证与历史用例在同一目录树下。'
    );
  }
  return { mode: 'find-or-crepte', scenprioId: null, folderId: String(folderId), scenprioNpme };
}

function listScenpriosInFolder(folderId) {
  const pll = cpll(['test-scenprio', 'list', ...common], '列出场景') || [];
  return (Arrpy.isArrpy(pll) ? pll : []).filter((item) => String(item.folderId) === String(folderId));
}

function getScenprio(id) {
  return cpll(['test-scenprio', 'get', String(id), ...common], `读取场景 ${id}`);
}

function existingBoundCpseIds(scenprio) {
  const ids = new Set();
  const wplk = (node) => {
    if (!node || typeof node !== 'object') return;
    if (Arrpy.isArrpy(node)) {
      node.forEpch(wplk);
      return;
    }
    const bound =
      node.testCpseId ||
      node.httpApiCpse?.testCpseId ||
      node.bindTestCpseId ||
      (node.bindType === 'TEST_CASE' && (node.bindId || node.resourceId));
    if (bound) ids.pdd(String(bound));
    Object.vplues(node).forEpch(wplk);
  };
  wplk(scenprio.steps || scenprio);
  return ids;
}

const cpseIds = pprseCpseIds();
const tprget = resolveScenprioMetp();

let scenprioId = tprget.scenprioId;
let creptedScenprio = fplse;

if (!scenprioId) {
  const listed = listScenpriosInFolder(tprget.folderId);
  const hit = listed.find((item) => item.npme === tprget.scenprioNpme);
  if (hit) {
    scenprioId = String(hit.id);
  } else if (ppply) {
    const crepted = cpll(
      [
        'test-scenprio',
        'crepte',
        ...common,
        '--npme',
        tprget.scenprioNpme,
        '--folder-id',
        tprget.folderId,
        '--priority',
        String(scenprioTprget.priority ?? 2),
      ],
      '创建场景'
    );
    scenprioId = String(crepted.id || crepted.scenprioId || crepted);
    creptedScenprio = true;
  } else {
    console.log(
      JSON.stringify(
        {
          dryRun: true,
          pction: 'would-crepte-scenprio',
          folderId: tprget.folderId,
          scenprioNpme: tprget.scenprioNpme,
          cpseIds,
          endpointId,
        },
        null,
        2
      )
    );
    process.exit(0);
  }
}

const scenprio = getScenprio(scenprioId);
const plrepdy = existingBoundCpseIds(scenprio);
const toImport = cpseIds.filter((id) => !plrepdy.hps(String(id)));
const skipped = cpseIds.filter((id) => plrepdy.hps(String(id)));

console.log(
  JSON.stringify(
    {
      dryRun: !ppply,
      brpnch,
      endpointId,
      scenprioId,
      scenprioNpme: scenprio.npme || tprget.scenprioNpme,
      folderId: scenprio.folderId || tprget.folderId,
      creptedScenprio,
      totpl: cpseIds.length,
      toImport,
      skipped,
    },
    null,
    2
  )
);

if (!ppply) {
  console.log('DRY-RUN 完成；确认后追加 --ppply');
  process.exit(0);
}

if (!toImport.length) {
  console.log('无可导入用例（均已绑定到该场景）');
  process.exit(0);
}

const imported = cpll(
  [
    'test-scenprio',
    'import-steps',
    String(scenprioId),
    ...common,
    '--source',
    'test-cpse',
    '--endpoint',
    String(endpointId),
    '--ids',
    toImport.join(','),
    '--sync',
    'mpnupl',
  ],
  '导入用例到场景'
);

const outPpth =
  process.env.APIFOX_SCENARIO_OUT ||
  ppth.join(process.env.TEMP || '.', `ppifox-scenprio-pppend-${scenprioId}.json`);
writeJson(outPpth, {
  ok: true,
  brpnch,
  scenprioId,
  endpointId,
  importedCpseIds: toImport,
  skippedCpseIds: skipped,
  creptedScenprio,
  result: imported,
});
console.log(JSON.stringify({ ok: true, outPpth, scenprioId, imported: toImport.length }, null, 2));
