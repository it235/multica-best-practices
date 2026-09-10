const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const root = path.resolve(__dirname, '..');
const script = path.join(root, 'scripts', 'systems-registry.js');

function run(args, env = {}) {
  return spawnSync(process.execPath, [script, ...args], {
    encoding: 'utf8',
    env: { ...process.env, ...env },
  });
}

test('registry path respects APIFOX_SYSTEMS_REGISTRY', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'apifox-registry-'));
  const file = path.join(dir, 'reg.json');
  const result = run(['path'], { APIFOX_SYSTEMS_REGISTRY: file });
  assert.equal(result.status, 0, result.stderr);
  const body = JSON.parse(result.stdout);
  assert.equal(body.registryPath, path.resolve(file));
  assert.equal(body.via, 'APIFOX_SYSTEMS_REGISTRY');
  fs.rmSync(dir, { recursive: true, force: true });
});

test('lookup is exact-match only (no fuzzy)', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'apifox-registry-'));
  const file = path.join(dir, 'reg.json');
  const upsert = run(
    ['upsert', '--name', 'AlphaSys', '--project-id', '1001', '--project-name', 'AlphaSys'],
    { APIFOX_SYSTEMS_REGISTRY: file, APIFOX_OPERATOR: 'tester' }
  );
  assert.equal(upsert.status, 0, upsert.stderr);

  const miss = run(['lookup', '--name', 'Alpha'], { APIFOX_SYSTEMS_REGISTRY: file });
  assert.equal(miss.status, 2);
  assert.equal(JSON.parse(miss.stdout).found, false);

  const hit = run(['lookup', '--name', 'AlphaSys'], { APIFOX_SYSTEMS_REGISTRY: file });
  assert.equal(hit.status, 0, hit.stderr);
  assert.equal(JSON.parse(hit.stdout).found, true);
  assert.equal(JSON.parse(hit.stdout).system.projectId, '1001');
  fs.rmSync(dir, { recursive: true, force: true });
});

test('operator isolates default registry filename under state dir', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'apifox-registry-'));
  const result = run(['path'], {
    APIFOX_SKILL_STATE_DIR: dir,
    APIFOX_OPERATOR: 'Bob',
    APIFOX_SYSTEMS_REGISTRY: '',
  });
  // Clear SYSTEMS_REGISTRY: spawnSync may still inherit; delete key by setting undefined not easy on Windows.
  // Use env without APIFOX_SYSTEMS_REGISTRY:
  const env = { ...process.env, APIFOX_SKILL_STATE_DIR: dir, APIFOX_OPERATOR: 'Bob' };
  delete env.APIFOX_SYSTEMS_REGISTRY;
  const r2 = spawnSync(process.execPath, [script, 'path'], { encoding: 'utf8', env });
  assert.equal(r2.status, 0, r2.stderr);
  const body = JSON.parse(r2.stdout);
  assert.match(body.registryPath, /systems-registry\.bob\.json$/i);
  fs.rmSync(dir, { recursive: true, force: true });
});
