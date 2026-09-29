const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const validator = require('gltf-validator');
const root = path.resolve(process.argv[2] || path.join(__dirname, '../..'));
async function check(file) {
  const bytes = fs.readFileSync(file);
  const report = await validator.validateBytes(new Uint8Array(bytes), {maxIssues: 100000});
  if (report.issues.truncated) throw Error('Truncated validation');
  return {report, sha256: crypto.createHash('sha256').update(bytes).digest('hex')};
}
(async () => {
  const baseline = await check(path.join(root, 'source/original.glb'));
  fs.writeFileSync(path.join(root, 'checks/original-format.json'), JSON.stringify(baseline, null, 2));
  const errors = r => r.issues.messages.filter(m => m.severity === 0);
  const expected = JSON.stringify(errors(baseline.report));
  const summary = [];
  for (let rank = 2; rank <= 10; rank++) {
    const result = await check(path.join(root, `models/knight-L${rank}.glb`));
    fs.writeFileSync(path.join(root, `checks/L${rank}-format.json`), JSON.stringify(result, null, 2));
    if (JSON.stringify(errors(result.report)) !== expected) {
      console.error(JSON.stringify({rank, issues:result.report.issues.numErrors, first:errors(result.report).slice(0,3)}));
      throw Error(`L${rank}: introduced format error`);
    }
    summary.push({rank, sha256: result.sha256, inheritedErrors: result.report.issues.numErrors, introducedErrors: 0, warnings: result.report.issues.numWarnings});
  }
  fs.writeFileSync(path.join(root, 'checks/format-summary.json'), JSON.stringify(summary, null, 2));
  console.log(JSON.stringify(summary));
})().catch(e => { console.error(e.message); process.exitCode = 1; });
