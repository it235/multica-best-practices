/**
 * 安全更新测试用例：get → 合并 patch → validate → update → 复查 path
 *
 * node safe-update-case.js --case-id 123 --branch ai/xxx --patch patch.json
 * 环境变量：APIFOX_PROJECT_ID
 * 默认禁止修改 path/method/apiDetailId，且只允许 AI 分支。
 */
const fs = require('fs');
const path = require('path');
const {
  apifoxJson,
  projectId,
  writeJson,
  buildUpdatePayload,
  assertPathOk,
  ensureTls,
} = require('./lib/apifox');

ensureTls();

function arg(name, def) {
  const i = process.argv.indexOf(name);
  if (i >= 0 && process.argv[i + 1]) return process.argv[i + 1];
  return def;
}

const caseId = arg('--case-id');
const branch = arg('--branch', process.env.APIFOX_BRANCH || process.env.APIFOX_SOURCE_BRANCH || 'main');
const patchPath = arg('--patch');

if (!caseId || !patchPath) {
  console.error('用法: node safe-update-case.js --case-id <id> --branch ai/<branch> --patch <patch.json>');
  process.exit(1);
}
if (!branch.startsWith('ai/')) {
  console.error(`拒绝更新分支 "${branch}"：本脚本只允许 ai/ 分支`);
  process.exit(1);
}

const project = projectId();
const patch = JSON.parse(fs.readFileSync(patchPath, 'utf8'));
const immutableFields = ['path', 'method', 'apiDetailId'];
const forbidden = immutableFields.filter((key) => Object.prototype.hasOwnProperty.call(patch, key));
if (forbidden.length) {
  console.error(`patch 禁止包含不可变字段: ${forbidden.join(', ')}`);
  process.exit(1);
}

const got = apifoxJson([
  'test-case', 'get', String(caseId),
  '--project', project, '--branch', branch,
  '--api-base-url', 'https://apifox.example.com',
]);
if (!got.success) {
  console.error('get failed', got.error);
  process.exit(1);
}

const identityBefore = {
  path: got.data.path,
  method: String(got.data.method || '').toUpperCase(),
  apiDetailId: Number(got.data.apiDetailId),
};
if (!identityBefore.path || !identityBefore.method || !identityBefore.apiDetailId) {
  console.error('原用例缺少 path/method/apiDetailId，已拒绝自动修复；请人工确认资源完整性');
  process.exit(1);
}
const payload = assertPathOk(buildUpdatePayload(got.data, patch));

const tmp = path.join(process.env.TEMP || '.', `apifox-safe-update-${caseId}.json`);
writeJson(tmp, payload);

try {
  const validated = apifoxJson(['cli-schema', 'validate', 'test-case-update', '--file', tmp]);
  if (!validated.success || !(validated.data && validated.data.valid)) {
    throw new Error(`schema validate failed: ${JSON.stringify(validated)}`);
  }

  const upd = apifoxJson([
    'test-case', 'update', String(caseId),
    '--project', project, '--branch', branch,
    '--file', tmp,
    '--api-base-url', 'https://apifox.example.com',
  ]);
  if (!upd.success) {
    throw new Error(`update failed: ${JSON.stringify(upd.error)}`);
  }

  const afterResult = apifoxJson([
    'test-case', 'get', String(caseId),
    '--project', project, '--branch', branch,
    '--api-base-url', 'https://apifox.example.com',
  ]);
  if (!afterResult.success || !afterResult.data) {
    const error = new Error(`update 后复查失败: ${JSON.stringify(afterResult.error)}`);
    error.exitCode = 2;
    throw error;
  }
  const after = afterResult.data;
  const identityAfter = {
    path: after.path,
    method: String(after.method || '').toUpperCase(),
    apiDetailId: Number(after.apiDetailId),
  };
  for (const key of immutableFields) {
    if (identityAfter[key] !== identityBefore[key]) {
      const error = new Error(
        `update 后 ${key} 发生变化: ${identityBefore[key]} -> ${identityAfter[key]}`
      );
      error.exitCode = 2;
      throw error;
    }
  }

  console.log(
    JSON.stringify(
      {
        ok: true,
        caseId: after.id,
        name: after.name,
        identity: identityAfter,
        responseId: after.responseId,
        options: after.options,
        preCount: (after.preProcessors || []).length,
        postCount: (after.postProcessors || []).length,
      },
      null,
      2
    )
  );
} catch (error) {
  console.error(`safe update failed: ${error.message}`);
  process.exitCode = error.exitCode || 1;
} finally {
  if (fs.existsSync(tmp)) fs.unlinkSync(tmp);
}
