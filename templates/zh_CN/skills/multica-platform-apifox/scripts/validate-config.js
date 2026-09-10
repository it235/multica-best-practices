/**
 * 离线严格校验 config，不生成文件、不访问网络。
 * 用法：node validate-config.js [config.json]
 */
const path = require('path');
const { spawnSync } = require('child_process');

const config = path.resolve(process.argv[2] || path.join(__dirname, 'config.json'));
const generator = path.join(__dirname, 'generate-cases.js');
const result = spawnSync(process.execPath, [generator, '--config', config, '--validate-only'], {
  stdio: 'inherit',
  env: process.env,
});

process.exit(result.status === null ? 1 : result.status);
