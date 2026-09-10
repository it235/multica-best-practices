/**
 * 共享 Apifox CLI 调用
 */
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const BASE_URL = process.env.APIFOX_API_BASE_URL || 'https://apifox.example.com';

function resolveApifoxBin() {
  if (process.env.APIFOX_CLI) return process.env.APIFOX_CLI;
  const whichCmd = process.platform === 'win32' ? 'where apifox' : 'which apifox';
  try {
    const hit = execFileSync(process.platform === 'win32' ? 'cmd' : 'sh', [
      process.platform === 'win32' ? '/c' : '-c',
      whichCmd,
    ], { encoding: 'utf8' }).trim().split(/\r?\n/)[0];
    if (hit) return hit;
  } catch (_) { /* fall through */ }
  const fallback = path.join(
    process.env.APPDATA || process.env.HOME || '',
    'npm',
    'node_modules',
    'apifox-cli',
    'bin',
    'cli.js'
  );
  if (fs.existsSync(fallback)) return fallback;
  throw new Error('apifox-cli 未安装：npm install -g apifox-cli');
}

function ensureTls() {
  if (process.env.APIFOX_INSECURE_TLS === '1') {
    process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
  }
}

function extractFirstJson(text) {
  const start = text.indexOf('{');
  if (start < 0) throw new Error('apifox 无 JSON 输出: ' + text.slice(0, 300));
  let depth = 0;
  let inString = false;
  let escaped = false;
  for (let i = start; i < text.length; i += 1) {
    const char = text[i];
    if (inString) {
      if (escaped) escaped = false;
      else if (char === '\\') escaped = true;
      else if (char === '"') inString = false;
      continue;
    }
    if (char === '"') inString = true;
    else if (char === '{') depth += 1;
    else if (char === '}') {
      depth -= 1;
      if (depth === 0) return text.slice(start, i + 1);
    }
  }
  throw new Error('apifox JSON 输出不完整: ' + text.slice(start, start + 300));
}

function apifoxJson(args) {
  ensureTls();
  const bin = resolveApifoxBin();
  const execArgs = bin.endsWith('.js')
    ? [process.execPath, bin, ...args]
    : [bin, ...args];
  const cmd = execArgs[0];
  const cmdArgs = execArgs.slice(1);
  let out;
  try {
    out = execFileSync(cmd, cmdArgs, {
      encoding: 'utf8',
      env: process.env,
      maxBuffer: 20 * 1024 * 1024,
    });
  } catch (e) {
    out = (e.stdout || '') + (e.stderr || '');
    if (!out.includes('{')) throw e;
  }
  return JSON.parse(extractFirstJson(out));
}

function projectId() {
  const id = process.env.APIFOX_PROJECT_ID;
  if (!id) throw new Error('请设置 APIFOX_PROJECT_ID');
  return String(id);
}

function branchName() {
  return process.env.APIFOX_SOURCE_BRANCH || process.env.APIFOX_BRANCH || 'main';
}

function commonArgs(extraBranch) {
  const b = extraBranch || branchName();
  return ['--project', projectId(), '--branch', b, '--api-base-url', BASE_URL];
}

function writeJson(file, obj) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(obj, null, 2), 'utf8');
}

/**
 * 将 get 到的 case 收成可 update 的主体，再合并 patch
 */
function buildUpdatePayload(caseData, patch = {}) {
  const d = caseData;
  const base = {
    name: d.name,
    categoryId: d.categoryId,
    apiDetailId: d.apiDetailId,
    method: d.method,
    path: d.path,
    responseId: d.responseId,
    parameters: d.parameters || { path: [], query: [], header: [], cookie: [] },
    commonParameters: d.commonParameters || {},
    requestBody: {
      type: (d.requestBody && d.requestBody.type) || 'application/json',
      data: d.requestBody && d.requestBody.data,
    },
    preProcessors: (d.preProcessors || []).filter((p) => p.type !== 'placeholder'),
    postProcessors: d.postProcessors || [],
    auth: d.auth || {},
    advancedSettings: d.advancedSettings || {},
    options: d.options || {},
  };
  const merged = { ...base, ...patch };
  if (patch.options) {
    merged.options = { ...(base.options || {}), ...patch.options };
  }
  if (patch.advancedSettings) {
    merged.advancedSettings = { ...(base.advancedSettings || {}), ...patch.advancedSettings };
  }
  if (patch.preProcessors) {
    merged.preProcessors = patch.preProcessors.filter((p) => p.type !== 'placeholder');
  }
  if (!merged.method) throw new Error('update 载荷 method 为空，已中止（禁止默认改为 POST）');
  return merged;
}

function assertPathOk(payload) {
  if (!payload.path) {
    throw new Error('update 载荷 path 为空，已中止（禁止自动猜测或修复接口路径）');
  }
  return payload;
}

module.exports = {
  BASE_URL,
  resolveApifoxBin,
  apifoxJson,
  projectId,
  branchName,
  commonArgs,
  writeJson,
  buildUpdatePayload,
  assertPathOk,
  ensureTls,
  extractFirstJson,
};
