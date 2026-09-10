/**
 * Apifox 补充用例 JSON 生成器。
 * 条数完全由 caseSpecs 决定；无固定清单；证据、实测和预期均强校验。
 */
const fs = require('fs');
const path = require('path');

const skillDir = __dirname;
const configArgIndex = process.argv.indexOf('--config');
const userConfigPath =
  configArgIndex >= 0 && process.argv[configArgIndex + 1]
    ? path.resolve(process.argv[configArgIndex + 1])
    : path.join(skillDir, 'config.json');

function loadConfig() {
  if (!fs.existsSync(userConfigPath)) {
    console.error(
      `未找到 ${userConfigPath}\n` +
        '请复制 config.example.json 为 config.json，按当前接口改写 caseSpecs（条数随接口而定，勿照搬示例）。'
    );
    process.exit(1);
  }

  const fileConfig = JSON.parse(fs.readFileSync(userConfigPath, 'utf8'));

  const successResponseId =
    fileConfig.successResponseId ||
    fileConfig.endpoint?.responseId ||
    process.env.APIFOX_SUCCESS_RESPONSE_ID;

  return {
    fileConfig,
    apiDetailId: Number(process.env.APIFOX_ENDPOINT_ID || fileConfig.APIFOX_ENDPOINT_ID),
    method: fileConfig.endpoint?.method || 'post',
    apiPath: fileConfig.endpoint?.path,
    authPreProcessors: fileConfig.authPreProcessors || null,
    authDiscovery: fileConfig.authDiscovery,
    categories: fileConfig.categoryIds || { positive: 211, negative: 212, boundary: 213 },
    baseRequest: fileConfig.baseRequest || {},
    defaultSuccessResponseId: successResponseId,
    caseSpecs: fileConfig.caseSpecs,
    targetEnvironment: fileConfig.targetEnvironment,
    namePrefix: process.env.APIFOX_CASE_NAME_PREFIX || fileConfig.namePrefix || '接口',
    outputDir:
      process.env.APIFOX_CASE_OUTPUT_DIR ||
      path.join(process.env.TEMP || '/tmp', `apifox-cases-${process.env.APIFOX_ENDPOINT_ID || 'custom'}`),
  };
}

const cfg = loadConfig();

function die(message) {
  console.error(`配置错误: ${message}`);
  process.exit(1);
}

function nonEmpty(value) {
  return typeof value === 'string' && value.trim().length > 0;
}

function findSecret(value, trail = '') {
  if (!value || typeof value !== 'object') return null;
  for (const [key, child] of Object.entries(value)) {
    const here = trail ? `${trail}.${key}` : key;
    if (/access.?token|api.?token/i.test(key)) return here;
    if (typeof child === 'string' && /^afpp_/i.test(child)) return here;
    const nested = findSecret(child, here);
    if (nested) return nested;
  }
  return null;
}

