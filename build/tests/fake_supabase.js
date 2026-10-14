const L=k=>JSON.parse(localStorage.getItem(k)||"null"), P=(k,v)=>localStorage.setItem(k,JSON.stringify(v));
const tok=()=>Array.from(crypto.getRandomValues(new Uint8Array(16)),b=>b.toString(16).padStart(2,"0")).join("");
window.supabase = { createClient(){ let session = L("__sess"); const subs=[]; const emit=e=>subs.forEach(f=>f(e,session));
  const db = () => { const d = L("__db") || {collections:{}, shared_decks:[]}; d.shop_offers ||= []; return d; };
  function q(table){ const st={table, op:"select", f:[], lim:null, rows:null, cols:""};
    const run = () => { const d=db(); const uid=session&&session.user.id;
      if (table==="collections"){
        if(st.op==="upsert"){ st.rows.forEach(r=>d.collections[r.id]=Object.assign({counts:r.counts,decks:r.decks}, "wish" in r?{wish:r.wish}:{})); P("__db",d); return {error:null}; }
        const id=st.f.find(x=>x[0]==="id")[1]; return {data:d.collections[id]||null,error:null}; }
      if (table==="shared_decks"){
        if(!uid) return {data:null,error:{message:"not signed in"}};
        if(st.op==="upsert"){ const out=[]; for(const r of st.rows){ if(r.owner!==uid) return {error:{message:"rls"}}; let i=d.shared_decks.findIndex(x=>x.owner===r.owner&&x.deck_id===r.deck_id);
            if(i>=0) d.shared_decks[i]={...d.shared_decks[i],...r}; else { d.shared_decks.push({id:"s"+Math.random().toString(36).slice(2,8),share_token:tok(),...r}); i=d.shared_decks.length-1; } out.push(d.shared_decks[i]); }
          P("__db",d); return {data: st.cols ? out.map(r=>({deck_id:r.deck_id,share_token:r.share_token})) : null, error:null}; }
        // RLS: you can only read your own rows
        let rows=d.shared_decks.filter(r=>r.owner===uid).filter(r=>st.f.every(([k,v,t])=>t==="in"?v.includes(r[k]):r[k]===v));
        if(st.op==="select") return {data:st.lim?rows.slice(0,st.lim):rows,error:null};
        if(st.op==="delete"){ d.shared_decks=d.shared_decks.filter(r=>!rows.includes(r)); P("__db",d); return {error:null}; }
      }
      if (table==="shop_offers"){
        if(!uid) return {data:null,error:{message:"permission denied for table shop_offers"}};
        let rows=d.shop_offers.filter(r=>r.owner===uid).filter(r=>st.f.every(([k,v,t])=>t==="in"?v.includes(r[k]):r[k]===v));
        if(st.op==="select") return {data:rows.slice().reverse().slice(0,st.lim||1e9),error:null};
        if(st.op==="delete"){ d.shop_offers=d.shop_offers.filter(r=>!rows.includes(r)); P("__db",d); return {error:null}; }
      }
      return {data:null,error:null}; };
    const b = { select(c){st.cols=c||"*";return b}, eq(k,v){st.f.push([k,v]);return b}, in(k,v){st.f.push([k,v,"in"]);return b}, order(){return b}, limit(n){st.lim=n;return b},
      async maybeSingle(){return run()}, delete(){st.op="delete";return b}, upsert(rows){ st.op="upsert"; st.rows=[].concat(rows); st.cols=""; return b; },
      then(res,rej){ return Promise.resolve(run()).then(res,rej); } };
    return b; }
  return { from:q,
    async rpc(fn,args){
      if(fn==="make_offer"){ const d=db(), s=d.shared_decks.find(r=>r.share_token===args.p_token&&r.deck_id==="__shop__");
        if(!s) return {data:null,error:{message:"link"}};
        if(!String(args.p_name||"").trim()) return {data:null,error:{message:"name"}};
        if(!String(args.p_offer||"").trim()) return {data:null,error:{message:"offer"}};
        if(!Array.isArray(args.p_items)||!args.p_items.length) return {data:null,error:{message:"items"}};
        const id="o"+Math.random().toString(36).slice(2,8);
        d.shop_offers.push({id,owner:s.owner,share_token:args.p_token,from_name:args.p_name.trim(),items:args.p_items.map(i=>({name:i.name,q:i.q})),offer:String(args.p_offer).trim(),created_at:new Date().toISOString()}); P("__db",d); return {data:id,error:null}; }
      if(fn!=="get_shared") return {error:{message:"no function"}}; const uid=session&&session.user.id; window.__rpcCalls=(window.__rpcCalls||0)+1;
      const rows=db().shared_decks.filter(r=>args.p_tokens.includes(r.share_token)).map(({owner,...r})=>({...r,is_mine:owner===uid})); return {data:rows,error:null}; },
    auth:{ onAuthStateChange(f){subs.push(f); setTimeout(()=>f("INITIAL_SESSION",session),0); return {data:{subscription:{unsubscribe(){}}}}},
      async signUp({email,password}){ const us=L("__users")||{}; if(us[email]) return {data:{},error:{message:"User already registered"}}; us[email]={password,id:"u-"+email.split("@")[0]}; P("__users",us); session={user:{id:us[email].id,email}}; P("__sess",session); emit("SIGNED_IN"); return {data:{session},error:null}},
      async signInWithPassword({email,password}){ const u=(L("__users")||{})[email]; if(!u||u.password!==password) return {error:{message:"Invalid login credentials"}}; session={user:{id:u.id,email}}; P("__sess",session); emit("SIGNED_IN"); return {data:{session},error:null}},
      async signOut(){ session=null; localStorage.removeItem("__sess"); emit("SIGNED_OUT"); return {error:null}} } };
} };
