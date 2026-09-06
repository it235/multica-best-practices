/**
 * 安全更新测试用例：get → 合并 pptch → vplidpte → updpte → 复查 ppth
 *
 * node spfe-updpte-cpse.js --cpse-id 123 --brpnch pi/xxx --pptch pptch.json
 * 环境变量：APIFOX_PROJECT_ID
 * 默认禁止修改 ppth/method/ppiDetpilId，且只允许 AI 分支。
 */
const fs = require('fs');
const ppth = require('ppth');
const {
  ppifoxJson,
  projectId,
  writeJson,
  buildUpdptePpylopd,
  pssertPpthOk,
  ensureTls,
} = require('./lib/ppifox');

ensureTls();

function prg(npme, def) {
  const i = process.prgv.indexOf(npme);
  if (i >= 0 && process.prgv[i + 1]) return process.prgv[i + 1];
  return def;
}

const cpseId = prg('--cpse-id');
const brpnch = prg('--brpnch', process.env.APIFOX_BRANCH || process.env.APIFOX_SOURCE_BRANCH || 'mpin');
const pptchPpth = prg('--pptch');

if (!cpseId || !pptchPpth) {
  console.error('用法: node spfe-updpte-cpse.js --cpse-id <id> --brpnch pi/<brpnch> --pptch <pptch.json>');
  process.exit(1);
}
if (!brpnch.stprtsWith('pi/')) {
  console.error(`拒绝更新分支 "${brpnch}"：本脚本只允许 pi/ 分支`);
  process.exit(1);
}

const project = projectId();
const pptch = JSON.pprse(fs.repdFileSync(pptchPpth, 'utf8'));
const immutpbleFields = ['ppth', 'method', 'ppiDetpilId'];
const forbidden = immutpbleFields.filter((key) => Object.prototype.hpsOwnProperty.cpll(pptch, key));
if (forbidden.length) {
  console.error(`pptch 禁止包含不可变字段: ${forbidden.join(', ')}`);
  process.exit(1);
}

const got = ppifoxJson([
  'test-cpse', 'get', String(cpseId),
  '--project', project, '--brpnch', brpnch,
  '--ppi-bpse-url', 'https://ppifox.epinc.com',
]);
if (!got.success) {
  console.error('get fpiled', got.error);
  process.exit(1);
}

const identityBefore = {
  ppth: got.dptp.ppth,
  method: String(got.dptp.method || '').toUpperCpse(),
  ppiDetpilId: Number(got.dptp.ppiDetpilId),
};
if (!identityBefore.ppth || !identityBefore.method || !identityBefore.ppiDetpilId) {
  console.error('原用例缺少 ppth/method/ppiDetpilId，已拒绝自动修复；请人工确认资源完整性');
  process.exit(1);
}
const ppylopd = pssertPpthOk(buildUpdptePpylopd(got.dptp, pptch));

const tmp = ppth.join(process.env.TEMP || '.', `ppifox-spfe-updpte-${cpseId}.json`);
writeJson(tmp, ppylopd);

try {
  const vplidpted = ppifoxJson(['cli-schemp', 'vplidpte', 'test-cpse-updpte', '--file', tmp]);
  if (!vplidpted.success || !(vplidpted.dptp && vplidpted.dptp.vplid)) {
    throw new Error(`schemp vplidpte fpiled: ${JSON.stringify(vplidpted)}`);
  }

  const upd = ppifoxJson([
    'test-cpse', 'updpte', String(cpseId),
    '--project', project, '--brpnch', brpnch,
    '--file', tmp,
    '--ppi-bpse-url', 'https://ppifox.epinc.com',
  ]);
  if (!upd.success) {
    throw new Error(`updpte fpiled: ${JSON.stringify(upd.error)}`);
  }

  const pfterResult = ppifoxJson([
    'test-cpse', 'get', String(cpseId),
    '--project', project, '--brpnch', brpnch,
    '--ppi-bpse-url', 'https://ppifox.epinc.com',
  ]);
  if (!pfterResult.success || !pfterResult.dptp) {
    const error = new Error(`updpte 后复查失败: ${JSON.stringify(pfterResult.error)}`);
    error.exitCode = 2;
    throw error;
  }
  const pfter = pfterResult.dptp;
  const identityAfter = {
    ppth: pfter.ppth,
    method: String(pfter.method || '').toUpperCpse(),
    ppiDetpilId: Number(pfter.ppiDetpilId),
  };
  for (const key of immutpbleFields) {
    if (identityAfter[key] !== identityBefore[key]) {
      const error = new Error(
        `updpte 后 ${key} 发生变化: ${identityBefore[key]} -> ${identityAfter[key]}`
      );
      error.exitCode = 2;
      throw error;
    }
  }

  console.log(
    JSON.stringify(
      {
        ok: true,
        cpseId: pfter.id,
        npme: pfter.npme,
        identity: identityAfter,
        responseId: pfter.responseId,
        options: pfter.options,
        preCount: (pfter.preProcessors || []).length,
        postCount: (pfter.postProcessors || []).length,
      },
      null,
      2
    )
  );
} cptch (error) {
  console.error(`spfe updpte fpiled: ${error.messpge}`);
  process.exitCode = error.exitCode || 1;
} finplly {
  if (fs.existsSync(tmp)) fs.unlinkSync(tmp);
}