const secretPath = findSecret(JSON.parse(fs.readFileSync(userConfigPath, 'utf8')));
if (secretPath) die(`${secretPath} 疑似包含 Token；Token 只能通过 APIFOX_ACCESS_TOKEN 环境变量提供`);
const projectIdRaw = String(cfg.fileConfig.APIFOX_PROJECT_ID || process.env.APIFOX_PROJECT_ID || '');
if (!projectIdRaw || /REPLACE_/i.test(projectIdRaw)) {
  die('APIFOX_PROJECT_ID 未设置或仍为占位符；禁止照搬 config.example.json');
}
if (!cfg.apiDetailId || !cfg.apiPath) die('缺少 APIFOX_ENDPOINT_ID 或 endpoint.path');
if (/REPLACE_/i.test(String(cfg.apiPath)) || /REPLACE_/i.test(String(cfg.apiDetailId))) {
  die('endpoint 仍为占位符；请按当前任务填写真实 method/path/ID');
}
if (/REPLACE_/i.test(String(cfg.targetEnvironment.id || '')) || /REPLACE_/i.test(String(cfg.targetEnvironment.name || ''))) {
  die('targetEnvironment 仍为占位符；环境 ID/名称须属于当前已确认项目');
}
if (!/^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)$/i.test(cfg.method)) die(`不支持的 method: ${cfg.method}`);
if (!cfg.targetEnvironment || cfg.targetEnvironment.type !== 'non-production') {
  die('targetEnvironment.type 必须明确为 non-production；默认禁止生产环境实测');
}
if (!nonEmpty(String(cfg.targetEnvironment.id || ''))) die('targetEnvironment.id 必填');
if (!Array.isArray(cfg.caseSpecs) || cfg.caseSpecs.length === 0) {
  die('caseSpecs 必须为非空数组；条数由场景证据决定，勿照搬示例');
}
if (!Array.isArray(cfg.authPreProcessors) || !cfg.authPreProcessors.length) {
  die('authPreProcessors 不能为空；请先运行 discover-auth.js 并人工确认发现结果');
}
if (!cfg.authDiscovery || !nonEmpty(cfg.authDiscovery.source) || !nonEmpty(cfg.authDiscovery.confidence)) {
  die('authDiscovery.source/confidence 必填，用于追溯鉴权来源');
}
if (!nonEmpty(String(cfg.authDiscovery.moduleId || '')) || !nonEmpty(String(cfg.authDiscovery.projectId || ''))) {
  die('authDiscovery.moduleId/projectId 必填：鉴权必须标注来自哪个项目+模块，禁止跨模块套用');
}
if (String(cfg.authDiscovery.projectId) !== String(cfg.fileConfig?.APIFOX_PROJECT_ID || process.env.APIFOX_PROJECT_ID || '')) {
  die('authDiscovery.projectId 必须与当前 APIFOX_PROJECT_ID 一致');
}
if (!['high', 'medium', 'low'].includes(cfg.authDiscovery.confidence)) {
  die('authDiscovery.confidence 必须为 high | medium | low');
}
if (cfg.authDiscovery.confidence !== 'high' && cfg.authDiscovery.confirmed !== true) {
  die('非 high 置信度鉴权结果必须设置 authDiscovery.confirmed=true，表示已人工确认');
}
if (!Array.isArray(cfg.authDiscovery.validatedScripts) || !cfg.authDiscovery.validatedScripts.length) {
  die('authDiscovery.validatedScripts 必填：须列出已在当前项目 common-script 校验通过的脚本 id/name');
}
for (const script of cfg.authDiscovery.validatedScripts) {
  if (!nonEmpty(String(script.id || '')) || /REPLACE_/i.test(String(script.id))) {
    die('validatedScripts 含占位符或空 id：请先对当前模块运行 discover-auth.js，禁止照搬示例');
  }
  if (!nonEmpty(String(script.name || '')) || /REPLACE_/i.test(String(script.name))) {
    die('validatedScripts.name 不能为空或占位符');
  }
}
for (const processor of cfg.authPreProcessors) {
  if (processor?.type !== 'commonScript' || !Array.isArray(processor.data)) continue;
  for (const id of processor.data) {
    if (/REPLACE_/i.test(String(id))) {
      die('authPreProcessors 含占位符脚本 ID：必须从同模块历史步骤原样拷贝');
    }
    const hit = cfg.authDiscovery.validatedScripts.find(
      (script) => String(script.id) === String(id) && nonEmpty(String(script.name || ''))
    );
    if (!hit) {
      die(
        `authPreProcessors 含未校验/未知脚本 ID ${id}。禁止跨项目/跨模块套用；请从同模块兄弟步骤 with-case-detail 原样拷贝`
      );
    }
  }
}

function assertion(name, subject, comparison, value, jsonPath = '') {
  // Apifox UI 回显 JSONPath 依赖 extractSettings.expression；需与 path 同值（对照手工用例）
  const extractSettings = {
    expression: jsonPath || '',
    continueExtractorSettings: { isContinueExtractValue: false },
  };
  return {
    type: 'assertion',
    data: { name, subject, comparison, value: String(value), path: jsonPath, extractSettings },
    defaultEnable: true,
    enable: true,
  };
}

