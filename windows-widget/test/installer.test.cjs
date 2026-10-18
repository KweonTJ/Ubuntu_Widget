'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const hook=require('../packaging/after-pack.cjs');
test('uninstaller enumerates installed files and preserves arbitrary files in the destination',async()=>{
 const dir=fs.mkdtempSync(path.join(process.env.WIDGET_TEST_TEMP||os.tmpdir(),'widget-installer-'));
 try{const app=path.join(dir,'app');fs.mkdirSync(path.join(app,'resources','nested'),{recursive:true});fs.writeFileSync(path.join(app,'Widget Library.exe'),'app');fs.writeFileSync(path.join(app,'resources','nested','cost$.dat'),'asset');await hook({appOutDir:app,outDir:dir});const script=fs.readFileSync(path.join(dir,'uninstall-files.nsh'),'utf8');assert(script.includes('Delete "$INSTDIR\\Widget Library.exe"'));assert(script.includes('cost$$.dat'));assert(!/RMDir\s+\/r/i.test(script));assert(!script.includes('*'));assert(script.indexOf('RMDir "$INSTDIR\\resources\\nested"')<script.indexOf('RMDir "$INSTDIR\\resources"'));const installer=fs.readFileSync(path.join(__dirname,'../packaging/installer.nsi'),'utf8');assert(!/RMDir\s+\/r/i.test(installer));assert(installer.includes('RequestExecutionLevel user'));assert(!installer.includes('Delete "$APPDATA'));}finally{fs.rmSync(dir,{recursive:true,force:true});}
});
