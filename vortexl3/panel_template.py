"""VortexL3 Web Panel - cyberpunk frontend template (self-contained, offline-safe)."""

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VORTEXL3 // CYBER TUNNEL CONTROL</title>
<script>
/* pre-apply theme + language before first paint (no flash) */
try{
  var _th=localStorage.getItem('v3theme')||'cyberpunk';
  document.documentElement.setAttribute('data-theme',_th);
  var _lg=localStorage.getItem('v3lang')||'en';
  if(_lg==='fa'){document.documentElement.setAttribute('dir','rtl');}
}catch(e){}
</script>
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
#tabs{margin:14px 0 2px}
.tab{opacity:.65}
.tab.active{opacity:1;box-shadow:0 0 14px rgba(0,240,255,.4)}
table.sv{width:100%;border-collapse:collapse;font-size:13px;margin-top:6px}
table.sv td,table.sv th{border-bottom:1px solid rgba(0,240,255,.12);padding:8px 6px;text-align:left}
table.sv th{color:var(--dim);font-size:11px;letter-spacing:2px}
.pill{display:inline-block;border-radius:999px;padding:2px 12px;font-size:11px;letter-spacing:2px}
.pill.on{color:var(--lime);border:1px solid rgba(182,255,0,.5)}
.pill.off{color:var(--red);border:1px solid rgba(255,51,85,.5)}
.pill.na{color:var(--dim);border:1px solid rgba(107,122,153,.5)}
.logview{white-space:pre-wrap;font-family:Consolas,monospace;font-size:12px;color:var(--txt);
  background:#02020a;border:1px solid var(--line);border-radius:10px;
  padding:12px;margin-top:12px;max-height:320px;overflow:auto}
.prog{height:10px;border:1px solid var(--line);border-radius:999px;margin-top:12px;overflow:hidden}
.prog div{height:100%;width:0;background:linear-gradient(90deg,var(--neon),var(--pink));
  box-shadow:0 0 12px var(--neon);transition:width .4s}
select{max-width:100%}
/* themes */
[data-theme="matrix"]{--bg:#020805;--bg2:#031007;--neon:#00ff66;--pink:#00ff66;
  --lime:#ccff00;--txt:#c8ffd8;--dim:#3f7a52;--card:rgba(3,20,10,.85);
  --line:rgba(0,255,102,.25)}
[data-theme="solar"]{--bg:#e8edf3;--bg2:#dfe6ee;--neon:#0066cc;--pink:#cc0066;
  --lime:#1a7a00;--amber:#b36b00;--red:#cc0033;--txt:#1a2433;--dim:#5a6b80;
  --card:rgba(255,255,255,.92);--line:rgba(0,102,204,.3)}
[data-theme="solar"] body::after{opacity:.15}
[dir="rtl"] body,[dir="rtl"] input,[dir="rtl"] select{font-family:Tahoma,"Segoe UI",sans-serif}
[dir="rtl"] .logo,[dir="rtl"] .tname,[dir="rtl"] .sheet h2,[dir="rtl"] .login h1{letter-spacing:1px}
/* boot overlay */
#boot{position:fixed;inset:0;z-index:300;background:var(--bg);display:flex;
  align-items:center;justify-content:center;cursor:pointer}
#boot pre{font-family:Consolas,monospace;color:var(--neon);font-size:14px;
  text-shadow:0 0 10px var(--neon);margin:0;padding:20px;white-space:pre-wrap}
/* glitch logo */
.glitch{position:relative}
.glitch::before,.glitch::after{content:attr(data-t);position:absolute;inset:0;opacity:.7}
.glitch::before{color:var(--pink);animation:gl1 2.4s infinite steps(2);clip-path:inset(0 0 55% 0)}
.glitch::after{color:var(--neon);animation:gl2 3.1s infinite steps(2);clip-path:inset(60% 0 0 0)}
@keyframes gl1{0%,92%{transform:none;opacity:0}93%{transform:translate(-3px,-2px);opacity:.8}
  96%{transform:translate(3px,1px);opacity:.8}100%{transform:none;opacity:0}}
@keyframes gl2{0%,88%{transform:none;opacity:0}89%{transform:translate(3px,2px);opacity:.8}
  94%{transform:translate(-3px,-1px);opacity:.8}100%{transform:none;opacity:0}}
/* wizard */
.steps{display:flex;gap:6px;margin:12px 0}
.step{flex:1;text-align:center;font-size:11px;letter-spacing:2px;color:var(--dim);
  border-bottom:2px solid rgba(107,122,153,.3);padding-bottom:6px}
.step.on{color:var(--neon);border-color:var(--neon)}
.step.done{color:var(--lime);border-color:var(--lime)}
.review{font-family:Consolas,monospace;font-size:13px;background:#02020a;
  border:1px solid var(--line);border-radius:10px;padding:12px;white-space:pre-wrap}
/* charts */
canvas.chart{width:100%;height:220px;background:#02020a;border:1px solid var(--line);
  border-radius:10px;margin-top:10px}
