"""VortexL3 Web Panel - cyberpunk frontend template (self-contained, offline-safe)."""

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VORTEXL3 // CYBER TUNNEL CONTROL</title>
<style>
:root{
  --bg:#050510; --bg2:#0a0a1c;
  --neon:#00f0ff; --pink:#ff2bd6; --lime:#b6ff00; --amber:#ffb300; --red:#ff3355;
  --txt:#d7f9ff; --dim:#6b7a99;
  --card:rgba(10,14,34,.82); --line:rgba(0,240,255,.25);
}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:var(--bg);color:var(--txt);
  font-family:"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;min-height:100vh}
body::before{content:"";position:fixed;inset:0;pointer-events:none;z-index:0;
  background:
    radial-gradient(600px 300px at 15% 10%,rgba(255,43,214,.12),transparent 60%),
    radial-gradient(700px 340px at 85% 20%,rgba(0,240,255,.12),transparent 60%),
    radial-gradient(500px 500px at 50% 100%,rgba(182,255,0,.06),transparent 60%);}
body::after{content:"";position:fixed;inset:0;pointer-events:none;z-index:50;opacity:.5;
  background:repeating-linear-gradient(0deg,rgba(255,255,255,.025) 0 1px,transparent 1px 3px);}
.grid-bg{position:fixed;inset:0;z-index:0;pointer-events:none;opacity:.35;
  background-image:linear-gradient(rgba(0,240,255,.07) 1px,transparent 1px),
    linear-gradient(90deg,rgba(0,240,255,.07) 1px,transparent 1px);
  background-size:44px 44px;
  mask-image:radial-gradient(ellipse at 50% 0%,#000 30%,transparent 75%);}
.wrap{position:relative;z-index:1;max-width:1080px;margin:0 auto;padding:24px 16px 60px}
/* header */
.hdr{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;
  border:1px solid var(--line);border-radius:14px;padding:16px 20px;
  background:linear-gradient(180deg,rgba(0,240,255,.06),transparent),var(--card);
  box-shadow:0 0 24px rgba(0,240,255,.12),inset 0 0 40px rgba(0,240,255,.04)}
.logo{font-family:Consolas,"Courier New",monospace;font-weight:900;letter-spacing:3px;
  font-size:clamp(22px,4vw,34px);color:#fff;
  text-shadow:0 0 8px var(--neon),0 0 24px var(--neon),0 0 60px rgba(0,240,255,.6)}
.logo span{color:var(--pink);text-shadow:0 0 8px var(--pink),0 0 24px var(--pink)}
.sub{color:var(--dim);letter-spacing:5px;font-size:11px;margin-top:4px}
.badge{display:inline-block;border:1px solid var(--pink);color:var(--pink);border-radius:999px;
  padding:4px 14px;font-size:12px;letter-spacing:2px;
  box-shadow:0 0 12px rgba(255,43,214,.35),inset 0 0 12px rgba(255,43,214,.12)}
.meta{color:var(--dim);font-size:13px;margin-top:6px}
.meta b{color:var(--neon)}
/* cards */
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:18px 0}
.stat{border:1px solid var(--line);border-radius:12px;padding:14px;background:var(--card)}
.stat .k{font-size:11px;letter-spacing:3px;color:var(--dim)}
.stat .v{font-size:26px;font-weight:800;margin-top:4px;color:#fff;text-shadow:0 0 14px rgba(0,240,255,.7)}
.stat .v.pink{text-shadow:0 0 14px rgba(255,43,214,.7)}
/* tunnel */
.tun{border:1px solid var(--line);border-radius:14px;background:var(--card);margin:14px 0;overflow:hidden}
.tun-head{display:flex;align-items:center;gap:12px;padding:14px 16px;flex-wrap:wrap;
  background:linear-gradient(90deg,rgba(0,240,255,.08),transparent)}
.dot{width:12px;height:12px;border-radius:50%;flex:none}
.dot.on{background:var(--lime);box-shadow:0 0 12px var(--lime)}
.dot.off{background:var(--red);box-shadow:0 0 12px var(--red)}
.tname{font-family:Consolas,monospace;font-weight:800;font-size:18px;color:#fff;letter-spacing:1px}
.ttype{font-size:11px;color:var(--dim);letter-spacing:2px;border:1px solid rgba(107,122,153,.4);
  border-radius:6px;padding:2px 8px}
.tstatus{margin-left:auto;font-size:12px;letter-spacing:2px}
.tstatus.on{color:var(--lime)} .tstatus.off{color:var(--red)}
.tun-body{padding:6px 16px 16px}
.kv{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:6px 18px;
  font-size:13px;margin:8px 0}
.kv div{color:var(--dim)} .kv b{color:var(--txt);font-weight:600}
.peers,.fwds{font-size:12px;color:var(--dim);margin-top:6px}
.peers b,.fwds b{color:var(--neon)}
.tag{display:inline-block;border:1px solid var(--line);border-radius:6px;padding:1px 8px;margin:2px 4px 2px 0;color:var(--txt)}
/* buttons */
.btn{cursor:pointer;border:1px solid var(--neon);background:rgba(0,240,255,.08);color:var(--neon);
  border-radius:8px;padding:8px 14px;font-size:13px;letter-spacing:1px;font-weight:700;
  transition:.15s}
.btn:hover{background:rgba(0,240,255,.2);box-shadow:0 0 14px rgba(0,240,255,.5)}
.btn.danger{border-color:var(--red);color:var(--red);background:rgba(255,51,85,.07)}
.btn.danger:hover{background:rgba(255,51,85,.18);box-shadow:0 0 14px rgba(255,51,85,.5)}
.btn.pink{border-color:var(--pink);color:var(--pink);background:rgba(255,43,214,.07)}
.btn.pink:hover{background:rgba(255,43,214,.18);box-shadow:0 0 14px rgba(255,43,214,.5)}
.btn.ghost{border-color:rgba(107,122,153,.5);color:var(--dim);background:transparent}
.btn:disabled{opacity:.4;cursor:wait}
.rowbtns{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.topbar{display:flex;gap:10px;flex-wrap:wrap;margin:6px 0 4px}
/* login */
.login{max-width:420px;margin:12vh auto 0;border:1px solid var(--pink);border-radius:16px;
  padding:32px 28px;background:var(--card);
  box-shadow:0 0 30px rgba(255,43,214,.25),inset 0 0 60px rgba(255,43,214,.05)}
.login h1{margin:0 0 4px;font-family:Consolas,monospace;letter-spacing:4px;color:#fff;
  text-shadow:0 0 10px var(--pink),0 0 30px var(--pink)}
.login p{color:var(--dim);font-size:12px;letter-spacing:3px}
label{display:block;font-size:11px;letter-spacing:3px;color:var(--dim);margin:14px 0 6px}
input,select{width:100%;background:#070714;border:1px solid var(--line);border-radius:8px;
  color:var(--txt);padding:10px 12px;font-size:14px;outline:none}
input:focus,select:focus{border-color:var(--neon);box-shadow:0 0 12px rgba(0,240,255,.35)}
.w100{width:100%;margin-top:18px;padding:12px;font-size:15px}
.err{display:none;margin-top:12px;color:var(--red);font-size:13px;border:1px solid rgba(255,51,85,.4);
  border-radius:8px;padding:8px 10px;background:rgba(255,51,85,.06)}
/* modal */
.modal{position:fixed;inset:0;z-index:100;display:none;align-items:center;justify-content:center;
  background:rgba(3,3,12,.8);padding:16px}
.modal.open{display:flex}
.sheet{width:100%;max-width:560px;max-height:90vh;overflow:auto;border:1px solid var(--neon);
  border-radius:14px;background:#08081a;padding:22px;
  box-shadow:0 0 40px rgba(0,240,255,.25)}
.sheet h2{margin:0 0 4px;font-family:Consolas,monospace;letter-spacing:3px;color:#fff;
  text-shadow:0 0 12px var(--neon)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:0 12px}
@media(max-width:560px){.grid2{grid-template-columns:1fr}}
.hint{font-size:11px;color:var(--dim);margin-top:2px}
/* toast + log */
#toast{position:fixed;bottom:18px;left:50%;transform:translateX(-50%);z-index:200;display:none;
  max-width:90vw;border:1px solid var(--neon);background:#061318;color:var(--txt);
  border-radius:10px;padding:10px 18px;font-size:13px;box-shadow:0 0 20px rgba(0,240,255,.4)}
#log{white-space:pre-wrap;font-family:Consolas,monospace;font-size:12px;color:var(--lime);
  background:#02020a;border:1px solid rgba(182,255,0,.25);border-radius:10px;
  padding:12px;margin-top:14px;max-height:220px;overflow:auto;display:none}
.hidden{display:none!important}
a{color:var(--neon)}
</style>
</head>
<body>
<div class="grid-bg"></div>
<div class="wrap">

  <!-- LOGIN -->
  <div id="view-login">
    <div class="login">
      <h1>VORTEX<span style="color:var(--pink)">L3</span></h1>
      <p>CYBER TUNNEL CONTROL // SECURE ACCESS</p>
      <label>USERNAME</label>
      <input id="in-user" autocomplete="username" placeholder="vortex-xxxxxx">
      <label>PASSWORD</label>
      <input id="in-pass" type="password" autocomplete="current-password" placeholder="••••••••••••">
      <div id="login-err" class="err"></div>
      <button class="btn pink w100" id="btn-login" onclick="doLogin()">JACK IN ▸</button>
    </div>
  </div>

  <!-- DASHBOARD -->
  <div id="view-dash" class="hidden">
    <div class="hdr">
      <div>
        <div class="logo">VORTEX<span>L3</span></div>
        <div class="sub">CYBER TUNNEL CONTROL</div>
        <div class="meta">MODE <b id="m-mode">-</b> &nbsp;•&nbsp; NODE <b id="m-ip">-</b> &nbsp;•&nbsp; v<b id="m-ver">-</b></div>
      </div>
      <div style="text-align:right">
        <span class="badge" id="m-count">0 TUNNELS</span>
        <div class="topbar" style="justify-content:flex-end;margin-top:10px">
          <button class="btn pink" onclick="openCreate()">+ NEW TUNNEL</button>
          <button class="btn ghost" onclick="doLogout()">LOGOUT</button>
        </div>
      </div>
    </div>

    <div class="cards">
      <div class="stat"><div class="k">TOTAL</div><div class="v" id="s-total">0</div></div>
      <div class="stat"><div class="k">ONLINE</div><div class="v" id="s-on" style="color:var(--lime)">0</div></div>
      <div class="stat"><div class="k">OFFLINE</div><div class="v pink" id="s-off">0</div></div>
      <div class="stat"><div class="k">FORWARDS</div><div class="v" id="s-fw">0</div></div>
    </div>

    <div id="tunnels"></div>
    <div id="log"></div>
  </div>
</div>

<!-- CREATE MODAL -->
<div class="modal" id="modal">
  <div class="sheet">
    <h2 id="mc-title">NEW TUNNEL</h2>
    <div class="hint" id="mc-mode"></div>
    <div class="grid2">
      <div><label>SIDE</label>
        <select id="f-side"><option value="IRAN">IRAN</option><option value="KHAREJ">KHAREJ</option></select></div>
      <div><label>NAME</label><input id="f-name" placeholder="tunnel1"></div>
    </div>
    <div id="fld-l2tp">
      <div class="grid2">
        <div><label>LOCAL SERVER PUBLIC IP *</label><input id="f-local" placeholder="1.2.3.4"></div>
        <div><label>REMOTE SERVER PUBLIC IP *</label><input id="f-remote" placeholder="5.6.7.8"></div>
      </div>
      <div class="grid2">
        <div><label>INTERFACE IP</label><input id="f-ifip" placeholder="auto"></div>
        <div><label>REMOTE FORWARD IP (IRAN)</label><input id="f-rfwd" placeholder="auto"></div>
      </div>
      <div class="grid2">
        <div><label>ENCAP</label><select id="f-encap"><option value="ip">IP</option><option value="udp">UDP</option></select></div>
        <div><label>UDP PORT</label><input id="f-udp" placeholder="auto"></div>
      </div>
      <div class="grid2">
        <div><label>TUNNEL ID</label><input id="f-tid" placeholder="auto"></div>
        <div><label>PEER TUNNEL ID</label><input id="f-ptid" placeholder="auto"></div>
      </div>
      <div class="grid2">
        <div><label>SESSION ID</label><input id="f-sid" placeholder="auto"></div>
        <div><label>PEER SESSION ID</label><input id="f-psid" placeholder="auto"></div>
      </div>
      <div class="hint">Empty = smart auto value (collision-free). IDs must mirror the other side.</div>
    </div>
    <div id="fld-et" class="hidden">
      <div class="grid2">
        <div><label>TUNNEL INTERFACE IP</label><input id="f-etip" placeholder="auto"></div>
        <div><label>PEER SERVER PUBLIC IP *</label><input id="f-etpeer" placeholder="9.9.9.9"></div>
      </div>
      <div class="grid2">
        <div><label>MESH PORT</label><input id="f-etport" placeholder="auto"></div>
        <div><label>HOSTNAME</label><input id="f-ethost" placeholder="auto"></div>
      </div>
      <div class="grid2">
        <div><label>NETWORK SECRET</label><input id="f-etsec" placeholder="vortexl2"></div>
        <div><label>REMOTE FORWARD IP (IRAN)</label><input id="f-etrf" placeholder="auto"></div>
      </div>
      <div class="hint">Network name is auto-derived from the secret so both sides match.</div>
    </div>
    <div class="err" id="mc-err"></div>
    <div class="rowbtns">
      <button class="btn pink" id="btn-create" onclick="doCreate()">DEPLOY ▸</button>
      <button class="btn ghost" onclick="closeCreate()">CANCEL</button>
    </div>
  </div>
</div>

<!-- FORWARDS MODAL -->
<div class="modal" id="modal-fw">
  <div class="sheet">
    <h2>PORT FORWARDS</h2>
    <div class="hint" id="fw-tun"></div>
    <label>PORTS (e.g. 443,80,2000-2005)</label>
    <input id="fw-ports" placeholder="443,80">
    <div class="err" id="fw-err"></div>
    <div class="rowbtns">
      <button class="btn" onclick="doFw('add')">ADD ▸</button>
      <button class="btn danger" onclick="doFw('remove')">REMOVE ▸</button>
      <button class="btn ghost" onclick="closeFw()">CLOSE</button>
    </div>
  </div>
</div>

<div id="toast"></div>

<script>
let MODE="l2tpv3", FW_TUNNEL="";
function toast(m,ok){const t=document.getElementById('toast');
  t.textContent=m;t.style.display='block';
  t.style.borderColor=ok===false?'var(--red)':'var(--neon)';clearTimeout(t._h);
  t._h=setTimeout(()=>t.style.display='none',4200);}
function log(m){const l=document.getElementById('log');l.style.display='block';
  l.textContent=m+"\n"+l.textContent.slice(0,4000);}
async function api(path,body){
  const o={method:body?'POST':'GET',headers:{}};
  if(body){o.headers['Content-Type']='application/json';o.body=JSON.stringify(body);}
  const r=await fetch(path,o);
  if(r.status===401){showLogin();throw new Error('Session expired, login again');}
  return r.json();
}
function showLogin(){document.getElementById('view-login').classList.remove('hidden');
  document.getElementById('view-dash').classList.add('hidden');}
function showDash(){document.getElementById('view-login').classList.add('hidden');
  document.getElementById('view-dash').classList.remove('hidden');}
async function doLogin(){
  const u=document.getElementById('in-user').value.trim(),
        p=document.getElementById('in-pass').value,
        e=document.getElementById('login-err');
  e.style.display='none';
  try{const r=await api('/api/login',{username:u,password:p});
    if(r.ok){showDash();refresh();}else{e.textContent=r.error||'Login failed';e.style.display='block';}
  }catch(err){e.textContent=err.message;e.style.display='block';}
}
document.getElementById('in-pass').addEventListener('keydown',ev=>{if(ev.key==='Enter')doLogin();});
async function doLogout(){try{await api('/api/logout',{});}catch(e){}showLogin();}
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,
  c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
async function refresh(){
  try{
    const r=await api('/api/summary');
    if(!r.ok){toast(r.error||'Failed to load',false);return;}
    MODE=r.mode;
    document.getElementById('m-mode').textContent=r.mode.toUpperCase();
    document.getElementById('m-ip').textContent=r.server_ip;
    document.getElementById('m-ver').textContent=r.version;
    const t=r.tunnels;let on=0,fw=0;
    t.forEach(x=>{if(x.running)on++;fw+=(x.forwards||[]).length;});
    document.getElementById('s-total').textContent=t.length;
    document.getElementById('s-on').textContent=on;
    document.getElementById('s-off').textContent=t.length-on;
    document.getElementById('s-fw').textContent=fw;
    document.getElementById('m-count').textContent=t.length+' TUNNELS';
    const box=document.getElementById('tunnels');box.innerHTML='';
    if(!t.length){box.innerHTML='<div class="tun"><div class="tun-body">No tunnels yet — hit <b>+ NEW TUNNEL</b>.</div></div>';return;}
    t.forEach(x=>{
      const d=document.createElement('div');d.className='tun';
      const kv = x.type==='easytier'
        ? `<div>INTERFACE <b>${esc(x.interface||'-')}</b></div>
           <div>LOCAL IP <b>${esc(x.local_ip||'-')}</b></div>
           <div>PEER IP <b>${esc(x.remote_ip||'-')}</b></div>
           <div>MESH PORT <b>${esc(x.port||'-')}</b></div>`
        : `<div>INTERFACE <b>${esc(x.interface||'-')}</b></div>
           <div>LOCAL IP <b>${esc(x.local_ip||'-')}</b></div>
           <div>REMOTE IP <b>${esc(x.remote_ip||'-')}</b></div>
           <div>TUNNEL IP <b>${esc(x.interface_ip||'-')}</b></div>`;
      const peers=(x.peers||[]).map(p=>
        `<span class="tag">${esc(p.ipv4)} · ${esc(p.hostname)} · ${esc(p.latency)} · ${esc(p.tunnel)}</span>`).join('');
      const fw=(x.forwards||[]).map(f=>
        `<span class="tag">${esc(f.port)} → ${esc(f.remote)} ${f.active?'●':'○'}</span>`).join('')||'<span class="hint">none</span>';
      d.innerHTML=`
        <div class="tun-head">
          <span class="dot ${x.running?'on':'off'}"></span>
          <span class="tname">${esc(x.name)}</span>
          <span class="ttype">${esc(x.type.toUpperCase())}</span>
          <span class="tstatus ${x.running?'on':'off'}">${esc(x.status).toUpperCase()}</span>
        </div>
        <div class="tun-body">
          <div class="kv">${kv}</div>
          ${peers?`<div class="peers">PEERS<br>${peers}</div>`:''}
          <div class="fwds">FORWARDS<br>${fw}</div>
          <div class="rowbtns">
            <button class="btn" onclick="act('${esc(x.name)}','start')">START</button>
            <button class="btn" onclick="act('${esc(x.name)}','restart')">RESTART</button>
            <button class="btn" onclick="act('${esc(x.name)}','stop')">STOP</button>
            <button class="btn pink" onclick="openFw('${esc(x.name)}')">FORWARDS</button>
            <button class="btn danger" onclick="del('${esc(x.name)}')">DELETE</button>
          </div>
        </div>`;
      box.appendChild(d);
    });
  }catch(err){toast(err.message,false);}
}
async function act(name,action){
  toast(action.toUpperCase()+' '+name+' …');
  try{const r=await api('/api/tunnel/action',{name,action});
    log('['+action.toUpperCase()+'] '+name+'\n'+(r.message||r.error||''));
    toast(r.ok?'Done ✓':'Failed ✗',r.ok);refresh();
  }catch(err){toast(err.message,false);}
}
async function del(name){
  if(!confirm('Delete tunnel "'+name+'"?'))return;
  act(name,'delete');
}
function openCreate(){
  document.getElementById('mc-err').style.display='none';
  document.getElementById('mc-mode').textContent='MODE: '+MODE.toUpperCase();
  document.getElementById('fld-l2tp').classList.toggle('hidden',MODE==='easytier');
  document.getElementById('fld-et').classList.toggle('hidden',MODE!=='easytier');
  document.getElementById('modal').classList.add('open');
}
function closeCreate(){document.getElementById('modal').classList.remove('open');}
function openFw(name){FW_TUNNEL=name;
  document.getElementById('fw-tun').textContent='TUNNEL: '+name;
  document.getElementById('fw-err').style.display='none';
  document.getElementById('modal-fw').classList.add('open');}
function closeFw(){document.getElementById('modal-fw').classList.remove('open');}
function val(id){return document.getElementById(id).value.trim();}
async function doCreate(){
  const e=document.getElementById('mc-err');e.style.display='none';
  const b=document.getElementById('btn-create');b.disabled=true;
  let body;
  if(MODE==='easytier'){
    body={side:val('f-side'),name:val('f-name'),local_ip:val('f-etip'),peer_ip:val('f-etpeer'),
      port:val('f-etport'),hostname:val('f-ethost'),network_secret:val('f-etsec'),
      remote_forward_ip:val('f-etrf')};
  }else{
    body={side:val('f-side'),name:val('f-name'),local_ip:val('f-local'),remote_ip:val('f-remote'),
      interface_ip:val('f-ifip'),remote_forward_ip:val('f-rfwd'),encap:val('f-encap'),
      udp_port:val('f-udp'),tunnel_id:val('f-tid'),peer_tunnel_id:val('f-ptid'),
      session_id:val('f-sid'),peer_session_id:val('f-psid')};
  }
  try{const r=await api('/api/tunnel/create',body);
    if(r.ok){closeCreate();log('[CREATE]\n'+r.message);toast('Tunnel deployed ✓');refresh();}
    else{e.textContent=r.message||r.error;e.style.display='block';}
  }catch(err){e.textContent=err.message;e.style.display='block';}
  b.disabled=false;
}
async function doFw(how){
  const e=document.getElementById('fw-err');e.style.display='none';
  try{const r=await api('/api/forwards/'+how,{name:FW_TUNNEL,ports:val('fw-ports')});
    if(r.ok){closeFw();log('[FORWARDS '+how.toUpperCase()+'] '+FW_TUNNEL+'\n'+r.message);
      toast('Forwards updated ✓');refresh();}
    else{e.textContent=r.message||r.error;e.style.display='block';}
  }catch(err){e.textContent=err.message;e.style.display='block';}
}
refresh().catch(()=>{});
</script>
</body>
</html>
"""
