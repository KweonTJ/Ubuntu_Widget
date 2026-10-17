/* Local compatibility adapter inside the official page's own authenticated session.
 * No passwords or tokens cross the WebKit message bridge. This is not a public
 * todomate API; schema changes fail visibly instead of showing invented tasks.
 */
(() => {
  if (!['www.todomate.net', 'todomate.net'].includes(location.hostname) || window.uwTodomate) return;
  const bridge = window.uwTodomate = {tasks: [], status: 'loading', pending: [], date: '', error: ''};
  let uid = '', unsubscribe, bound = false, ready = false;
  const day = () => {const d = new Date(); return {key: [d.getFullYear(), String(d.getMonth()+1).padStart(2,'0'), String(d.getDate()).padStart(2,'0')].join('-'), value: Date.UTC(d.getFullYear(), d.getMonth(), d.getDate())};};
  const publish = () => window.webkit.messageHandlers.uwTodomate.postMessage(JSON.stringify({status:bridge.status, tasks:bridge.tasks, pending:bridge.pending, date:bridge.date, error:bridge.error}));
  const fail = code => {bridge.status = 'error'; bridge.error = code || 'unavailable'; publish();};
  const clear = status => {if(unsubscribe) unsubscribe(); unsubscribe=null; bridge.tasks=[]; bridge.pending=[]; bridge.status=status; bridge.date=day().key; publish();};
  function subscribe(user) {
    clear(user ? 'syncing' : 'signed_out');
    uid = user ? user.uid : '';
    if (!uid) return;
    const f=window.firebase_firestore, db=f.getFirestore(), today=day();
    try {
      const q=f.query(f.collection(db,'TodoItem'), f.where('writerID','==',uid), f.where('date','==',today.value));
      unsubscribe=f.onSnapshot(q, {includeMetadataChanges:true}, snapshot => {
        if(uid !== user.uid || today.key !== day().key) return;
        const rows=[];
        for(const doc of snapshot.docs) {
          const t=doc.data();
          if(t.writerID!==uid || t.date!==today.value || typeof t.content!=='string' || typeof t.isDone!=='boolean') {fail('schema_changed');return;}
          rows.push({id:doc.id,text:t.content.slice(0,1000),done:t.isDone,order:Number(t.createTime)||0});
        }
        rows.sort((a,b)=>a.order-b.order || a.id.localeCompare(b.id));
        bridge.tasks=rows; bridge.date=today.key; bridge.status=snapshot.metadata.fromCache?'cached':'ready'; bridge.error='';publish();
      }, e=>fail(e.code));
    } catch(e) {fail(e.code || 'schema_changed');}
  }
  bridge.toggle = async (id, expected, date) => {
    if(!uid || date!==day().key || bridge.pending.includes(id) || !bridge.tasks.some(t=>t.id===id && t.done===expected)) {fail('stale_task');return;}
    const f=window.firebase_firestore, db=f.getFirestore(), owner=uid;
    bridge.pending.push(id);publish();
    try {
      await f.runTransaction(db, async transaction => {
        const ref=f.doc(db,'TodoItem',id), snap=await transaction.get(ref), t=snap.data();
        if(!t || t.writerID!==owner || uid!==owner || t.date!==day().value || t.isDone!==expected) throw {code:'stale_task'};
        // Keep active timers under the official app's control.
        if(t.hasTimer || t.timer) throw {code:'timer_running'};
        transaction.update(ref, expected ? {isDone:false} : {isDone:true,doneTime:Date.now(),spentTime:Number(t.spentTime)||0,timer:null,hasTimer:false});
      });
    } catch(e) {fail(e.code || 'write_failed');}
    finally {bridge.pending=bridge.pending.filter(x=>x!==id);publish();}
  };
  function boot() {
    try {
      if(!bound && window.firebase_auth && window.firebase_firestore) {
        const auth=window.firebase_auth.getAuth();
        bound=true;
        auth.authStateReady().then(()=>{ready=true;window.firebase_auth.onAuthStateChanged(auth,subscribe);}).catch(e=>fail(e.code));
      }
      if(ready && bridge.date && bridge.date!==day().key) subscribe(window.firebase_auth.getAuth().currentUser);
    } catch(e) { /* The official app may not have initialized its default app yet. */ bound=false; }
  }
  boot();setInterval(boot,1000);setInterval(publish,15000);
})();