.dtabs{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}
canvas.spark{width:100%;height:44px}
</style>
</head>
<body>
<div class="grid-bg"></div>
<div id="boot" onclick="skipBoot()"><pre id="boot-txt"></pre></div>
<div class="wrap">

  <!-- LOGIN -->
  <div id="view-login">
    <div class="login">
      <h1>VORTEX<span style="color:var(--pink)">L3</span></h1>
      <p data-i18n="login_sub">CYBER TUNNEL CONTROL // SECURE ACCESS</p>
      <label data-i18n="username">USERNAME</label>
      <input id="in-user" autocomplete="username" placeholder="vortex-xxxxxx">
      <label data-i18n="password">PASSWORD</label>
      <input id="in-pass" type="password" autocomplete="current-password" placeholder="••••••••••••">
      <div id="login-err" class="err"></div>
      <button class="btn pink w100" id="btn-login" onclick="doLogin()" data-i18n="login_btn">JACK IN ▸</button>
    </div>
  </div>

  <!-- DASHBOARD -->
  <div id="view-dash" class="hidden">
    <div class="hdr">
      <div>
        <div class="logo glitch" data-t="VORTEXL3">VORTEX<span>L3</span></div>
        <div class="sub" data-i18n="subtitle">CYBER TUNNEL CONTROL</div>
        <div class="meta">MODE <b id="m-mode">-</b> &nbsp;•&nbsp; NODE <b id="m-ip">-</b> &nbsp;•&nbsp; v<b id="m-ver">-</b></div>
      </div>
      <div style="text-align:right">
        <span class="badge" id="m-count">0 TUNNELS</span>
        <div class="topbar" style="justify-content:flex-end;margin-top:10px">
          <button class="btn pink" onclick="openCreate()" data-i18n="new_tunnel">+ NEW TUNNEL</button>
          <button class="btn ghost" onclick="cycleTheme()" id="btn-theme" title="Theme">◐</button>
          <button class="btn ghost" onclick="cycleLang()" id="btn-lang" title="Language">FA</button>
          <button class="btn ghost" onclick="doLogout()" data-i18n="logout">LOGOUT</button>
        </div>
      </div>
    </div>

    <div class="topbar" id="tabs">
      <button class="btn tab active" onclick="showTab('tunnels',this)" data-i18n="tab_tunnels">TUNNELS</button>
      <button class="btn tab" onclick="showTab('system',this)" data-i18n="tab_system">SYSTEM</button>
      <button class="btn tab" onclick="showTab('network',this)" data-i18n="tab_network">NETWORK</button>
      <button class="btn tab" onclick="showTab('panel',this)" data-i18n="tab_panel">PANEL</button>
    </div>

    <div id="sec-tunnels">
    <div class="cards">
      <div class="stat"><div class="k" data-i18n="total">TOTAL</div><div class="v" id="s-total">0</div></div>
      <div class="stat"><div class="k" data-i18n="online">ONLINE</div><div class="v" id="s-on" style="color:var(--lime)">0</div></div>
      <div class="stat"><div class="k" data-i18n="offline">OFFLINE</div><div class="v pink" id="s-off">0</div></div>
      <div class="stat"><div class="k" data-i18n="fwds">FORWARDS</div><div class="v" id="s-fw">0</div></div>
    </div>

    <div id="tunnels"></div>
    <div id="log"></div>
    </div><!-- /sec-tunnels -->

    <div id="sec-detail" class="hidden">
      <div class="rowbtns"><button class="btn ghost" onclick="backToList()">◂ <span data-i18n="back">BACK</span></button></div>
      <div class="tun"><div class="tun-head"><span class="dot" id="d-dot"></span>
        <span class="tname" id="d-name">-</span><span class="ttype" id="d-type">-</span>
        <span class="tstatus" id="d-status">-</span></div>
        <div class="tun-body">
          <div class="dtabs">
            <button class="btn tab active" onclick="dtab('info',this)" data-i18n="overview">OVERVIEW</button>
            <button class="btn tab" onclick="dtab('traffic',this)" data-i18n="traffic">TRAFFIC</button>
            <button class="btn tab" onclick="dtab('forwards',this)" data-i18n="forwards">FORWARDS</button>
            <button class="btn tab" onclick="dtab('logs',this)" data-i18n="logs">LOGS</button>
            <button class="btn tab" onclick="dtab('peer',this)" data-i18n="peer">PEER</button>
          </div>
          <div id="d-info"><div class="kv" id="d-kv"></div><div class="fwds" id="d-peers"></div>
            <div class="rowbtns" id="d-actions"></div></div>
          <div id="d-traffic" class="hidden">
            <div class="rowbtns">
              <button class="btn ghost" onclick="loadHistory(1)">1H</button>
              <button class="btn ghost" onclick="loadHistory(6)">6H</button>
              <button class="btn ghost" onclick="loadHistory(24)">24H</button>
            </div>
            <canvas class="chart" id="ch-tp" width="900" height="220"></canvas>
            <canvas class="chart" id="ch-ping" width="900" height="140"></canvas>
          </div>
          <div id="d-forwards" class="hidden"><div class="fwds" id="d-fw"></div>
            <div class="rowbtns"><button class="btn pink" id="d-fwbtn">MANAGE</button></div></div>
          <div id="d-logs" class="hidden"><div class="rowbtns">
            <button class="btn" onclick="loadDetailLogs()">LOAD ▸</button></div>
            <div id="d-logview" class="logview">Hit LOAD.</div></div>
          <div id="d-peer" class="hidden"><div id="d-peerbody" class="logview" style="color:var(--txt)">loading…</div>
            <div class="rowbtns"><button class="btn" onclick="copyPeer2()">COPY ▸</button></div></div>
        </div></div>
    </div>

    <div id="sec-system" class="hidden">
      <div class="tun"><div class="tun-head"><span class="tname" data-i18n="services">SERVICES</span>
        <span class="tstatus"><button class="btn ghost" onclick="loadHealth()">REFRESH</button></span></div>
        <div class="tun-body" id="health"></div></div>
      <div class="tun"><div class="tun-head"><span class="tname" data-i18n="logs_t">LOGS</span></div>
        <div class="tun-body">
          <div class="rowbtns">
            <select id="log-svc" style="max-width:300px"></select>
            <select id="log-lines" style="max-width:120px">
              <option value="50">50</option><option value="100" selected>100</option>
              <option value="200">200</option><option value="500">500</option>
            </select>
            <button class="btn" onclick="loadLogs()">LOAD ▸</button>
          </div>
          <div id="logview" class="logview">Select a service and hit LOAD.</div>
        </div></div>
      <div class="tun"><div class="tun-head"><span class="tname" data-i18n="tg">TELEGRAM ALERTS</span></div>
        <div class="tun-body">
          <div class="kv" id="tgbox"></div>
          <label>BOT TOKEN</label><input id="tg-token" type="password" placeholder="123456:ABC-...">
          <label>CHAT ID</label><input id="tg-chat" placeholder="123456789">
          <div class="rowbtns">
            <button class="btn pink" onclick="tgSave(true)">ENABLE &amp; SAVE ▸</button>
            <button class="btn ghost" onclick="tgSave(false)">SAVE (DISABLED)</button>
            <button class="btn ghost" onclick="tgTest()">SEND TEST ▸</button>
            <button class="btn ghost" onclick="loadTg()">REFRESH</button>
          </div>
          <div class="hint">Create a bot via @BotFather, then send it one message and get your chat ID via @userinfobot. Alerts fire when a tunnel goes down / recovers.</div>
        </div></div>
      <div class="tun"><div class="tun-head"><span class="tname" data-i18n="backup">BACKUP &amp; RESTORE</span></div>
        <div class="tun-body">
          <div class="rowbtns">
            <button class="btn" onclick="doBackup()">DOWNLOAD BACKUP ▸</button>
          </div>
          <label>RESTORE FROM FILE (new tunnels only, existing names are skipped)</label>
          <input id="restore-file" type="file" accept=".json,application/json">
          <div class="rowbtns"><button class="btn pink" onclick="doRestore()">RESTORE ▸</button></div>
        </div></div>
      <div class="tun"><div class="tun-head"><span class="tname" data-i18n="update">UPDATE FROM GITHUB</span></div>
        <div class="tun-body">
          <div class="kv" id="updbox"></div>
          <div class="rowbtns">
            <button class="btn ghost" onclick="checkUpdate()">CHECK ▸</button>
            <button class="btn pink" onclick="runUpdate()">UPDATE NOW ▸</button>
            <button class="btn ghost" onclick="updateLog()">VIEW LOG</button>
          </div>
          <div id="updlog" class="logview hidden"></div>
        </div></div>
    </div>

    <div id="sec-network" class="hidden">
      <div class="tun"><div class="tun-head"><span class="tname" data-i18n="fwd_engine">FORWARD ENGINE</span></div>
        <div class="tun-body">
          <div class="kv"><div>MODE <b id="fw-mode">-</b></div></div>
          <div class="rowbtns">
            <button class="btn" onclick="setMode('haproxy')">HAPROXY</button>
            <button class="btn" onclick="setMode('socat')">SOCAT</button>
            <button class="btn danger" onclick="setMode('none')">DISABLE</button>
            <button class="btn ghost" onclick="fwRestart()">RESTART</button>
            <button class="btn ghost" onclick="fwValidate()">VALIDATE</button>
          </div>
        </div></div>
      <div class="tun"><div class="tun-head"><span class="tname" data-i18n="cron">AUTO-RESTART CRON</span></div>
        <div class="tun-body" id="cronbox"></div></div>
      <div class="tun"><div class="tun-head"><span class="tname" data-i18n="tcp">TCP OPTIMIZATION</span></div>
        <div class="tun-body">
          <div class="kv" id="tcpbox"></div>
          <div class="rowbtns"><button class="btn pink" onclick="applyTcp()">APPLY OPTIMIZATION ▸</button>
          <button class="btn ghost" onclick="loadTcp()">REFRESH</button></div>
        </div></div>
      <div class="tun"><div class="tun-head"><span class="tname" data-i18n="dns">DNS MANAGER</span></div>
        <div class="tun-body">
          <div class="kv" id="dnsbox"></div>
          <div class="rowbtns">
            <button class="btn pink" onclick="startScan()">SCAN &amp; APPLY BEST DNS ▸</button>
            <button class="btn ghost" onclick="loadDns()">REFRESH</button>
          </div>
          <div id="scanbar" class="prog hidden"><div id="scanfill"></div></div>
          <div id="scanres" class="fwds" style="margin-top:8px"></div>
          <div class="rowbtns">
            <input id="dns-hours" placeholder="hours (1-72)" style="max-width:150px">
            <button class="btn ghost" onclick="setDnsHours()">SET INTERVAL</button>
            <button class="btn ghost" onclick="dnsAuto('enable')">AUTO-CHECK ON</button>
            <button class="btn danger" onclick="dnsAuto('disable')">AUTO-CHECK OFF</button>
          </div>
        </div></div>
      <div class="tun"><div class="tun-head"><span class="tname" data-i18n="speed">SPEED TEST</span><span style="font-size:11px;color:var(--dim)">iperf3</span></div>
        <div class="tun-body">
          <div class="kv" id="speedbox"></div>
          <div class="rowbtns" id="speedbtns">
            <button class="btn ghost" onclick="speedInstall()">INSTALL IPERF3 ▸</button>
            <button class="btn ghost" onclick="speedServer('start')">SERVER ON</button>
            <button class="btn danger" onclick="speedServer('stop')">SERVER OFF</button>
          </div>
          <div class="grid2" style="margin-top:10px">
            <div><label data-i18n="target">TARGET (peer tunnel IP)</label><select id="sp-target"></select></div>
            <div><label data-i18n="duration">DURATION</label><select id="sp-dur">
              <option value="5">5s</option><option value="10" selected>10s</option><option value="30">30s</option>
            </select></div>
          </div>
          <div class="rowbtns"><button class="btn pink" onclick="speedRun()">RUN TEST ▸</button></div>
          <div id="speedres" class="fwds" style="margin-top:8px"></div>
        </div></div>
    </div>

    <div id="sec-panel" class="hidden">
      <div class="tun"><div class="tun-head"><span class="tname" data-i18n="access">ACCESS</span></div>
        <div class="tun-body"><div class="kv" id="panelbox"></div>
          <div class="rowbtns"><button class="btn ghost" onclick="loadPanelInfo()">REFRESH</button></div>
        </div></div>
      <div class="tun"><div class="tun-head"><span class="tname" data-i18n="https">HTTPS</span></div>
        <div class="tun-body">
          <div class="kv" id="httpsbox"></div>
          <div class="hint">Self-signed certificate (browser will show a warning — accept it). Changing restarts the panel.</div>
          <div class="rowbtns">
            <button class="btn pink" onclick="setHttps(true)">ENABLE HTTPS ▸</button>
            <button class="btn danger" onclick="setHttps(false)">DISABLE (HTTP)</button>
          </div>
          <div id="https-reconnect" class="hidden" style="margin-top:10px"></div>
        </div></div>
      <div class="tun"><div class="tun-head"><span class="tname" data-i18n="chg_pass">CHANGE PASSWORD</span></div>
        <div class="tun-body">
          <label>CURRENT PASSWORD</label><input id="pw-cur" type="password">
          <label>NEW PASSWORD (min 8 chars)</label><input id="pw-new" type="password">
          <div class="rowbtns"><button class="btn pink" onclick="changePw()">CHANGE ▸</button></div>
        </div></div>
      <div class="tun"><div class="tun-head"><span class="tname" data-i18n="chg_port">CHANGE PORT</span></div>
        <div class="tun-body">
          <label>NEW PORT (1-65535, must be free)</label><input id="p-port" placeholder="e.g. 32410">
          <div class="hint">Panel restarts after the change — reconnect via the new URL.</div>
          <div class="rowbtns"><button class="btn pink" onclick="changePort()">CHANGE &amp; RESTART ▸</button></div>
          <div id="reconnect" class="hidden" style="margin-top:10px"></div>
        </div></div>
    </div>