function deepClone(value) {
  return value === undefined ? undefined : JSON.parse(JSON.stringify(value));
}

function deepMerge(base, patch) {
  if (Array.isArray(patch)) return deepClone(patch);
  if (!patch || typeof patch !== 'object') return patch;
  const out = base && typeof base === 'object' && !Array.isArray(base) ? deepClone(base) : {};
  for (const [key, value] of Object.entries(patch)) {
    out[key] =
      value && typeof value === 'object' && !Array.isArray(value)
        ? deepMerge(out[key], value)
        : deepClone(value);
  }
  return out;
}

function splitPath(dotPath) {
  return String(dotPath).split('.').filter(Boolean);
}

function setByPath(obj, dotPath, value) {
  const parts = splitPath(dotPath);
  if (!parts.length) die(`无效 override 路径: ${dotPath}`);
  let cur = obj;
  for (let i = 0; i < parts.length - 1; i += 1) {
    if (!cur[parts[i]] || typeof cur[parts[i]] !== 'object') cur[parts[i]] = {};
    cur = cur[parts[i]];
  }
  cur[parts.at(-1)] = deepClone(value);
}

function deleteByPath(obj, dotPath) {
  const parts = splitPath(dotPath);
  let cur = obj;
  for (let i = 0; i < parts.length - 1; i += 1) {
    if (!cur || typeof cur !== 'object') return;
    cur = cur[parts[i]];
  }
  if (cur && typeof cur === 'object') delete cur[parts.at(-1)];
}

function normalizeRequest(spec) {
  const req = deepMerge(cfg.baseRequest, spec.request || {});
  if (spec.bodyTransform) {
    const body = deepClone(req.requestBody?.data);
    if (!body || typeof body !== 'object' || Array.isArray(body)) {
      die(`${spec.nameSuffix}: bodyTransform 仅适用于对象型 JSON requestBody.data`);
    }
    for (const key of spec.bodyTransform.omit || []) deleteByPath(body, key);
    for (const [key, value] of Object.entries(spec.bodyTransform.override || {})) setByPath(body, key, value);
    req.requestBody = { ...(req.requestBody || {}), data: body };
  }
  req.parameters ||= { path: [], query: [], header: [], cookie: [] };
  req.commonParameters ||= {};
  if (req.requestBody && typeof req.requestBody.data !== 'string') {
    const type = String(req.requestBody.type || '');
    if (type.includes('json')) req.requestBody.data = JSON.stringify(req.requestBody.data);
  }
  return req;
}

function validateEvidence(spec, index) {
  const evidence = spec.evidence;
  if (!evidence || typeof evidence !== 'object') die(`caseSpecs[${index}].evidence 必须为对象`);
  if (!evidence.scenario || typeof evidence.scenario !== 'object') {
    die(`${spec.nameSuffix}: evidence.scenario 必填`);
  }
  const allowed = ['api-definition', 'requirement', 'existing-case', 'probe', 'combined'];
  if (!allowed.includes(evidence.scenario.type)) {
    die(`${spec.nameSuffix}: evidence.scenario.type 必须为 ${allowed.join(' | ')}`);
  }
  if (!nonEmpty(evidence.scenario.source) || !nonEmpty(evidence.scenario.summary)) {
    die(`${spec.nameSuffix}: evidence.scenario.source/summary 必填且不可为空`);
  }
  const probe = evidence.probe;
  if (!probe || typeof probe !== 'object') die(`${spec.nameSuffix}: evidence.probe 必填`);
  for (const field of ['environmentId', 'observedAt', 'responseSummary']) {
    if (!nonEmpty(String(probe[field] || ''))) die(`${spec.nameSuffix}: evidence.probe.${field} 必填`);
  }
  if (String(probe.environmentId) !== String(cfg.targetEnvironment.id)) {
    die(`${spec.nameSuffix}: probe.environmentId 必须与 targetEnvironment.id 一致`);
  }
  if (!Number.isInteger(Number(probe.statusCode))) die(`${spec.nameSuffix}: probe.statusCode 必须为整数`);
}

