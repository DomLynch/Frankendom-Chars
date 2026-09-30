// Compare the final candidate with its unchanged source using Khronos validation.
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '../../..');
const validator = require(path.join(root, 'work/pitborn-20260929/tools/node_modules/gltf-validator'));
const work = path.join(root, 'work/pitborn-l1-20260930');
(async () => {
  const reports = {};
  for (const [name, file] of Object.entries({source:'source/pitborn.glb', candidate:'models/pitborn-L1.glb'})) {
    const report = await validator.validateBytes(new Uint8Array(fs.readFileSync(path.join(work, file))), {maxIssues:100000});
    fs.writeFileSync(path.join(work,'checks',name+'-format.json'), JSON.stringify(report,null,2));
    const errors = {};
    for (const issue of report.issues.messages.filter(x=>x.severity===0)) errors[issue.code]=(errors[issue.code]||0)+1;
    reports[name]={errors:report.issues.numErrors,warnings:report.issues.numWarnings,errorCodes:errors};
  }
  reports.newErrors = Object.fromEntries(Object.entries(reports.candidate.errorCodes).filter(([code,n])=>n>(reports.source.errorCodes[code]||0)));
  fs.writeFileSync(path.join(work,'checks/format-summary.json'), JSON.stringify(reports,null,2));
  console.log(JSON.stringify(reports));
  if (Object.keys(reports.newErrors).length) process.exitCode=1;
})();