</div>
</div>

<!-- CREATE MODAL -->
<div class="modal" id="modal">
  <div class="sheet">
    <h2 data-i18n="new_tunnel">NEW TUNNEL</h2>
    <div class="hint" id="mc-mode"></div>
    <div class="steps" id="wz-steps"></div>
    <div id="wz-body"></div>
    <div class="err" id="mc-err"></div>
    <div class="rowbtns">
      <button class="btn ghost" id="wz-back" onclick="wzNav(-1)">◂ <span data-i18n="back">BACK</span></button>
      <button class="btn pink" id="wz-next" onclick="wzNav(1)">NEXT ▸</button>
      <button class="btn ghost" onclick="closeCreate()" data-i18n="cancel">CANCEL</button>
    </div>
  </div>
</div>

<!-- FORWARDS MODAL -->
<div class="modal" id="modal-fw">
  <div class="sheet">
    <h2 data-i18n="pf">PORT FORWARDS</h2>
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

<!-- PEER CARD MODAL -->
<div class="modal" id="modal-peer">
  <div class="sheet">
    <h2 data-i18n="peer">PEER SETUP CARD</h2>
    <div class="hint" id="peer-sub">Enter these values on the OTHER server.</div>
    <div id="peercard" class="logview" style="color:var(--txt)">loading…</div>
    <div class="rowbtns">
      <button class="btn" onclick="copyPeer()">COPY ▸</button>
      <button class="btn ghost" onclick="closePeer()">CLOSE</button>
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
    const t=r.tunnels;LAST=t;let on=0,fw=0;
    t.forEach(x=>{if(x.running)on++;fw+=(x.forwards||[]).length;});
    document.getElementById('s-total').textContent=t.length;
    document.getElementById('s-on').textContent=on;
    document.getElementById('s-off').textContent=t.length-on;
    document.getElementById('s-fw').textContent=fw;
    document.getElementById('m-count').textContent=t.length+' TUNNELS';
    const box=document.getElementById('tunnels');box.innerHTML='';
    if(!t.length){box.innerHTML=`<div class="tun"><div class="tun-body">${t('no_tun')}</div></div>`;return;}
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
          <span class="tname" style="cursor:pointer" onclick="openDetail('${esc(x.name)}')">${esc(x.name)}</span>
          <span class="ttype">${esc(x.type.toUpperCase())}</span>
          <span class="tstatus ${x.running?'on':'off'}">${esc(x.status).toUpperCase()}</span>
        </div>
        <div class="tun-body">
          <div class="kv">${kv}</div>
          ${peers?`<div class="peers">PEERS<br>${peers}</div>`:''}
          <div class="fwds">FORWARDS<br>${fw}</div>
          <div class="fwds" id="traf-${esc(x.name)}">TRAFFIC<br><span class="hint">loading…</span></div>
          <div class="rowbtns">
            <button class="btn" onclick="openDetail('${esc(x.name)}')">${t('overview')}</button>
            <button class="btn" onclick="act('${esc(x.name)}','start')">${t('start')}</button>
            <button class="btn" onclick="act('${esc(x.name)}','restart')">${t('restart')}</button>
            <button class="btn" onclick="act('${esc(x.name)}','stop')">${t('stop')}</button>
            <button class="btn pink" onclick="openFw('${esc(x.name)}')">${t('forwards')}</button>
            <button class="btn ghost" onclick="pingTest('${esc(x.name)}')">${t('ping_test')}</button>
            <button class="btn ghost" onclick="openPeer('${esc(x.name)}')">${t('peer_card')}</button>
            <button class="btn danger" onclick="del('${esc(x.name)}')">${t('delete')}</button>
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
    toast(r.ok?'Done ✓':'Failed ✗',r.ok);await refresh();
    if(DETAIL){const x=LAST.find(v=>v.name===DETAIL);if(x)renderDetail(x);}
  }catch(err){toast(err.message,false);}
}
async function del(name){
  if(!confirm('Delete tunnel "'+name+'"?'))return;
  act(name,'delete');
}
/* ---- i18n + theme + boot ---- */
const I18N={
en:{subtitle:'CYBER TUNNEL CONTROL',login_sub:'CYBER TUNNEL CONTROL // SECURE ACCESS',
 username:'USERNAME',password:'PASSWORD',login_btn:'JACK IN ▸',
 tab_tunnels:'TUNNELS',tab_system:'SYSTEM',tab_network:'NETWORK',tab_panel:'PANEL',
 new_tunnel:'+ NEW TUNNEL',logout:'LOGOUT',back:'BACK',cancel:'CANCEL',next:'NEXT ▸',deploy:'DEPLOY ▸',
 overview:'OVERVIEW',traffic:'TRAFFIC',forwards:'FORWARDS',logs:'LOGS',peer:'PEER',
 total:'TOTAL',online:'ONLINE',offline:'OFFLINE',fwds:'FORWARDS',
 start:'START',restart:'RESTART',stop:'STOP',delete:'DELETE',ping_test:'PING TEST',peer_card:'PEER CARD',
 manage:'MANAGE',refresh:'REFRESH',load:'LOAD ▸',enable:'ENABLE',disable:'DISABLE',validate:'VALIDATE',
 services:'SERVICES',logs_t:'LOGS',fwd_engine:'FORWARD ENGINE',cron:'AUTO-RESTART CRON',tcp:'TCP OPTIMIZATION',
 dns:'DNS MANAGER',speed:'SPEED TEST',access:'ACCESS',chg_pass:'CHANGE PASSWORD',chg_port:'CHANGE PORT',
 https:'HTTPS',tg:'TELEGRAM ALERTS',backup:'BACKUP & RESTORE',update:'UPDATE FROM GITHUB',pf:'PORT FORWARDS',
 new_t:'NEW TUNNEL',no_tun:'No tunnels yet — hit + NEW TUNNEL.'},
fa:{subtitle:'کنترل سایبری تانل',login_sub:'کنترل سایبری تانل // دسترسی امن',
 username:'نام کاربری',password:'گذرواژه',login_btn:'ورود ▸',
 tab_tunnels:'تانل‌ها',tab_system:'سیستم',tab_network:'شبکه',tab_panel:'پنل',
 new_tunnel:'+ تانل جدید',logout:'خروج',back:'بازگشت',cancel:'انصراف',next:'بعدی ▸',deploy:'استقرار ▸',
 overview:'نمای کلی',traffic:'ترافیک',forwards:'فورواردها',logs:'لاگ‌ها',peer:'همتا',
 total:'کل',online:'آنلاین',offline:'آفلاین',fwds:'فورواردها',
 start:'استارت',restart:'ری‌استارت',stop:'توقف',delete:'حذف',ping_test:'تست پینگ',peer_card:'کارت همتا',
 manage:'مدیریت',refresh:'به‌روزرسانی',load:'بارگذاری ▸',enable:'فعال',disable:'غیرفعال',validate:'اعتبارسنجی',
 services:'سرویس‌ها',logs_t:'لاگ‌ها',fwd_engine:'موتور فوروارد',cron:'ری‌استارت خودکار',tcp:'بهینه‌سازی TCP',
 dns:'مدیریت DNS',speed:'تست سرعت',access:'دسترسی',chg_pass:'تغییر گذرواژه',chg_port:'تغییر پورت',
 https:'HTTPS',tg:'هشدار تلگرام',backup:'بکاپ و بازیابی',update:'آپدیت از گیت‌هاب',pf:'فوروارد پورت',
 new_t:'تانل جدید',no_tun:'هنوز تانلی نیست — «+ تانل جدید» را بزن.'}};
