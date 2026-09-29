const fs = require('fs');
const path = require('path');
const assert = require('assert');
const validator = require(process.env.GLTF_VALIDATOR_PATH || 'gltf-validator');
const root = path.resolve(__dirname, '..');
const errors = r => r.issues.messages.filter(m => m.severity === 0).map(m => JSON.stringify([m.code, m.message, m.pointer])).sort();
async function validate(rank) {
  const file = path.join(root, 'models', `dwarf-${rank}.glb`);
  return validator.validateBytes(new Uint8Array(fs.readFileSync(file)), {maxIssues: 0});
}
(async () => {
  const baseline = await validate('L1');
  const results = [];
  for (let level = 2; level <= 10; level++) {
    const rank = `L${level}`;
    const result = await validate(rank);
    assert.deepStrictEqual(errors(result), errors(baseline), `${rank} introduced or changed errors`);
    results.push({rank, originalErrors: baseline.issues.numErrors, candidateErrors: result.issues.numErrors, newErrors: 0, warnings: result.issues.numWarnings});
  }
  fs.writeFileSync(path.join(root, 'reports', 'format-regression.json'), JSON.stringify(results, null, 2));
  console.log(JSON.stringify(results));
})().catch(error => { console.error(error); process.exitCode = 1; });