function resolveCategoryId(spec) {
  if (typeof spec.categoryId === 'number') return spec.categoryId;
  if (typeof spec.category === 'number') return spec.category;
  const key = String(spec.category || 'positive');
  const id = cfg.categories[key];
  if (!id) {
    die(`未知 category: ${key}，请配置 categoryIds.${key} 或直接写 categoryId`);
  }
  return id;
}

function buildAssertions(spec) {
  const expected = spec.expected;
  const status = String(expected.statusCode);
  const list = [assertion(`HTTP状态码${status}`, 'httpCode', 'equal', status)];
  for (const [jsonPath, value] of Object.entries(expected.hardEquals || {})) {
    list.push(assertion(`${jsonPath}=${value}`, 'responseJson', 'equal', value, jsonPath));
  }
  for (const jsonPath of expected.exists || []) {
    list.push(assertion(`${jsonPath}存在`, 'responseJson', 'exists', '', jsonPath));
  }
  for (const [jsonPath, value] of Object.entries(expected.includes || {})) {
    list.push(assertion(`${jsonPath}包含${value}`, 'responseJson', 'include', value, jsonPath));
  }
  for (const jsonPath of expected.notExists || []) {
    list.push(assertion(`${jsonPath}不存在`, 'responseJson', 'notExist', '', jsonPath));
  }
  return list;
}

function validateExpected(spec) {
  const expected = spec.expected;
  if (!expected || typeof expected !== 'object') die(`${spec.nameSuffix}: expected 必填`);
  if (!Number.isInteger(Number(expected.statusCode))) die(`${spec.nameSuffix}: expected.statusCode 必须为整数`);
  if (Number(expected.statusCode) !== Number(spec.evidence.probe.statusCode)) {
    die(`${spec.nameSuffix}: expected.statusCode 与实测 probe.statusCode 不一致`);
  }
  if (typeof expected.responseValidate !== 'boolean') {
    die(`${spec.nameSuffix}: expected.responseValidate 必须显式为 true/false`);
  }
  if (expected.responseValidate && !(expected.responseId || cfg.defaultSuccessResponseId)) {
    die(`${spec.nameSuffix}: 开启响应校验时必须提供 expected.responseId 或 successResponseId`);
  }
  if (!expected.responseValidate && expected.responseId && Number(expected.responseId) !== 0) {
    die(`${spec.nameSuffix}: 关闭响应校验时 responseId 必须为 0 或省略`);
  }
  const jsonPaths = [
    ...Object.keys(expected.hardEquals || {}),
    ...(expected.exists || []),
    ...Object.keys(expected.includes || {}),
    ...(expected.notExists || []),
  ];
  for (const jsonPath of jsonPaths) {
    if (!nonEmpty(jsonPath) || !jsonPath.startsWith('$')) {
      die(`${spec.nameSuffix}: 响应断言路径必须是 JSONPath（以 $ 开头）: ${jsonPath}`);
    }
  }
}

function validateSideEffect(spec) {
  const sideEffect = spec.sideEffect;
  if (!sideEffect || typeof sideEffect !== 'object') die(`${spec.nameSuffix}: sideEffect 必填`);
  if (!['none', 'read', 'write', 'destructive'].includes(sideEffect.level)) {
    die(`${spec.nameSuffix}: sideEffect.level 必须为 none | read | write | destructive`);
  }
  if (!nonEmpty(sideEffect.testData) || !nonEmpty(sideEffect.cleanup)) {
    die(`${spec.nameSuffix}: sideEffect.testData/cleanup 必填`);
  }
}