let LANG=localStorage.getItem('v3lang')||'en';
function t(k){return (I18N[LANG]&&I18N[LANG][k])||I18N.en[k]||k;}
function applyLang(){
  document.querySelectorAll('[data-i18n]').forEach(el=>{el.textContent=t(el.getAttribute('data-i18n'));});
  document.querySelectorAll('[data-i18n-ph]').forEach(el=>{el.setAttribute('placeholder',t(el.getAttribute('data-i18n-ph')));});
  document.getElementById('btn-lang').textContent=LANG==='en'?'FA':'EN';
  if(typeof refresh==='function'&&!document.getElementById('view-dash').classList.contains('hidden'))refresh();
}
function cycleLang(){LANG=LANG==='en'?'fa':'en';
  try{localStorage.setItem('v3lang',LANG);}catch(e){}
  document.documentElement.setAttribute('dir',LANG==='fa'?'rtl':'');
  applyLang();}
const THEMES=['cyberpunk','matrix','solar'];
function cycleTheme(){
  const cur=document.documentElement.getAttribute('data-theme')||'cyberpunk';
  const nxt=THEMES[(THEMES.indexOf(cur)+1)%THEMES.length];
  document.documentElement.setAttribute('data-theme',nxt);
  try{localStorage.setItem('v3theme',nxt);}catch(e){}
  toast('Theme: '+nxt);
}
const BOOT_LINES=['VORTEXL3 SECURE SHELL v'+'5.4.0','> establishing uplink ............ OK',
 '> verifying tunnel grid .......... OK','> access granted — welcome, operator'];
let BOOT_TIMER=null;
function runBoot(){
  const box=document.getElementById('boot'),pre=document.getElementById('boot-txt');
  if(!box||!pre)return;
  box.style.display='flex';pre.textContent='';let i=0;
  clearInterval(BOOT_TIMER);
  BOOT_TIMER=setInterval(()=>{
    if(i<BOOT_LINES.length){pre.textContent+=BOOT_LINES[i]+'\n';i++;}
    else{skipBoot();}
  },380);
}
function skipBoot(){clearInterval(BOOT_TIMER);
  const box=document.getElementById('boot');if(box)box.style.display='none';}
