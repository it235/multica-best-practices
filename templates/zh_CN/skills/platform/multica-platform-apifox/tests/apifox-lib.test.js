const test = require('node:test');
const assert = require('node:assert/strict');
const {
  buildUpdatePayload,
  assertPathOk,
  extractFirstJson,
} = require('../scripts/lib/apifox');

const fullCase = {
  name: 'case',
  categoryId: 211,
  apiDetailId: 3506053,
  method: 'POST',
  path: '/api/subject/file/replace',
  responseId: 3493513,
  parameters: { path: [], query: [], header: [], cookie: [] },
  commonParameters: {},
  requestBody: { type: 'application/json', data: '{}' },
  preProcessors: [{ type: 'placeholder' }, { type: 'commonScript', data: [1] }],
  postProcessors: [],
  options: { responseValidate: true, keep: true },
  advancedSettings: { disabledSystemHeaders: {}, keep: true },
};

test('update payload preserves identity and deeply merges protected options', () => {
  const payload = buildUpdatePayload(fullCase, {
    responseId: 0,
    options: { responseValidate: false },
    advancedSettings: { followRedirect: false },
  });
  assert.equal(payload.path, fullCase.path);
  assert.equal(payload.method, fullCase.method);
  assert.equal(payload.apiDetailId, fullCase.apiDetailId);
  assert.deepEqual(payload.options, { responseValidate: false, keep: true });
  assert.deepEqual(payload.advancedSettings, {
    disabledSystemHeaders: {},
    keep: true,
    followRedirect: false,
  });
  assert.equal(payload.preProcessors.length, 1);
});

test('empty method and path are rejected instead of silently defaulting', () => {
  assert.throws(() => buildUpdatePayload({ ...fullCase, method: '' }, {}), /method 为空/);
  assert.throws(() => assertPathOk({ ...fullCase, path: '' }), /path 为空/);
});

test('CLI JSON extraction ignores warnings before and after object', () => {
  const parsed = JSON.parse(
    extractFirstJson('warning before\n{"success":true,"data":{"text":"} inside"}}\nwarning after')
  );
  assert.equal(parsed.success, true);
  assert.equal(parsed.data.text, '} inside');
});