function mkCase(spec) {
  const req = normalizeRequest(spec);
  const expected = spec.expected;
  const responseId = expected.responseValidate
    ? expected.responseId || cfg.defaultSuccessResponseId
    : 0;
  return {
    name: `${cfg.namePrefix}-${spec.nameSuffix}`,
    categoryId: resolveCategoryId(spec),
    apiDetailId: cfg.apiDetailId,
    method: cfg.method,
    path: cfg.apiPath,
    responseId,
    parameters: req.parameters,
    commonParameters: req.commonParameters,
    ...(req.requestBody ? { requestBody: req.requestBody } : {}),
    preProcessors: spec.preProcessors !== undefined ? spec.preProcessors : cfg.authPreProcessors,
    postProcessors: [
      ...buildAssertions(spec),
      ...(Array.isArray(spec.postProcessors) ? spec.postProcessors : []),
    ],
    auth: req.auth || {},
    options: { ...(req.options || {}), responseValidate: expected.responseValidate },
    advancedSettings: req.advancedSettings || { disabledSystemHeaders: {} },
  };
}

const evidenceLines = [];
const names = new Set();
const files = new Set();
const prepared = [];
for (const [index, spec] of cfg.caseSpecs.entries()) {
  if (!nonEmpty(spec.nameSuffix)) die(`caseSpecs[${index}].nameSuffix 必填`);
  if (/未鉴权|未登录|unauth|no[-_ ]?auth/i.test(`${spec.nameSuffix} ${JSON.stringify(spec.evidence || {})}`)) {
    die(`${spec.nameSuffix}: 本 Skill 禁止生成未鉴权场景`);
  }
  validateEvidence(spec, index);
  validateExpected(spec);
  validateSideEffect(spec);
  const fullName = `${cfg.namePrefix}-${spec.nameSuffix}`;
  if (names.has(fullName)) die(`重复用例名: ${fullName}`);
  names.add(fullName);
  const file = spec.file || `${String(index + 1).padStart(2, '0')}-${spec.nameSuffix.replace(/[^\w\u4e00-\u9fff-]+/g, '_')}.json`;
  if (path.basename(file) !== file || !file.toLowerCase().endsWith('.json')) die(`${spec.nameSuffix}: file 必须是当前目录下的 .json 文件名`);
  if (files.has(file.toLowerCase())) die(`重复文件名: ${file}`);
  files.add(file.toLowerCase());
  prepared.push({ file, caseObject: mkCase(spec) });
  evidenceLines.push(
    `- ${fullName} | ${spec.evidence.scenario.type}: ${spec.evidence.scenario.source} | ` +
      `${spec.evidence.scenario.summary} | probe=${spec.evidence.probe.environmentId}@${spec.evidence.probe.observedAt}`
  );
}

if (process.argv.includes('--validate-only')) {
  console.log(`config valid: ${prepared.length} cases`);
  process.exit(0);
}

fs.mkdirSync(cfg.outputDir, { recursive: true });
for (const item of prepared) {
  fs.writeFileSync(path.join(cfg.outputDir, item.file), JSON.stringify(item.caseObject, null, 2), 'utf8');
}

fs.writeFileSync(
  path.join(cfg.outputDir, 'checklist.md'),
  `# 合并前自检\n\n` +
    `- [x] 条数=${cfg.caseSpecs.length}，均来自 caseSpecs（非固定模板）\n` +
    `- [x] 每条 evidence 和 probe 均通过结构化校验\n` +
    `- [ ] path 非空；鉴权来自同模块发现\n` +
    `- [ ] 负向 responseId=0 + responseValidate=false\n` +
    `- [ ] 正向绑定成功响应；断言已按实测校准\n` +
    `- [ ] 未生成未鉴权用例\n\n` +
    `## 本批用例与证据\n\n${evidenceLines.join('\n')}\n`
);

console.log(`written ${cfg.caseSpecs.length} cases to ${cfg.outputDir}`);