runBoot();
/* ---- tunnel detail page ---- */
let DETAIL=null,LAST=[];
function openDetail(name){
  const x=LAST.find(v=>v.name===name);if(!x){toast('Tunnel not loaded',false);return;}
  DETAIL=name;renderDetail(x);
  ['tunnels','system','network','panel'].forEach(v=>document.getElementById('sec-'+v).classList.add('hidden'));
  document.querySelectorAll('#tabs .tab').forEach(b=>b.classList.remove('active'));
  document.getElementById('sec-detail').classList.remove('hidden');
  dtab('info');window.scrollTo(0,0);
}
function backToList(){
  DETAIL=null;document.getElementById('sec-detail').classList.add('hidden');refresh();
}
function renderDetail(x){
  document.getElementById('d-dot').className='dot '+(x.running?'on':'off');
  document.getElementById('d-name').textContent=x.name;
  document.getElementById('d-type').textContent=(x.type||'').toUpperCase();
  const st=document.getElementById('d-status');
  st.textContent=(x.status||'').toUpperCase();st.className='tstatus '+(x.running?'on':'off');
  const rows=x.type==='easytier'
    ?[['INTERFACE',x.interface],['LOCAL IP',x.local_ip],['PEER IP',x.remote_ip],['MESH PORT',x.port]]
    :[['INTERFACE',x.interface],['LOCAL IP',x.local_ip],['REMOTE IP',x.remote_ip],
      ['TUNNEL IP',x.interface_ip],['TUNNEL ID',x.tunnel_id],['ENCAP',x.encap]];
  document.getElementById('d-kv').innerHTML=rows.map(r=>`<div>${r[0]} <b>${esc(r[1]||'-')}</b></div>`).join('');
  document.getElementById('d-peers').innerHTML=(x.peers||[]).length?
    'PEERS<br>'+x.peers.map(p=>`<span class="tag">${esc(p.ipv4)} · ${esc(p.hostname)} · ${esc(p.latency)} · ${esc(p.tunnel)}</span>`).join(''):'';
  document.getElementById('d-fw').innerHTML=(x.forwards||[]).length?
    x.forwards.map(f=>`<span class="tag">${esc(f.port)} → ${esc(f.remote)} ${f.active?'●':'○'}</span>`).join('')
    :'<span class="hint">none</span>';
  document.getElementById('d-fwbtn').onclick=()=>openFw(x.name);
  document.getElementById('d-actions').innerHTML=
    `<button class="btn" onclick="act('${esc(x.name)}','start')">${t('start')}</button>
     <button class="btn" onclick="act('${esc(x.name)}','restart')">${t('restart')}</button>
     <button class="btn" onclick="act('${esc(x.name)}','stop')">${t('stop')}</button>
     <button class="btn ghost" onclick="pingTest('${esc(x.name)}')">${t('ping_test')}</button>
     <button class="btn danger" onclick="del('${esc(x.name)}')">${t('delete')}</button>`;
  loadHistory(6);loadDetailPeer();
}
function dtab(sub,btn){
  ['info','traffic','forwards','logs','peer'].forEach(s=>
    document.getElementById('d-'+s).classList.toggle('hidden',s!==sub));
  if(btn){btn.parentElement.querySelectorAll('.tab').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');}
  if(sub==='traffic')loadHistory(6);
  if(sub==='peer')loadDetailPeer();
}
async function loadDetailPeer(){
  const box=document.getElementById('d-peerbody');if(!DETAIL)return;
  try{const r=await api('/api/peer/card?name='+encodeURIComponent(DETAIL));
    box.textContent=r.ok?Object.entries(r.card).map(([k,v])=>k+': '+v).join('\n')
      :'Error: '+(r.error||'failed');
  }catch(err){box.textContent='Error: '+err.message;}
}
function copyPeer2(){navigator.clipboard.writeText(document.getElementById('d-peerbody').textContent)
  .then(()=>toast('Copied ✓')).catch(()=>toast('Copy failed',false));}
async function loadDetailLogs(){
  const box=document.getElementById('d-logview');box.textContent='Loading…';
  const x=LAST.find(v=>v.name===DETAIL);if(!x)return;
  const svc=x.type==='easytier'?('vortexl3-easytier-'+x.name):'vortexl3-tunnel';
  try{const r=await api('/api/logs?service='+encodeURIComponent(svc)+'&lines=100');
    box.textContent=r.ok?r.output:('Error: '+(r.error||'failed'));
  }catch(err){box.textContent='Error: '+err.message;}
}
/* ---- charts (offline canvas) ---- */
function cssVar(n){return getComputedStyle(document.documentElement).getPropertyValue(n).trim()||'#00f0ff';}
function drawSeries(cv,series,keys,colors){
  const ctx=cv.getContext('2d'),W=cv.width,H=cv.height;
  ctx.clearRect(0,0,W,H);ctx.fillStyle='#02020a';ctx.fillRect(0,0,W,H);
  const pad=8,V=series.map(p=>keys.map(k=>p[k]||0)).flat();
  let mx=Math.max(1,...V);
  ctx.strokeStyle='rgba(120,140,180,.15)';ctx.lineWidth=1;
  for(let g=0;g<=4;g++){const y=pad+(H-2*pad)*g/4;
    ctx.beginPath();ctx.moveTo(pad,y);ctx.lineTo(W-pad,y);ctx.stroke();}
  keys.forEach((k,ki)=>{
    ctx.strokeStyle=colors[ki];ctx.lineWidth=2;ctx.shadowColor=colors[ki];ctx.shadowBlur=8;
    ctx.beginPath();let started=false;
    series.forEach((p,i)=>{
      const x=series.length<2?W/2:pad+(W-2*pad)*i/(series.length-1);
      const y=H-pad-(H-2*pad)*Math.min((p[k]||0)/mx,1);
      if(!started){ctx.moveTo(x,y);started=true;}else ctx.lineTo(x,y);});
    ctx.stroke();ctx.shadowBlur=0;});
  const last=series[series.length-1];
  ctx.font='12px Consolas,monospace';
  keys.forEach((k,ki)=>{ctx.fillStyle=colors[ki];
    ctx.fillText(k+': '+(last?last[k]:0),pad+ki*170,H-4);});
  ctx.fillStyle='rgba(120,140,180,.8)';
  ctx.fillText('max '+mx,pad,14);
}
async function loadHistory(hours){
  if(!DETAIL)return;
  try{const r=await api('/api/history?name='+encodeURIComponent(DETAIL)+'&hours='+hours);
    if(!r.ok||!r.series)return;
    const pts=r.series.points;
    if(!pts.length){toast('No history yet — sampler collects every 30s',false);return;}
    drawSeries(document.getElementById('ch-tp'),pts,['rx_mbps','tx_mbps'],
      [cssVar('--neon'),cssVar('--pink')]);
    drawSeries(document.getElementById('ch-ping'),pts.map(p=>({ping_ms:p.ping_ms||0})),['ping_ms'],['#b6ff00']);
  }catch(err){toast(err.message,false);}
}
async function doFw(how){
  const e=document.getElementById('fw-err');e.style.display='none';
  try{const r=await api('/api/forwards/'+how,{name:FW_TUNNEL,ports:val('fw-ports')});
    if(r.ok){closeFw();log('[FORWARDS '+how.toUpperCase()+'] '+FW_TUNNEL+'\n'+r.message);
      toast('Forwards updated ✓');refresh();}
    else{e.textContent=r.message||r.error;e.style.display='block';}
  }catch(err){e.textContent=err.message;e.style.display='block';}
}
function showTab(n,btn){
  ['tunnels','system','network','panel'].forEach(x=>
    document.getElementById('sec-'+x).classList.toggle('hidden',x!==n));
  document.getElementById('sec-detail').classList.add('hidden');DETAIL=null;
  document.querySelectorAll('#tabs .tab').forEach(b=>b.classList.remove('active'));
  if(btn)btn.classList.add('active');
  if(n==='system'){loadHealth();loadTg();}
  if(n==='network'){loadMode();loadCron();loadTcp();loadDns();loadSpeed();}
  if(n==='panel'){loadPanelInfo();}
}
/* ---- system ---- */
async function loadHealth(){
  try{const r=await api('/api/health');
    if(!r.ok){toast('Health failed',false);return;}
    let h='<table class="sv"><tr><th>SERVICE</th><th>STATE</th><th>ACTIONS</th></tr>';
    r.services.forEach(s=>{
      const pill=s.active?'<span class="pill on">ACTIVE</span>'
        :(s.state==='unknown'?'<span class="pill na">UNKNOWN</span>':'<span class="pill off">'+esc(s.state.toUpperCase())+'</span>');
      h+=`<tr><td>${esc(s.label)}<br><span class="hint">${esc(s.service)}</span></td><td>${pill}</td>
        <td><button class="btn ghost" onclick="svcAct('${esc(s.service)}','start')">START</button>
        <button class="btn ghost" onclick="svcAct('${esc(s.service)}','restart')">RESTART</button>
        <button class="btn danger" onclick="svcAct('${esc(s.service)}','stop')">STOP</button></td></tr>`;
    });
    document.getElementById('health').innerHTML=h+'</table>';
  }catch(err){toast(err.message,false);}
}
async function svcAct(svc,action){
  toast(action.toUpperCase()+' '+svc+' …');
  try{const r=await api('/api/service/action',{service:svc,action});
    log('['+action.toUpperCase()+'] '+svc+'\n'+(r.message||r.error||''));
    toast(r.ok?'Done ✓':'Failed ✗',r.ok);loadHealth();
  }catch(err){toast(err.message,false);}
}
async function loadLogs(){
  const svc=document.getElementById('log-svc').value;
  const lines=document.getElementById('log-lines').value;
  const box=document.getElementById('logview');box.textContent='Loading…';
  try{const r=await api('/api/logs?service='+encodeURIComponent(svc)+'&lines='+lines);
    box.textContent=r.ok?r.output:('Error: '+(r.error||'failed'));
    if(r.services){const sel=document.getElementById('log-svc');
      if(!sel.options.length){r.services.forEach(s=>{const o=document.createElement('option');
        o.value=s;o.textContent=s;sel.appendChild(o);});}}
  }catch(err){box.textContent='Error: '+err.message;}
}
/* ---- network: forwards ---- */
async function loadMode(){
  try{const r=await api('/api/forward/mode');
    if(r.ok)document.getElementById('fw-mode').textContent=r.mode.toUpperCase();
  }catch(err){toast(err.message,false);}
}
async function setMode(m){
  toast('MODE → '+m.toUpperCase()+' …');
  try{const r=await api('/api/forward/mode',{mode:m});
    log('[FORWARD MODE]\n'+(r.message||r.error||''));toast(r.ok?'Done ✓':'Failed ✗',r.ok);loadMode();
  }catch(err){toast(err.message,false);}
}
async function fwRestart(){
  try{const r=await api('/api/forward/restart',{});toast(r.message||'done',r.ok);}catch(err){toast(err.message,false);}
}
async function fwValidate(){
  try{const r=await api('/api/forward/validate',{});
    log('[VALIDATE]\n'+(r.message||r.error||''));toast(r.ok?'Valid ✓':'Failed ✗',r.ok);
  }catch(err){toast(err.message,false);}
}
/* ---- network: cron ---- */
function cronRow(title,key,st,intervals){
  const opts=intervals.map(i=>`<option value="${i}"${(''+i===String(st._sel||60))?' selected':''}>every ${i===60?'hour':i+' min'}</option>`).join('');
  return `<div style="margin:8px 0"><b>${title}</b> — ${st.enabled?'<span class="pill on">'+esc(st.schedule)+'</span>':'<span class="pill off">DISABLED</span>'}
    <div class="rowbtns"><select id="cron-${key}" style="max-width:170px">${opts}</select>
    <button class="btn ghost" onclick="cronSet('${key}','enable')">ENABLE</button>
    <button class="btn danger" onclick="cronSet('${key}','disable')">DISABLE</button></div></div>`;
}
async function loadCron(){
  try{const r=await api('/api/cron/status');
    if(!r.ok)return;
    document.getElementById('cronbox').innerHTML=
      cronRow('PORT FORWARDS','forward',r.forward,r.intervals)+
      cronRow('EASYTier TUNNELS','easytier',r.easytier,r.intervals);
  }catch(err){toast(err.message,false);}
}
async function cronSet(kind,action){
  const iv=document.getElementById('cron-'+kind).value;
  try{const r=await api('/api/cron/'+kind,{action,interval:parseInt(iv,10)});
    toast(r.message||'done',r.ok);loadCron();
  }catch(err){toast(err.message,false);}
}
/* ---- network: tcp ---- */
async function loadTcp(){
  try{const r=await api('/api/tcp/status');
    if(!r.ok){toast('TCP status failed',false);return;}
    document.getElementById('tcpbox').innerHTML=Object.entries(r.params)
      .map(([k,v])=>`<div>${esc(k.split('.').pop())} <b>${esc(v)}</b></div>`).join('');
  }catch(err){toast(err.message,false);}
}
async function applyTcp(){
  toast('Applying TCP optimization …');
  try{const r=await api('/api/tcp/apply',{});
    log('[TCP OPTIMIZATION]\n'+(r.message||r.error||''));toast(r.ok?'Applied ✓':'Failed ✗',r.ok);loadTcp();
  }catch(err){toast(err.message,false);}
}
/* ---- network: dns ---- */
async function loadDns(){
  try{const r=await api('/api/dns/status');
    if(!r.ok)return;
    document.getElementById('dnsbox').innerHTML=
      `<div>SYSTEM DNS <b>${esc(r.system_dns||'-')}</b></div>
       <div>ACTIVE <b>${esc(r.configured_dns||'-')}${r.configured_name?' ('+esc(r.configured_name)+')':''}</b></div>
       <div>LAST CHECK <b>${esc(r.last_check||'-')}</b></div>
       <div>AUTO-CHECK <b>${r.auto_check.enabled?esc(r.auto_check.schedule):'DISABLED'}</b> (every ${esc(r.interval_hours)}h)</div>`;
  }catch(err){toast(err.message,false);}
}
let SCAN_TIMER=null;
async function startScan(){
  try{const r=await api('/api/dns/scan',{});
    if(!r.ok){toast(r.message||'Scan failed',false);return;}
    toast('DNS scan running …');document.getElementById('scanbar').classList.remove('hidden');
    document.getElementById('scanres').textContent='';
    clearInterval(SCAN_TIMER);SCAN_TIMER=setInterval(pollScan,2500);pollScan();
  }catch(err){toast(err.message,false);}
}
async function pollScan(){
  try{const r=await api('/api/dns/scan');
    if(!r.ok)return;
    const total=r.total||1, done=(r.progress||[]).length;
    document.getElementById('scanfill').style.width=Math.min(100,Math.round(done/total*100))+'%';
    if(r.done){clearInterval(SCAN_TIMER);
      const best=r.best?`BEST: ${esc(r.best.name)} (${esc(r.best.ip)}) — ${esc(r.best.score)}ms`:'';
      document.getElementById('scanres').innerHTML=
        `<b>${r.success?'✓ APPLIED':'✗ FAILED'}</b> ${esc(r.message||'')}<br>${best}`;
      toast(r.success?'Best DNS applied ✓':'Scan failed ✗',r.success);loadDns();
    }else{
      const last=(r.progress||[]).slice(-3).map(p=>`${esc(p.name)} ${esc(p.ip)}: ${p.status==='ok'?esc(p.score)+'ms':'fail'}`).join(' · ');
      document.getElementById('scanres').textContent=`Scanning… ${done}/${total} — ${last}`;
    }
  }catch(err){clearInterval(SCAN_TIMER);}
}
async function setDnsHours(){
  const h=parseInt(document.getElementById('dns-hours').value,10);
  try{const r=await api('/api/dns/interval',{hours:h});toast(r.message||'done',r.ok);loadDns();
  }catch(err){toast(err.message,false);}
}
async function dnsAuto(a){
  try{const r=await api('/api/dns/autocheck',{action:a});toast(r.message||'done',r.ok);loadDns();
  }catch(err){toast(err.message,false);}
}
/* ---- panel self-manage ---- */
async function loadPanelInfo(){
  try{const r=await api('/api/panel/info');
    if(!r.ok)return;
    document.getElementById('panelbox').innerHTML=
      `<div>URL <b>${esc(r.url)}</b></div><div>USERNAME <b>${esc(r.username)}</b></div>
       <div>PORT <b>${esc(r.port)}</b></div><div>VERSION <b>${esc(r.version)}</b></div>`;
    document.getElementById('httpsbox').innerHTML=
      `<div>STATUS <b>${r.tls_active?'HTTPS ✓ ACTIVE':(r.https?'HTTPS (applies after restart)':'HTTP')}</b></div>
       <div>URL <b>${esc(r.url)}</b></div>`;
  }catch(err){toast(err.message,false);}
}
async function setHttps(on){
  if(!confirm((on?'Enable HTTPS (self-signed cert)?':'Disable HTTPS (plain HTTP)?')+' Panel will restart.'))return;
  try{const r=await api('/api/panel/https',{enabled:on});
    if(r.ok){document.getElementById('https-reconnect').classList.remove('hidden');
      document.getElementById('https-reconnect').innerHTML=
        `Panel restarting… reconnect in ~10s: <a href="${esc(r.reconnect_url)}">${esc(r.reconnect_url)}</a>`;
      toast('Restarting panel …',true);
    }else toast(r.message||r.error||'failed',false);
  }catch(err){toast(err.message,false);}
}
async function changePw(){
  const cur=document.getElementById('pw-cur').value, nw=document.getElementById('pw-new').value;
  try{const r=await api('/api/panel/password',{current:cur,new:nw});
    toast(r.message||r.error||'done',r.ok);
    if(r.ok){document.getElementById('pw-cur').value='';document.getElementById('pw-new').value='';}
  }catch(err){toast(err.message,false);}
}
async function changePort(){
  const p=parseInt(document.getElementById('p-port').value,10);
  if(!p){toast('Enter a port',false);return;}
  if(!confirm('Panel will restart on port '+p+'. Continue?'))return;
  try{const r=await api('/api/panel/port',{port:p});
    if(r.ok){document.getElementById('reconnect').classList.remove('hidden');
      document.getElementById('reconnect').innerHTML=
        `Panel restarting… reconnect in ~10s: <a href="${esc(r.reconnect_url)}">${esc(r.reconnect_url)}</a>`;
      toast('Restarting panel …',true);
    }else toast(r.message||r.error||'failed',false);
  }catch(err){toast(err.message,false);}
}
/* ---- tunnels: traffic + ping + peer card ---- */
function fmtBytes(b){if(b>=1e9)return (b/1e9).toFixed(2)+' GB';
  if(b>=1e6)return (b/1e6).toFixed(2)+' MB';if(b>=1e3)return (b/1e3).toFixed(1)+' KB';return b+' B';}
async function loadStats(){
  if(document.getElementById('view-dash').classList.contains('hidden'))return;
  if(document.getElementById('sec-tunnels').classList.contains('hidden'))return;
  try{const r=await api('/api/stats');
    if(!r.ok)return;
    (r.traffic||[]).forEach(t=>{
      const el=document.getElementById('traf-'+CSS.escape(t.name));
      if(el)el.innerHTML=`TRAFFIC<br>▼ ${fmtBytes(t.rx_bytes)} (${t.rx_mbps} Mbps) · ▲ ${fmtBytes(t.tx_bytes)} (${t.tx_mbps} Mbps)${t.errors?` · <span style="color:var(--red)">ERR ${t.errors}</span>`:''}`;
    });
  }catch(e){}
}
setInterval(loadStats,4000);
async function pingTest(name){
  toast('Pinging from '+name+' …');
  try{const r=await api('/api/ping',{name});
    if(!r.ok){toast(r.error||'failed',false);return;}
    const lines=r.results.map(x=>`${x.label} ${x.ip}: ${x.ok?'✓': '✗'} avg=${x.avg_ms==null?'-':x.avg_ms+'ms'} loss=${x.loss_pct}%`);
    log('[PING] '+name+'\n'+lines.join('\n'));
    toast(r.results.every(x=>x.ok)?'Peer reachable ✓':'Peer unreachable ✗',r.results.every(x=>x.ok));
  }catch(err){toast(err.message,false);}
}
async function openPeer(name){
  document.getElementById('peer-sub').textContent='Tunnel "'+name+'" — enter these on the OTHER server.';
  document.getElementById('peercard').textContent='loading…';
  document.getElementById('modal-peer').classList.add('open');
  try{const r=await api('/api/peer/card?name='+encodeURIComponent(name));
    if(!r.ok){document.getElementById('peercard').textContent='Error: '+(r.error||'failed');return;}
    document.getElementById('peercard').textContent=
      Object.entries(r.card).map(([k,v])=>k+': '+v).join('\n');
  }catch(err){document.getElementById('peercard').textContent='Error: '+err.message;}
}
function closePeer(){document.getElementById('modal-peer').classList.remove('open');}
function copyPeer(){navigator.clipboard.writeText(document.getElementById('peercard').textContent)
  .then(()=>toast('Copied ✓')).catch(()=>toast('Copy failed',false));}
/* ---- system: telegram ---- */
async function loadTg(){
  try{const r=await api('/api/alerts/status');
    if(!r.ok)return;
    document.getElementById('tgbox').innerHTML=
      `<div>STATUS <b>${r.enabled?'ENABLED':'DISABLED'}</b></div>
       <div>CONFIGURED <b>${r.configured?'YES ('+esc(r.chat_id)+')':'NO'}</b></div>
       <div>LAST CHECK <b>${esc(r.last_check||'-')}</b></div>
       <div>LAST EVENT <b>${esc(r.last_event||'-')}</b></div>`;
    if(r.configured)document.getElementById('tg-chat').value=r.chat_id;
  }catch(err){toast(err.message,false);}
}
async function tgSave(on){
  const t=document.getElementById('tg-token').value.trim(),
        c=document.getElementById('tg-chat').value.trim();
  try{const r=await api('/api/alerts/config',{bot_token:t,chat_id:c,enabled:on});
    toast(r.message||'done',r.ok);loadTg();
  }catch(err){toast(err.message,false);}
}
async function tgTest(){
  try{const r=await api('/api/alerts/test',{});toast(r.message||'done',r.ok);
  }catch(err){toast(err.message,false);}
}
/* ---- system: backup/restore/update ---- */
function doBackup(){window.location='/api/backup';toast('Backup downloading …');}
async function doRestore(){
  const f=document.getElementById('restore-file').files[0];
  if(!f){toast('Select a backup file first',false);return;}
  try{const data=JSON.parse(await f.text());
    const r=await api('/api/restore',data);
    log('[RESTORE]\n'+(r.message||r.error||''));toast(r.ok?'Restored ✓':'Failed ✗',r.ok);refresh();
  }catch(err){toast('Invalid backup file: '+err.message,false);}
}
async function checkUpdate(){
  try{const r=await api('/api/update/check');
    if(!r.ok)return;
    document.getElementById('updbox').innerHTML=
      `<div>CURRENT <b>${esc(r.current)}</b></div>
       <div>LATEST <b>${esc(r.latest||'unknown (offline?)')}</b></div>
       <div>STATUS <b>${r.update_available?'UPDATE AVAILABLE ★':'UP TO DATE ✓'}</b></div>`;
    toast(r.update_available?'Update available ★':'Up to date ✓',!r.update_available?true:undefined);
  }catch(err){toast(err.message,false);}
}
async function runUpdate(){
  if(!confirm('Run the installer update now? Services will restart.'))return;
  try{const r=await api('/api/update/run',{});toast(r.message||'done',r.ok);updateLog(true);
  }catch(err){toast(err.message,false);}
}
let UPD_TIMER=null;
async function updateLog(auto){
  const box=document.getElementById('updlog');box.classList.remove('hidden');
  try{const r=await api('/api/update/log');
    box.textContent=r.log||'(empty)';
    clearInterval(UPD_TIMER);
    if(r.running||auto){UPD_TIMER=setInterval(async()=>{
      try{const q=await api('/api/update/log');box.textContent=q.log||'(empty)';
        if(!q.running)clearInterval(UPD_TIMER);}catch(e){clearInterval(UPD_TIMER);}},3000);}
  }catch(err){toast(err.message,false);}
}
function openFw(name){FW_TUNNEL=name;
  document.getElementById('fw-tun').textContent='TUNNEL: '+name;
  document.getElementById('fw-err').style.display='none';
  document.getElementById('modal-fw').classList.add('open');}
function closeFw(){document.getElementById('modal-fw').classList.remove('open');}
/* ---- create wizard ---- */
let WZ={step:1,data:{},body:{}};
const WZ_STEPS=['SIDE & NAME','ADDRESSES','ADVANCED','REVIEW'];
function openCreate(){WZ={step:1,data:{},body:{}};
  document.getElementById('mc-err').style.display='none';
  document.getElementById('mc-mode').textContent='MODE: '+MODE.toUpperCase();
  wzRender();document.getElementById('modal').classList.add('open');}
function closeCreate(){document.getElementById('modal').classList.remove('open');}
function wzIn(id,label,ph,value){
  return `<div><label>${label}</label><input id="${id}" placeholder="${ph||''}" value="${esc(value||'')}"></div>`;}
function wzSel(id,label,opts,value){
  return `<div><label>${label}</label><select id="${id}">`+
    opts.map(o=>`<option value="${o}"${o===value?' selected':''}>${o}</option>`).join('')+`</select></div>`;}
function wzRender(){
  const d=WZ.data,et=MODE==='easytier';
  document.getElementById('wz-steps').innerHTML=WZ_STEPS.map((s,i)=>
    `<div class="step${WZ.step===i+1?' on':''}${WZ.step>i+1?' done':''}">${i+1} · ${s}</div>`).join('');
  let h='';
  if(WZ.step===1){
    h=`<div class="grid2">${wzSel('w-side','SIDE',['IRAN','KHAREJ'],d.side||'IRAN')}
      ${wzIn('w-name','NAME','tunnel1',d.name)}</div>
      <div class="hint">Name: letters, numbers, dashes. Must be unique on this server.</div>`;
  }else if(WZ.step===2){
    h=et?`<div class="grid2">${wzIn('w-etip','TUNNEL INTERFACE IP','auto (e.g. 10.155.155.1)',d.etip)}
      ${wzIn('w-etpeer','PEER SERVER PUBLIC IP *','9.9.9.9',d.etpeer)}</div>
      <div class="grid2">${wzIn('w-etport','MESH PORT','auto (2070)',d.etport)}</div>`
    :`<div class="grid2">${wzIn('w-local','LOCAL SERVER PUBLIC IP *','1.2.3.4',d.local)}
      ${wzIn('w-remote','REMOTE SERVER PUBLIC IP *','5.6.7.8',d.remote)}</div>
      <div class="grid2">${wzSel('w-encap','ENCAP',['ip','udp'],d.encap||'ip')}</div>
      <div class="hint">UDP pierces some filters better; IP is simpler.</div>`;
  }else if(WZ.step===3){
    h=et?`<div class="grid2">${wzIn('w-ethost','HOSTNAME','auto',d.ethost)}
      ${wzIn('w-etsec','NETWORK SECRET','vortexl2',d.etsec)}</div>
      <div class="grid2">${wzIn('w-etrf','REMOTE FORWARD IP (IRAN side)','auto',d.etrf)}</div>
      <div class="hint">Secret + mesh port must match the other server. Network name auto-derives from secret.</div>`
    :`<div class="grid2">${wzIn('w-ifip','INTERFACE IP','auto',d.ifip)}
      ${wzIn('w-rfwd','REMOTE FORWARD IP (IRAN)','auto',d.rfwd)}</div>
      <div class="grid2">${wzIn('w-udp','UDP PORT (udp encap)','auto',d.udp)}
      ${wzIn('w-tid','TUNNEL ID','auto',d.tid)}</div>
      <div class="grid2">${wzIn('w-ptid','PEER TUNNEL ID','auto',d.ptid)}
      ${wzIn('w-sid','SESSION ID','auto',d.sid)}</div>
      <div class="grid2">${wzIn('w-psid','PEER SESSION ID','auto',d.psid)}</div>
      <div class="hint">Empty = smart auto value. IDs must mirror the other server.</div>`;
  }else{
    wzCollect();
    const rows=Object.entries(WZ.body).filter(([,v])=>v!==''&&v!=null)
      .map(([k,v])=>k+': '+v).join('\n')||'(defaults)';
    h=`<div class="review">${esc(rows)}</div>
      <div class="hint">Deploy creates the tunnel and starts it immediately.</div>`;
  }
  document.getElementById('wz-body').innerHTML=h;
  document.getElementById('wz-back').style.visibility=WZ.step===1?'hidden':'visible';
  document.getElementById('wz-next').textContent=WZ.step===4?t('deploy'):'NEXT ▸';
  document.getElementById('mc-err').style.display='none';
}
function wzCollect(){
  const g=id=>{const el=document.getElementById(id);return el?el.value.trim():'';};
  Object.assign(WZ.data,{side:g('w-side')||WZ.data.side||'IRAN',name:g('w-name')||WZ.data.name||'',
    local:g('w-local'),remote:g('w-remote'),encap:g('w-encap')||WZ.data.encap||'ip',
    ifip:g('w-ifip'),rfwd:g('w-rfwd'),udp:g('w-udp'),tid:g('w-tid'),ptid:g('w-ptid'),
    sid:g('w-sid'),psid:g('w-psid'),etip:g('w-etip'),etpeer:g('w-etpeer'),etport:g('w-etport'),
    ethost:g('w-ethost'),etsec:g('w-etsec'),etrf:g('w-etrf')});
  const d=WZ.data;
  if(MODE==='easytier'){
    WZ.body={side:d.side||'IRAN',name:d.name||'',local_ip:d.etip||'',peer_ip:d.etpeer||'',
      port:d.etport||'',hostname:d.ethost||'',network_secret:d.etsec||'',remote_forward_ip:d.etrf||''};
  }else{
    WZ.body={side:d.side||'IRAN',name:d.name||'',local_ip:d.local||'',remote_ip:d.remote||'',
      interface_ip:d.ifip||'',remote_forward_ip:d.rfwd||'',encap:d.encap||'ip',udp_port:d.udp||'',
      tunnel_id:d.tid||'',peer_tunnel_id:d.ptid||'',session_id:d.sid||'',peer_session_id:d.psid||''};
  }
}
function wzValid(){
  const e=document.getElementById('mc-err');
  const bad=m=>{e.textContent=m;e.style.display='block';return false;};
  if(WZ.step===1&&!document.getElementById('w-name').value.trim())return bad('Name is required');
  if(WZ.step===2){
    if(MODE==='easytier'){if(!document.getElementById('w-etpeer').value.trim())return bad('Peer server public IP is required');}
    else{if(!document.getElementById('w-local').value.trim())return bad('Local server public IP is required');
      if(!document.getElementById('w-remote').value.trim())return bad('Remote server public IP is required');}
  }
  e.style.display='none';return true;
}
function wzNav(d){
  if(d>0){
    if(WZ.step<4){wzCollect();if(!wzValid())return;WZ.step++;wzRender();}
    else{wzDeploy();}
  }else{WZ.step=Math.max(1,WZ.step-1);wzRender();}
}
async function wzDeploy(){
  const e=document.getElementById('mc-err');e.style.display='none';
  const b=document.getElementById('wz-next');b.disabled=true;
  try{const r=await api('/api/tunnel/create',WZ.body);
    if(r.ok){closeCreate();log('[CREATE]\n'+r.message);toast('Tunnel deployed ✓');refresh();}
    else{e.textContent=r.message||r.error;e.style.display='block';}
  }catch(err){e.textContent=err.message;e.style.display='block';}
  b.disabled=false;
}
/* ---- network: speed test ---- */
async function loadSpeed(){
  try{const r=await api('/api/speed/status');
    if(!r.ok)return;
    document.getElementById('speedbox').innerHTML=
      `<div>IPERF3 <b>${r.installed?'INSTALLED':'NOT INSTALLED'}</b></div>
       <div>SERVER <b>${r.server_running?'RUNNING :5201':'STOPPED'}</b></div>
       ${r.result&&r.result.mbps_received!==undefined?`<div>LAST <b>▼ ${esc(r.result.mbps_received)} Mbps · ▲ ${esc(r.result.mbps_sent)} Mbps</b></div>`:''}
       <div>STATE <b>${esc(r.phase||'idle')}${r.running?' …':''}</b> ${esc(r.message||'')}</div>`;
    const sel=document.getElementById('sp-target');
    if(sel&&!sel.options.length){(r.targets||[]).forEach(x=>{const o=document.createElement('option');
      o.value=x.ip;o.textContent=`${x.tunnel} · ${x.label} · ${x.ip}`;sel.appendChild(o);});}
  }catch(err){toast(err.message,false);}
}
async function speedInstall(){
  try{const r=await api('/api/speed/install',{});toast(r.message||'done',r.ok);
    if(r.ok)setTimeout(loadSpeed,4000);}catch(err){toast(err.message,false);}
}
async function speedServer(a){
  try{const r=await api('/api/speed/server',{action:a});toast(r.message||'done',r.ok);loadSpeed();
  }catch(err){toast(err.message,false);}
}
let SPD_TIMER=null;
async function speedRun(){
  const ip=document.getElementById('sp-target').value,
        dur=parseInt(document.getElementById('sp-dur').value,10);
  if(!ip){toast('No target available',false);return;}
  try{const r=await api('/api/speed/run',{target:ip,duration:dur});
    if(!r.ok){toast(r.message||'failed',false);return;}
    toast('Speed test running …');document.getElementById('speedres').textContent='Testing '+ip+' …';
    clearInterval(SPD_TIMER);SPD_TIMER=setInterval(async()=>{
      try{const q=await api('/api/speed/status');
        document.getElementById('speedres').innerHTML='<b>'+esc(q.message||'')+'</b>';
        if(!q.running){clearInterval(SPD_TIMER);
          if(q.result)document.getElementById('speedres').innerHTML+=
            `<br>▼ ${esc(q.result.mbps_received)} Mbps · ▲ ${esc(q.result.mbps_sent)} Mbps · retrans ${esc(q.result.retransmits)}`;
          loadSpeed();}
      }catch(e){clearInterval(SPD_TIMER);}},3000);
  }catch(err){toast(err.message,false);}
}
refresh().catch(()=>{});applyLang();
</script>
</body>
</html>
"""
