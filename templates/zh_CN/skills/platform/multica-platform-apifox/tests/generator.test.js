const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const root = path.resolve(__dirname, '..');
const generator = path.join(root, 'scripts', 'generate-cases.js');
const example = JSON.parse(
  fs.readFileSync(path.join(root, 'scripts', 'config.example.json'), 'utf8')
);
const validFixture = JSON.parse(
  fs.readFileSync(path.join(root, 'tests', 'fixtures', 'valid-config.json'), 'utf8')
);

function run(config, args = ['--validate-only'], env = {}) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'apifox-skill-test-'));
  const configPath = path.join(dir, 'config.json');
  fs.writeFileSync(configPath, JSON.stringify(config), 'utf8');
  const result = spawnSync(process.execPath, [generator, '--config', configPath, ...args], {
    encoding: 'utf8',
    env: { ...process.env, APIFOX_CASE_OUTPUT_DIR: path.join(dir, 'out'), ...env },
  });
  fs.rmSync(dir, { recursive: true, force: true });
  return result;
}

test('example config rejects placeholder auth script ids', () => {
  const result = run(example);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /占位符/);
});

test('valid module fixture passes strict validation', () => {
  const result = run(validFixture);
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /config valid: 2 cases/);
});

test('production environment is rejected', () => {
  const config = structuredClone(validFixture);
  config.targetEnvironment.type = 'production';
  const result = run(config);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /non-production/);
});

test('missing evidence is rejected', () => {
  const config = structuredClone(validFixture);
  delete config.caseSpecs[0].evidence;
  const result = run(config);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /evidence/);
});

test('token in config is rejected', () => {
  const config = structuredClone(validFixture);
  config.APIFOX_ACCESS_TOKEN = 'afpp_should_not_be_here';
  const result = run(config);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Token/);
});

test('expected status must match observed status', () => {
  const config = structuredClone(validFixture);
  config.caseSpecs[0].expected.statusCode = 201;
  const result = run(config);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /不一致/);
});

test('non-high auth discovery requires explicit confirmation', () => {
  const config = structuredClone(validFixture);
  config.authDiscovery.confidence = 'medium';
  config.authDiscovery.confirmed = false;
  const result = run(config);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /人工确认/);
});

test('unknown auth script id is rejected', () => {
  const config = structuredClone(validFixture);
  config.authPreProcessors = [
    {
      type: 'commonScript',
      data: [346698],
      enable: true,
      executionTiming: 'prerequest',
    },
  ];
  const result = run(config);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /未知脚本|未校验/);
});

test('auth discovery projectId must match current project', () => {
  const config = structuredClone(validFixture);
  config.authDiscovery.projectId = '999999';
  const result = run(config);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /projectId/);
});

test('missing moduleId in authDiscovery is rejected', () => {
  const config = structuredClone(validFixture);
  delete config.authDiscovery.moduleId;
  const result = run(config);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /moduleId/);
});

test('duplicate names are rejected before generation', () => {
  const config = structuredClone(validFixture);
  config.caseSpecs[1].nameSuffix = config.caseSpecs[0].nameSuffix;
  const result = run(config);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /重复用例名/);
});

test('generated files contain generalized request and assertions', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'apifox-skill-generate-'));
  const configPath = path.join(dir, 'config.json');
  const outputDir = path.join(dir, 'out');
  fs.writeFileSync(configPath, JSON.stringify(validFixture), 'utf8');
  const result = spawnSync(process.execPath, [generator, '--config', configPath], {
    encoding: 'utf8',
    env: { ...process.env, APIFOX_CASE_OUTPUT_DIR: outputDir },
  });
  assert.equal(result.status, 0, result.stderr);
  const generated = JSON.parse(
    fs.readFileSync(path.join(outputDir, '02-negative-missing-subject-id.json'), 'utf8')
  );
  assert.equal(generated.method, 'POST');
  assert.equal(generated.responseId, 0);
  assert.equal(generated.options.responseValidate, false);
  assert.equal(JSON.parse(generated.requestBody.data).subjectId, undefined);
  assert.ok(generated.postProcessors.some((processor) => processor.data.value === '400'));
  fs.rmSync(dir, { recursive: true, force: true });
});
