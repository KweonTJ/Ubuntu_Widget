const fs=require('fs'),vm=require('vm'),assert=require('assert').strict;
(async()=>{
 const date=new Date(),today=Date.UTC(date.getFullYear(),date.getMonth(),date.getDate());
 let user={uid:'test-owner'}, listener, authChange, writes=[], published=[];
 let row={writerID:user.uid,date:today,content:'Fixture task',isDone:false,createTime:1,spentTime:23,timer:null,hasTimer:false};
 const snap=()=>({docs:[{id:'fixture',data:()=>({...row})}],metadata:{fromCache:false}});
 const f={getFirestore:()=>({}),collection:(_d,name)=>{assert.equal(name,'TodoItem');return name;},where:(...args)=>args,
  query:(_c,...filters)=>{assert.deepEqual(filters,[['writerID','==','test-owner'],['date','==',today]]);return filters;},
  onSnapshot:(_q,_options,cb)=>{listener=cb;queueMicrotask(()=>cb(snap()));return()=>{};},doc:(_d,c,id)=>{assert.equal(c,'TodoItem');assert.equal(id,'fixture');return id;},
  runTransaction:async(_d,callback)=>{await callback({get:async()=>({data:()=>({...row})}),update:(_r,patch)=>{writes.push(patch);Object.assign(row,patch);}});listener(snap());}};
 const w={firebase_firestore:f,firebase_auth:{getAuth:()=>({authStateReady:async()=>{},currentUser:user}),onAuthStateChanged:(_a,cb)=>{authChange=cb;cb(user);}},
  webkit:{messageHandlers:{uwTodomate:{postMessage:s=>published.push(JSON.parse(s))}}}};
 const context={window:w,location:{hostname:'www.todomate.net'},setInterval:()=>{},Date,console};
 vm.runInNewContext(fs.readFileSync(process.argv[2],'utf8'),context);await new Promise(r=>setImmediate(r));
 assert.equal(w.uwTodomate.status,'ready');assert.equal(w.uwTodomate.tasks[0].text,'Fixture task');
 await w.uwTodomate.toggle('fixture',false,w.uwTodomate.date);assert.equal(row.isDone,true);assert.equal(writes[0].spentTime,23);assert.equal(typeof writes[0].doneTime,'number');
 await w.uwTodomate.toggle('fixture',true,w.uwTodomate.date);assert.equal(row.isDone,false);
 row.isDone=true;await w.uwTodomate.toggle('fixture',false,w.uwTodomate.date);assert.equal(writes.length,2);assert.equal(w.uwTodomate.error,'stale_task');
 row.isDone=false;row.hasTimer=true;listener(snap());await w.uwTodomate.toggle('fixture',false,w.uwTodomate.date);assert.equal(writes.length,2);assert.equal(w.uwTodomate.error,'timer_running');
 row.hasTimer=false;row.writerID='another-user';listener(snap());assert.equal(w.uwTodomate.error,'schema_changed');
 row.writerID='test-owner';listener(snap());row.date=0;await w.uwTodomate.toggle('fixture',false,w.uwTodomate.date);assert.equal(writes.length,2);
 authChange(null);listener(snap());assert.equal(w.uwTodomate.status,'signed_out');assert.equal(w.uwTodomate.tasks.length,0);
 assert.ok(published.every(p=>!('uid' in p) && !('password' in p) && !('token' in p)));
 console.log('Adapter contract passed: read, check, uncheck, ownership, date, stale state, timer, logout.');
})().catch(e=>{console.error(e);process.exitCode=1;});
