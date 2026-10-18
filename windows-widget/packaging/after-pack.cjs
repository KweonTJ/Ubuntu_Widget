'use strict';
// Generate exact uninstall paths; never recursively delete a user-chosen folder.
const fs = require('node:fs');
const path = require('node:path');
module.exports = async context => {
  const files = [], dirs = [];
  function walk(dir, relative = '') {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const name = relative ? relative + '/' + entry.name : entry.name;
      if (entry.isDirectory()) { walk(path.join(dir, entry.name), name); dirs.push(name); }
      else files.push(name);
    }
  }
  walk(context.appOutDir);
  const quote = name => name.replace(/\$/g, () => '$$').replace(/\//g, '\\');
  const lines = files.map(name => `Delete "$INSTDIR\\${quote(name)}"`);
  for (const name of dirs.sort((a,b)=>b.length-a.length)) lines.push(`RMDir "$INSTDIR\\${quote(name)}"`);
  const manifest = path.resolve(context.outDir, 'uninstall-files.nsh');
  fs.writeFileSync(manifest, lines.join('\n')+'\n');
  console.log('Prepared NSIS uninstall manifest:', manifest);
};
