// ChronoKen dashboard script (interactive demo)
document.addEventListener("DOMContentLoaded", () => {
  console.log('dashboard.js loaded');
  // In-page error overlay to capture runtime errors (helps debugging without DevTools)
  const _errorOverlay = document.createElement('div');
  _errorOverlay.id = 'error-overlay';
  Object.assign(_errorOverlay.style, {position:'fixed',left:'12px',right:'12px',bottom:'12px',zIndex:9999,background:'rgba(10,12,16,0.96)',color:'#fff',padding:'12px',borderRadius:'8px',boxShadow:'0 8px 30px rgba(0,0,0,0.6)',fontSize:'13px',display:'none',maxHeight:'40vh',overflow:'auto'});
  const _errClose = document.createElement('button'); _errClose.textContent='✕'; Object.assign(_errClose.style,{position:'absolute',right:'8px',top:'6px',background:'transparent',border:'none',color:'#fff',fontSize:'14px',cursor:'pointer'});
  const _errPre = document.createElement('pre'); _errPre.style.whiteSpace='pre-wrap'; _errPre.style.margin='0';
  _errorOverlay.appendChild(_errClose); _errorOverlay.appendChild(_errPre); document.body.appendChild(_errorOverlay);
  _errClose.addEventListener('click', ()=>{ _errorOverlay.style.display='none'; });
  function showErrorOverlay(msg){ _errPre.textContent = msg; _errorOverlay.style.display = 'block'; }
  // send the first UI error (dev-only) to the server log endpoint for easier debugging
  let _firstUiErrorSent = false;
  function _sendFirstUiError(payload){
    if(_firstUiErrorSent) return;
    _firstUiErrorSent = true;
    try{
      // best-effort, do not block or throw
      fetch('/api/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify(payload)
      }).catch(()=>{});
    }catch(e){}
  }

  window.addEventListener('error', function(ev){
    try{
      const stack = ev && ev.error && ev.error.stack ? ev.error.stack : null;
      const msg = ev && ev.message ? ev.message : (ev && ev.error ? String(ev.error) : String(ev));
      const out = stack || msg || 'Unknown error';
      showErrorOverlay('Error: ' + out);
      // send minimal context to server (dev-only)
      _sendFirstUiError({
        type: 'error',
        message: msg,
        stack: stack || null,
        href: location.href,
        userAgent: navigator.userAgent,
        timestamp: new Date().toISOString()
      });
    }catch(e){}
  });

  window.addEventListener('unhandledrejection', function(ev){
    try{
      const reason = ev && ev.reason ? ev.reason : 'Unhandled promise rejection';
      const stack = reason && reason.stack ? reason.stack : (typeof reason === 'object' ? JSON.stringify(reason) : String(reason));
      const out = stack || String(reason);
      showErrorOverlay('UnhandledRejection: ' + out);
      _sendFirstUiError({
        type: 'unhandledrejection',
        message: typeof reason === 'string' ? reason : (reason && reason.message) || String(reason),
        stack: stack || null,
        href: location.href,
        userAgent: navigator.userAgent,
        timestamp: new Date().toISOString()
      });
    }catch(e){}
  });
  // Simple app state
  const state = {
    missions: [
      {id:1,title:"DBMS assignment",hours:3,priority:"high",status:"pending"},
      {id:2,title:"Math practice",hours:1.5,priority:"medium",status:"pending"},
      {id:3,title:"Revise notes - OS",hours:0.5,priority:"low",status:"in_progress"},
    ],
    notes: [],
    sessions:0,
    focusedMinutes:0
  };

  // Require server-side authentication when loading the dashboard page directly.
  // If the user is not authenticated, redirect to the login page.
  (async function ensureAuthenticatedOnLoad(){
    try{
      const meResp = await fetch('/api/me', { credentials: 'same-origin' });
      if(!meResp || !meResp.ok){
        window.location.href = 'login.html';
        return;
      }
      const meJson = await meResp.json().catch(()=>({}));
      if(!meJson || !meJson.user){
        window.location.href = 'login.html';
        return;
      }
      // authenticated — allow the page to continue loading
    }catch(err){
      console.warn('Dashboard auth check failed', err);
      window.location.href = 'login.html';
    }
  })();

  // --- VIEW SWITCH ---
  const menuItems = document.querySelectorAll(".menu-item");
  const views = document.querySelectorAll(".view");
  const sidebar = document.querySelector('.sidebar');
  const sidebarToggle = document.getElementById('sidebarToggle');
  // Toggle sidebar visibility (used for mobile / narrow screens)
  function setSidebarCollapsed(collapsed){
    if(!sidebar) return;
    if(collapsed) sidebar.classList.add('collapsed'); else sidebar.classList.remove('collapsed');
  }
  sidebarToggle?.addEventListener('click', ()=>{ if(!sidebar) return; sidebar.classList.toggle('collapsed'); });
  // Ensure sidebar is visible on large screens
  window.addEventListener('resize', ()=>{ if(window.innerWidth > 1200) setSidebarCollapsed(false); });
  menuItems.forEach(btn => {
    btn.addEventListener("click", async () => {
      // If the user clicked the Dashboard item, require server-side login first.
      const view = btn.dataset.view;
      if(view === 'dashboard'){
        try{
          const meResp = await fetch('/api/me', { credentials: 'same-origin' });
          if(meResp && meResp.ok){
            const me = await meResp.json().catch(()=>({}));
            if(!me || !me.user){
              // not logged in -> redirect to login page
              window.location.href = 'login.html';
              return;
            }
            // else continue to render dashboard as authenticated user
          } else {
            // fallback: if server unreachable, redirect to login so user can sign in
            window.location.href = 'login.html';
            return;
          }
        }catch(err){
          console.warn('auth check failed', err);
          window.location.href = 'login.html';
          return;
        }
      }

      // proceed with existing click handler logic
      btn.dispatchEvent(new Event('data-view-checked'));
    });

    // attach the original handler logic under a custom event so flow is clearer
    btn.addEventListener('data-view-checked', () => {
      // original click handler body follows below (kept intact)
      menuItems.forEach(m=>m.classList.remove("active"));
      btn.classList.add("active");
      const view = btn.dataset.view;
      // If the clicked view is 'summon', open the floating chat modal instead of navigating
      if(view === 'summon'){
        openSummonModal();
        return;
      }
      // If the clicked view is one of the dashboard panels, keep the dashboard
      // page active and apply the corresponding compact grid modifier so the
      // main area shows only the requested panel (Today/Missions/Timeline/etc).
      // Note: treat 'focus' as a full-page view (not a small dashboard panel)
      const dashboardPanelViews = ['dashboard','missions','timeslices','timeline','scrolls','analytics','summon'];
      views.forEach(v=>v.classList.remove("active"));
      const grid = document.querySelector('#view-dashboard .grid');
      if(dashboardPanelViews.includes(view)){
        // activate dashboard view
        const dv = document.getElementById('view-dashboard');
        if(dv) dv.classList.add('active');
        // clear previous modifiers
        if(grid) grid.classList.remove('show-today-only','show-missions-only','show-timeline-only','show-focus-only','show-scrolls-only','show-analytics-only','show-summon-only');
        // apply appropriate modifier
        if(view === 'dashboard') grid?.classList.add('show-today-only');
        else if(view === 'missions') grid?.classList.add('show-missions-only');
        else if(view === 'timeslices' || view === 'timeline') grid?.classList.add('show-timeline-only');
        else if(view === 'focus') grid?.classList.add('show-focus-only');
        else if(view === 'scrolls') grid?.classList.add('show-scrolls-only');
        else if(view === 'analytics') grid?.classList.add('show-analytics-only');
        else if(view === 'summon') grid?.classList.add('show-summon-only');
        // special-case summon: open the modal instead of switching view
        if(view === 'summon') { openSummonModal(); }
      } else {
        // non-dashboard views map to top-level view-<name> sections
        const target = document.getElementById('view-' + view);
        if(target){
          target.classList.add('active');
        } else {
          const dv = document.getElementById('view-dashboard'); if(dv) dv.classList.add('active');
        }
      }

      // Auto-collapse sidebar on narrow screens after a menu selection to maximize content area
      try{
        if(window.innerWidth <= 900 && sidebar){ setSidebarCollapsed(true); }
      }catch(e){}
      // smooth scroll to top
      window.scrollTo({top:0,behavior:"smooth"});
      // pre-fill some relevant views (render data even when we stay on the dashboard)
      if(view==="missions") renderAllMissions();
      if(view==="timeslices" || view==="timeline") renderPlans();
      // (summon handled by modal open)
    });
  });

  // --- RENDER TODAY TASKS & MISSIONS ---
  function renderToday() {
    const todayTasks = document.getElementById("todayTasks");
    if(!todayTasks) return;
    todayTasks.innerHTML = "";
    state.missions.filter(m => m.status !== "done").slice(0,5).forEach(m => {
      const li = document.createElement("li");
      li.innerHTML = `<div class="mission-meta"><strong>${escapeHtml(m.title)}</strong><span class="muted">${m.hours} hrs • ${m.priority}</span></div>
                      <div><button class="btn small" data-action="start" data-id="${m.id}">Start</button></div>`;
      todayTasks.appendChild(li);
    });
  }

  // small helper to escape text inserted into HTML
  function escapeHtml(s){ return String(s||'').replace(/[&<>"']/g, c=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c])); }

  // expose helper for inline handler above
  window.markInProgress = (id) => {
    const f = state.missions.find(m=>m.id===id);
    if(f) { f.status="in_progress"; renderToday(); renderMissionsList(); updateAnalytics(); }
  }

  function renderMissionsList() {
    const list = document.getElementById("missionsList");
    if(!list) return;
    list.innerHTML = "";
    state.missions.forEach(m => {
      const li = document.createElement("li");
      li.innerHTML = `<div>
          <div style="display:flex;gap:10px;align-items:center">
            <strong>${escapeHtml(m.title)}</strong>
            <span class="${m.priority==='high'?'priority-high':m.priority==='medium'?'priority-medium':'priority-low'}" style="margin-left:8px">${m.priority}</span>
          </div>
          <div class="muted small">${m.hours} hrs • ${m.status}</div>
        </div>
        <div>
          <button class="btn small" data-action="complete" data-id="${m.id}">Done</button>
          <button class="btn ghost small" data-action="edit" data-id="${m.id}">Edit</button>
        </div>`;
      list.appendChild(li);
    });
  }
  // Global delegated handler for mission action buttons (start/complete/edit)
  function _handleMissionButton(btn){
    if(!btn) return null;
    const action = btn.dataset.action;
    const idRaw = btn.dataset.id;
    if(!action || !idRaw) return null;
    return { action, id: idRaw };
  }

  document.body.addEventListener('click', async (ev) => {
    try{
      const btn = ev.target.closest('button[data-action][data-id]');
      const info = _handleMissionButton(btn);
      if(!info) return;
      const {action, id} = info;
      if(action === 'start'){
        const m = state.missions.find(x=>String(x.id)===String(id));
        if(m){ m.status = 'in_progress'; renderToday(); renderMissionsList(); updateAnalytics(); }
        return;
      }
      if(action === 'complete'){
        const m = state.missions.find(x=>String(x.id)===String(id));
        if(!m) return;
        const prev = Object.assign({}, m);
        m.status = 'done'; renderToday(); renderMissionsList(); updateAnalytics();
        try{
          const r = await fetch('/api/tasks/' + encodeURIComponent(id), { method: 'PATCH', headers:{'Content-Type':'application/json'}, credentials:'same-origin', body: JSON.stringify({status:'done'}) });
          if(r.ok){ const j = await r.json(); if(j.task){ const idx = state.missions.findIndex(x=>String(x.id)===String(id)); if(idx!==-1) state.missions[idx] = j.task; renderMissionsList(); renderToday(); updateAnalytics(); } }
          else { throw new Error('server error'); }
        }catch(e){ alert('Failed to mark done: ' + e.message); const idx = state.missions.findIndex(x=>String(x.id)===String(id)); if(idx!==-1) state.missions[idx] = prev; renderMissionsList(); renderToday(); updateAnalytics(); }
        return;
      }
      if(action === 'edit'){
        const m = state.missions.find(x=>String(x.id)===String(id));
        if(!m) return alert('Not found');
        const newTitle = prompt('Edit title', m.title);
        if(!newTitle) return;
        const prev = Object.assign({}, m);
        m.title = newTitle; renderMissionsList(); renderToday(); updateAnalytics();
        try{
          const r = await fetch('/api/tasks/' + encodeURIComponent(id), { method: 'PATCH', headers:{'Content-Type':'application/json'}, credentials:'same-origin', body: JSON.stringify({title: newTitle}) });
          if(r.ok){ const j = await r.json(); if(j.task){ const idx = state.missions.findIndex(x=>String(x.id)===String(id)); if(idx!==-1) state.missions[idx] = j.task; renderMissionsList(); renderToday(); updateAnalytics(); } }
          else { throw new Error('server error'); }
        }catch(e){ alert('Failed to update task: ' + e.message); const idx = state.missions.findIndex(x=>String(x.id)===String(id)); if(idx!==-1) state.missions[idx] = prev; renderMissionsList(); renderToday(); updateAnalytics(); }
        return;
      }
    }catch(err){
      console.error('mission action handler error', err);
      showErrorOverlay('Mission handler error: ' + (err && err.message));
    }
  });

  // create mission
  const _createBtn = document.getElementById("createTaskBtn");
  if(!_createBtn){ console.warn('createTaskBtn not found'); }
  _createBtn?.addEventListener("click", async () => {
    const titleEl = document.getElementById("newTaskTitle");
    const title = titleEl.value.trim();
    const priority = document.getElementById("newTaskPriority").value;
    const hours = parseFloat(document.getElementById("newTaskHours").value) || 1;
    if(!title) return alert("Enter a mission title");
    // optimistic UI update
    const tempId = 'tmp-' + Date.now();
    const optimistic = {id: tempId, title, hours, priority, status: 'pending'};
    state.missions.unshift(optimistic);
    renderMissionsList(); renderToday(); updateAnalytics();
    titleEl.value = '';
    // persist to server
    try{
      const resp = await fetch('/api/tasks', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        credentials: 'same-origin',
        body: JSON.stringify({title, priority, hours})
      });
      const j = await resp.json();
      if(resp.ok && j.task){
        // replace temp with server task (match by temp id)
        const idx = state.missions.findIndex(m => m.id === tempId);
        if(idx !== -1){ state.missions[idx] = j.task; }
        else { state.missions.unshift(j.task); }
        renderMissionsList(); renderToday(); updateAnalytics();
      } else {
        // server returned error
        alert('Failed to save task: ' + (j.error || JSON.stringify(j)));
        // remove optimistic
        state.missions = state.missions.filter(m => m.id !== tempId);
        renderMissionsList(); renderToday(); updateAnalytics();
      }
    }catch(e){
      console.error('createTask error', e);
      showErrorOverlay('Create task error: ' + (e && e.message));
      // rollback optimistic update
      state.missions = state.missions.filter(m => m.id !== tempId);
      renderMissionsList(); renderToday(); updateAnalytics();
      alert('Network error saving task: ' + e.message);
    }
  });

  // Render all missions view
  function renderAllMissions(){
    const out = document.getElementById("allMissions");
    if(!out) return;
    out.innerHTML = "";
    state.missions.forEach(m=>{
      const li = document.createElement("li");
      li.className="missions-list-item";
      li.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center">
        <div><strong>${escapeHtml(m.title)}</strong><div class="muted">${m.hours} hrs • ${m.priority} • ${m.status}</div></div>
        <div><button class="btn small" data-action="complete" data-id="${m.id}">Done</button></div>
      </div>`;
      out.appendChild(li);
    });
  }

  // NOTES
  document.getElementById("saveNote")?.addEventListener("click", ()=>{
    const tEl = document.getElementById("quickNote");
    if(!tEl) return;
    const t = tEl.value.trim();
    if(!t) return;
    state.notes.push({id:Date.now(),text:t});
    tEl.value="";
    renderNotes();
  });
  function renderNotes(){
    const out = document.getElementById("notesList");
    if(!out) return;
    out.innerHTML="";
    state.notes.forEach(n=>{
      const li = document.createElement("li");
      li.innerHTML = `<div>${escapeHtml(n.text)}</div><div style="margin-top:6px"><button class="btn small" onclick="noteToMission(${n.id})">Convert to Mission</button></div>`;
      out.appendChild(li);
    });
  }
  window.noteToMission = (id) => {
    const note = state.notes.find(x=>x.id===id);
    if(!note) return;
    const title = note.text.split("\n")[0].slice(0,60);
    state.missions.push({id:Date.now(),title,hours:1,priority:"medium",status:"pending"});
    state.notes = state.notes.filter(x=>x.id!==id);
    renderNotes(); renderMissionsList(); renderToday(); updateAnalytics();
  }

  // PLANS (simple generator)
  function renderPlans(){
    const plans = document.getElementById("plansContainer");
    if(!plans) return;
    plans.innerHTML = "";
    // naive plan: schedule all pending tasks sequentially
    const pending = state.missions.filter(m=>m.status!=="done");
    pending.forEach((p, i)=>{
      const card = document.createElement("div");
      card.className="card";
      card.style.marginBottom="10px";
      card.innerHTML = `<div style="display:flex;justify-content:space-between"><strong>${escapeHtml(p.title)}</strong><span class="muted">${p.hours} hrs</span></div>
        <div class="muted small">Start: +${i*2}h • End: +${(i*2)+p.hours}h</div>
        <div style="margin-top:8px"><button class="btn small" onclick="addPlanToCalendarSample('${escapeHtml(p.title)}')">Add to Calendar</button></div>`;
      plans.appendChild(card);
    });
  }

  // Today plan UI
  function renderTodayPlan(){
    const el = document.getElementById("todayPlan");
    if(!el) return;
    el.innerHTML="";
    const pending = state.missions.filter(m=>m.status!=="done").slice(0,4);
    pending.forEach(m=>{
      const div = document.createElement("div");
      div.className="plan-slot";
      div.innerHTML = `<strong>${escapeHtml(m.title)}</strong><div class="muted small">${m.hours} hrs • ${m.priority}</div>`;
      el.appendChild(div);
    });
  }

  // Analytics simple
  function updateAnalytics(){
    const focused = Math.round(state.focusedMinutes / 60);
    const tf = document.getElementById("timeFocused");
    const cp = document.getElementById("completePct");
    const cb = document.getElementById("completeBar");
    const fb = document.getElementById("focusBar");
    if(tf) tf.textContent = `${focused}h`;
    const completed = state.missions.filter(m=>m.status==="done").length;
    const pct = Math.round((completed / Math.max(1, state.missions.length))*100);
    if(cp) cp.textContent = pct+"%";
    if(cb) cb.style.width = pct + "%";
    if(fb) fb.style.width = Math.min(100, (focused*12)) + "%";
  }

  // INITIAL RENDERS
  renderToday(); renderMissionsList(); renderNotes(); renderTodayPlan(); updateAnalytics();

  // Fetch tasks from backend for the logged user and merge into state
  (async function fetchRemoteTasks(){
    try{
      let userId = 'me';
      try{
        const meResp = await fetch('/api/me', { credentials: 'same-origin' });
        if(meResp && meResp.ok){
          const meJson = await meResp.json().catch(()=>({}));
          if(meJson && meJson.user){
            userId = meJson.user.email || 'me';
            try{
              const avatar = document.querySelector('.sidebar .profile .avatar');
              const nameEl = document.querySelector('.sidebar .profile .name');
              const mutedEl = document.querySelector('.sidebar .profile .muted');
              if(nameEl) nameEl.textContent = meJson.user.name || meJson.user.email || nameEl.textContent;
              if(avatar && meJson.user.avatar) avatar.src = meJson.user.avatar;
              if(mutedEl) mutedEl.textContent = 'Member • Logged in';
            }catch(e){}
            try{ localStorage.setItem('user', userId); }catch(_){}
          }
        }
      }catch(err){ console.warn('could not fetch /api/me', err); }

      const r = await fetch('/api/tasks?user=' + encodeURIComponent(userId), { credentials: 'same-origin' });
      if(!r.ok) return;
      const j = await r.json();
      if(!j.tasks || !Array.isArray(j.tasks)) return;
      const existingById = new Map(state.missions.map(m => [String(m.id), m]));
      j.tasks.forEach(t=>{
        const sid = String(t.id || '');
        if(sid && existingById.has(sid)){
          const ex = existingById.get(sid);
          ex.title = t.title; ex.hours = t.hours||ex.hours; ex.priority = t.priority||ex.priority; ex.status = t.status||ex.status;
        } else {
          const duplicate = state.missions.find(m => (m.title === t.title && Number(m.hours || 0) === Number(t.hours || 0)));
          if(!duplicate) state.missions.push({id:t.id||Date.now(), title:t.title, hours:t.hours||1, priority:t.priority||'medium', status:t.status||'pending'});
        }
      });
      renderMissionsList(); renderToday(); renderTodayPlan(); updateAnalytics();
    }catch(err){ console.warn('failed to fetch remote tasks', err); }
  })();

  // Helper: create a task on server (used by chat quick-paths)
  async function createTaskOnServer(task){
    try{
      const resp = await fetch('/api/tasks', {method:'POST', headers:{'Content-Type':'application/json'}, credentials:'same-origin', body: JSON.stringify(task)});
      const j = await resp.json();
      if(resp.ok && j.task){
        return j.task;
      }
      return null;
    }catch(e){ return null; }
  }

  // Helper: list tasks from server (used by chat quick-paths)
  async function listTasksFromServer(){
    try{
      const r = await fetch('/api/tasks?user=me', {credentials:'same-origin'});
      if(!r.ok) return [];
      const j = await r.json();
      return j.tasks || [];
    }catch(e){ return []; }
  }

  // Default: show only the Today's Snapshot card on initial dashboard load
  (function ensureTodayOnlyView(){
    const grid = document.querySelector('#view-dashboard .grid');
    if(grid){
      grid.classList.add('show-today-only');
      document.querySelectorAll('.view').forEach(v=>v.classList.remove('active'));
      const dv = document.getElementById('view-dashboard');
      if(dv) dv.classList.add('active');
      document.querySelectorAll('.menu-item').forEach(m=>m.classList.remove('active'));
      const dashBtn = document.querySelector('.menu-item[data-view="dashboard"]');
      if(dashBtn) dashBtn.classList.add('active');
    }
  })();

  // --- TIMER (Pomodoro-like) ---
  let timer = {remaining:25*60, running:false, interval:null};
  const timerDisplay = document.getElementById("timerDisplay");
  const bigTimer = document.getElementById("bigTimer");

  function formatTime(sec){ const m = Math.floor(sec/60); const s = sec%60; return `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`; }

  function tick(){
    if(timer.running && timer.remaining>0){
      timer.remaining--;
      if(timerDisplay) timerDisplay.textContent = formatTime(timer.remaining);
      if(bigTimer) bigTimer.textContent = formatTime(timer.remaining);
      if(timer.remaining % 60 === 0) { state.focusedMinutes++; updateAnalytics(); }
      if(timer.remaining===0){ timer.running=false; clearInterval(timer.interval); state.sessions++; const sc = document.getElementById("sessionCount"); if(sc) sc.textContent = state.sessions; alert("Session complete — great work!"); }
    }
  }
  document.getElementById("startTimer")?.addEventListener("click", ()=>{ if(!timer.running){ timer.running=true; timer.interval = setInterval(tick,1000); }});
  document.getElementById("pauseTimer")?.addEventListener("click", ()=>{ timer.running=false; clearInterval(timer.interval); });
  document.getElementById("resetTimer")?.addEventListener("click", ()=>{ timer.running=false; clearInterval(timer.interval); timer.remaining = 25*60; if(timerDisplay) timerDisplay.textContent=formatTime(timer.remaining); if(bigTimer) bigTimer.textContent=formatTime(timer.remaining); });

  // big controls
  document.getElementById("bigStart")?.addEventListener("click", ()=>document.getElementById("startTimer")?.click());
  document.getElementById("bigPause")?.addEventListener("click", ()=>document.getElementById("pauseTimer")?.click());
  document.getElementById("bigReset")?.addEventListener("click", ()=>document.getElementById("resetTimer")?.click());

  // Focus quick start — robust view switch then start
  document.getElementById("startFocusBtn")?.addEventListener("click", ()=>{
    try{
      const viewBtn = document.querySelector('[data-view="focus"]');
      if(viewBtn) viewBtn.click();
      // wait briefly for view switch/animations then start the timer
      setTimeout(()=>{
        const startBtn = document.getElementById('startTimer');
        if(startBtn) startBtn.click();
        else { const bigStart = document.getElementById('bigStart'); if(bigStart) bigStart.click(); }
      }, 180);
    }catch(e){ console.warn('startFocusBtn handler failed', e); }
  });

  // Add to calendar placeholder (calls your backend)
  document.getElementById("addPlanToCalendar")?.addEventListener("click", async (ev)=>{
    ev.preventDefault();
    try{
      await connectAndSyncCalendar({quiet:false});
    }catch(e){ showErrorOverlay('Calendar sync failed: ' + (e && e.message)); }
  });

  window.addPlanToCalendarSample = (title) => {
    try{
      const now = new Date();
      // event starts in 1 hour, default duration 1 hour
      const start = new Date(now.getTime() + 60*60*1000);
      const end = new Date(start.getTime() + 60*60*1000);
      const payload = {
        summary: title,
        description: 'Created from ChronoKen',
        start: start.toISOString(),
        end: end.toISOString()
      };
      fetch('/api/calendar/add-event', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify(payload)
      }).then(async (r)=>{
        const j = await r.json().catch(()=>({}));
        if(r.ok && j.ok){ alert('Event added to calendar'); }
        else { alert('Failed to add event: ' + (j.error || JSON.stringify(j))); }
      }).catch(e=>{ alert('Network error adding event: ' + e.message); });
    }catch(e){ alert('Error creating calendar event: ' + e.message); }
  }

  // CREATE quick new mission floating
  document.getElementById("addTaskFloating")?.addEventListener("click", ()=>{ document.querySelector('[data-view="missions"]')?.click(); document.getElementById("newTaskTitle")?.focus(); });

  // Chat (Summon Ken) modal wiring
  document.getElementById("openSummon")?.addEventListener("click", ()=> openSummonModal());

  // Sidebar logout/profile wiring
  const logoutBtn = document.getElementById('logoutBtn');
  const profileBtn = document.getElementById('profileBtn');
  if(logoutBtn){
    logoutBtn.addEventListener('click', async ()=>{
      try{
        await fetch('/api/logout', { method: 'POST', credentials: 'same-origin' });
      }catch(e){ console.warn('logout failed', e); }
      window.location.href = 'login.html';
    });
  }
  if(profileBtn){
    profileBtn.addEventListener('click', async ()=>{
      const modal = document.getElementById('profile-modal');
      const preview = document.getElementById('profile-preview');
      const nameEl = document.getElementById('profile-name');
      const mutedEl = document.querySelector('.sidebar .profile .muted');
      const fileInput = document.getElementById('profile-file');
      if(!modal) return window.location.href = 'login.html';
      try{
        const meResp = await fetch('/api/me', { credentials: 'same-origin' });
        if(meResp && meResp.ok){
          const me = await meResp.json().catch(()=>({}));
          if(me && me.user){
            if(nameEl) nameEl.textContent = me.user.name || me.user.email;
            if(preview && me.user.avatar) preview.src = me.user.avatar;
            if(mutedEl) mutedEl.textContent = 'Member • Logged in';
          }
        }
      }catch(e){}
      if(fileInput) fileInput.value = null;
      modal.style.display = 'block';
      modal.setAttribute('aria-hidden','false');
    });
  }
  // profile modal handlers
  const profileModal = document.getElementById('profile-modal');
  const profileClose = document.getElementById('profile-close');
  const profileCancel = document.getElementById('profile-cancel');
  const profileSave = document.getElementById('profile-save');
  const profileFile = document.getElementById('profile-file');
  const profilePreview = document.getElementById('profile-preview');
  profileClose?.addEventListener('click', ()=>{ if(profileModal){ profileModal.style.display='none'; profileModal.setAttribute('aria-hidden','true'); } });
  profileCancel?.addEventListener('click', ()=>{ if(profileModal){ profileModal.style.display='none'; profileModal.setAttribute('aria-hidden','true'); } });
  profileFile?.addEventListener('change', (ev)=>{
    const f = ev.target.files && ev.target.files[0];
    if(!f) return;
    const url = URL.createObjectURL(f);
    if(profilePreview) profilePreview.src = url;
  });
  profileSave?.addEventListener('click', async ()=>{
    const f = profileFile.files && profileFile.files[0];
    if(!f) return alert('Please choose an image to upload');
    const fd = new FormData(); fd.append('avatar', f);
    try{
      profileSave.disabled = true;
      const r = await fetch('/api/avatar', { method: 'POST', body: fd, credentials: 'same-origin' });
      const j = await r.json();
      if(!r.ok){ alert('Upload failed: ' + (j.error||JSON.stringify(j))); profileSave.disabled = false; return; }
      try{ const avatarImg = document.querySelector('.sidebar .profile .avatar'); if(avatarImg && j.user && j.user.avatar) avatarImg.src = j.user.avatar; }catch(e){}
      if(profileModal){ profileModal.style.display='none'; profileModal.setAttribute('aria-hidden','true'); }
    }catch(e){ alert('Upload error: ' + e.message); }
    finally{ profileSave.disabled = false; }
  });

  const summonModal = document.getElementById('summon-modal');
  const summonClose = document.getElementById('summon-close');
  const summonSend = document.getElementById('summon-send');
  const summonInput = document.getElementById('summon-chat-input');

  // Spinner / elapsed status elements for Summon modal
  const summonStatus = document.getElementById('summon-status');
  const summonElapsedEl = document.getElementById('summon-elapsed');
  const summonSpinnerEl = document.getElementById('summon-spinner');
  let _spinnerInterval = null;
  let _spinnerStart = null;
  function startSpinner(){
    if(!summonStatus) return;
    summonStatus.classList.add('active');
    summonStatus.setAttribute('aria-hidden','false');
    _spinnerStart = Date.now();
    if(summonElapsedEl) summonElapsedEl.textContent = '0s';
    clearInterval(_spinnerInterval);
    _spinnerInterval = setInterval(()=>{ if(!summonElapsedEl || !_spinnerStart) return; const s = Math.floor((Date.now()-_spinnerStart)/1000); summonElapsedEl.textContent = s + 's'; }, 500);
  }
  function stopSpinner(){
    if(!summonStatus) return;
    summonStatus.classList.remove('active');
    summonStatus.setAttribute('aria-hidden','true');
    clearInterval(_spinnerInterval); _spinnerInterval = null; _spinnerStart = null;
    if(summonElapsedEl) summonElapsedEl.textContent = '';
  }

  function openSummonModal(){
    if(summonModal){
      summonModal.classList.add('open');
      summonModal.setAttribute('aria-hidden','false');
      setTimeout(()=>summonInput?.focus(), 150);
      const cw = getActiveChatWindow();
      if(cw && cw.children.length===0){
        appendChatBubble('ken', "Hello! I'm Ken, your AI agent. How can I assist you today?");
      }
    }
  }

  function closeSummonModal(){
    if(summonModal){
      summonModal.classList.remove('open');
      summonModal.setAttribute('aria-hidden','true');
    }
  }

  summonClose?.addEventListener('click', closeSummonModal);
  document.querySelector('.summon-overlay')?.addEventListener('click', closeSummonModal);

  // Helper: determine active chat container (modal preferred)
  function getActiveChatWindow(){
    const modal = document.getElementById('summon-modal');
    if(modal && modal.classList.contains('open')){
      return document.getElementById('summon-chat-window');
    }
    return document.getElementById('chatWindow');
  }

  // Helper: push assistant or user chat bubbles into the chat window
  function appendChatBubble(who='ken', html){
    const cw = getActiveChatWindow();
    if(!cw) return null;
    const div = document.createElement('div');
    div.className = 'chat-msg ' + (who==='user'?'user':'ken');
    div.innerHTML = typeof html === 'string' ? html.replace(/\n/g,'<br>') : html;
    cw.appendChild(div);
    cw.scrollTop = cw.scrollHeight;
    return div;
  }

  async function generateTimetable(daily_hours=3, num_days=7){
    appendChatBubble('ken', 'Generating timetable for next ' + num_days + ' days...');
    startSpinner();
    try{
      const resp = await fetch('/api/generate_timetable', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({daily_hours, num_days})
      });
      const data = await resp.json();
      if(!data.ok){
        appendChatBubble('ken', 'Failed to generate timetable: ' + (data.error||JSON.stringify(data)));
        stopSpinner();
        return;
      }
      const plan = data.plan || {};
      let out = '<strong>Generated Timetable:</strong><br/>';
      for(const [date, slots] of Object.entries(plan)){
        out += `<div style="margin-top:8px"><strong>${escapeHtml(date)}</strong><ul style="margin:6px 0 0 18px;padding:0">`;
        if(!slots || slots.length===0){ out += '<li>No tasks scheduled</li>'; }
        else {
          for(const s of slots){ out += `<li>${escapeHtml(s.title)} — ${s.hours}h</li>`; }
        }
        out += '</ul></div>';
      }
      appendChatBubble('ken', out);
      stopSpinner();
    } catch(e){
      appendChatBubble('ken', 'Error generating timetable: ' + e.message);
      stopSpinner();
    }
  }

  // Replace simulated chat with a WebSocket-backed chat (falls back to POST)
  let wsChat = null;
  const API_BASE = (window.__API_BASE__ && String(window.__API_BASE__).trim()) || (location.protocol + '//' + location.host) || 'http://127.0.0.1:8000';

  function ensureWs(){
    const timeoutMs = 4000;
    if(wsChat && wsChat.readyState === WebSocket.OPEN) return Promise.resolve(wsChat);
    return new Promise((resolve, reject)=>{
      try{
        const base = API_BASE;
        const wsScheme = base.startsWith('https') ? 'wss://' : (base.startsWith('http') ? 'ws://' : (location.protocol === 'https:' ? 'wss://' : 'ws://'));
        const hostPart = base.replace(/^https?:\/\//, '');
        wsChat = new WebSocket(wsScheme + hostPart + '/ws/chat');
      }catch(e){ wsChat = null; return reject(e); }
      let settled = false;
      const onOpen = ()=>{ if(settled) return; settled = true; cleanup(); resolve(wsChat); };
      const onError = (ev)=>{ if(settled) return; settled = true; cleanup(); wsChat = null; reject(new Error('ws error')); };
      const onClose = ()=>{ if(settled) return; settled = true; cleanup(); wsChat = null; reject(new Error('ws closed')); };
      const timer = setTimeout(()=>{ if(settled) return; settled = true; cleanup(); try{ wsChat.close(); }catch(_){} wsChat = null; console.warn('ensureWs: timeout'); reject(new Error('ws timeout')); }, timeoutMs);
      function cleanup(){ clearTimeout(timer); try{ wsChat.removeEventListener('open', onOpen); }catch{} try{ wsChat.removeEventListener('error', onError); }catch{} try{ wsChat.removeEventListener('close', onClose); }catch{} }
      wsChat.addEventListener('open', onOpen);
      wsChat.addEventListener('error', onError);
      wsChat.addEventListener('close', onClose);
    });
  }

  // Send helper used by modal and inline chat
  async function sendMessage(text){
    if(!text || !text.trim()) return;
    appendChatBubble('user', escapeHtml(text));
    const low = text.trim().toLowerCase();
    const createMatch = text.match(/^\s*create task\s*[:\-]?\s*(.*)/i);
    if(createMatch){
      const payloadStr = createMatch[1].trim();
      const parsed = {};
      const kvs = payloadStr.split(/,|;/).map(s=>s.trim()).filter(Boolean);
      kvs.forEach(item=>{
        const m = item.match(/^([a-zA-Z_\- ]+)=(.*)$/);
        if(m){ parsed[m[1].trim().toLowerCase().replace(/\s+/g,'_')] = m[2].trim(); }
      });
      if(!Object.keys(parsed).length && payloadStr){ parsed.title = payloadStr; }
      const taskObj = { title: parsed.title || 'Untitled', hours: parseFloat(parsed.hours) || 1, priority: parsed.priority || 'medium' };
      const tmp = { id: 'tmp-' + Date.now(), title: taskObj.title, hours: taskObj.hours, priority: taskObj.priority, status: 'pending' };
      state.missions.unshift(tmp); renderMissionsList(); renderToday(); updateAnalytics();
      const saved = await createTaskOnServer(taskObj);
      if(saved){
        const idx = state.missions.findIndex(m=>m.id===tmp.id);
        if(idx!==-1) state.missions[idx] = saved; else state.missions.unshift(saved);
        renderMissionsList(); renderToday(); updateAnalytics();
        appendChatBubble('ken', `Task created: <strong>${escapeHtml(saved.title)}</strong> (${saved.hours}h)`);
        return;
      } else {
        state.missions = state.missions.filter(m=>m.id!==tmp.id);
        renderMissionsList(); renderToday(); updateAnalytics();
        appendChatBubble('ken', `<em>Failed to create task. Please try again.</em>`);
        return;
      }
    }
    if(/^list tasks|^list my tasks|^show tasks/.test(low)){
      const tasks = await listTasksFromServer();
      tasks.forEach(t=>{ if(!state.missions.find(m=>String(m.id)===String(t.id))) state.missions.push({id:t.id,title:t.title,hours:t.hours||1,priority:t.priority||'medium',status:t.status||'pending'}); });
      renderMissionsList(); renderToday(); updateAnalytics();
      if(tasks.length===0) appendChatBubble('ken', 'You have no tasks yet.');
      else {
        const out = tasks.map(t=>`• ${escapeHtml(t.title)} — ${t.hours || 1}h`).join('<br>');
        appendChatBubble('ken', `<strong>Your tasks:</strong><br>${out}`);
      }
      return;
    }

    const assistantEl = appendChatBubble('ken', '<span class="typing-dots"><span></span><span></span><span></span></span>');
    assistantEl.classList.add('typing');
    startSpinner();
    let partial = '';
    try{
      const ws = await ensureWs();
      const onMessage = (ev)=>{
        try{
          const d = JSON.parse(ev.data);
          if(d.partial){
            partial += d.partial;
            assistantEl.classList.remove('typing');
            assistantEl.innerHTML = escapeHtml(partial).replace(/\n/g,'<br>');
            const cw = getActiveChatWindow(); if(cw) cw.scrollTop = cw.scrollHeight;
          }
          if(d.reply){
            assistantEl.classList.remove('typing');
            assistantEl.innerHTML = escapeHtml(d.reply).replace(/\n/g,'<br>');
            stopSpinner();
            ws.removeEventListener('message', onMessage);
          }
          if(d.error){
            assistantEl.classList.remove('typing');
            assistantEl.innerHTML = '<em>Error: '+escapeHtml(d.error||'unknown')+'</em>';
            stopSpinner();
            ws.removeEventListener('message', onMessage);
          }
        }catch(err){ console.warn('ws parse err', err, ev.data); }
      };
      ws.addEventListener('message', onMessage);
      ws.send(JSON.stringify({message: text}));
    }catch(err){
      try{
        const r = await fetch(API_BASE + '/api/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({message: text})});
        const data = await r.json();
        assistantEl.classList.remove('typing');
        if(data.reply) assistantEl.innerHTML = escapeHtml(data.reply).replace(/\n/g,'<br>');
        else assistantEl.innerHTML = '<em>No reply</em>';
        stopSpinner();
      }catch(e2){ assistantEl.innerHTML = '<em>Failed to send message</em>'; stopSpinner(); }
    }
  }

  // Generate plan helpers: prompt user for simple params then send a 'generate plan' quick-path
  function promptAndGenerate(defaultHours=2, defaultDays=3){
    try{
      const dh = window.prompt('Daily hours to allocate for planning?', String(defaultHours));
      if(dh === null) return;
      const nd = window.prompt('Number of days to plan for?', String(defaultDays));
      if(nd === null) return;
      const daily = parseFloat(dh) || defaultHours;
      const days = parseInt(nd) || defaultDays;
      const msg = `generate plan daily_hours=${daily} num_days=${days}`;
      sendMessage(msg);
    }catch(e){ alert('Could not create plan: ' + e.message); }
  }

  document.getElementById('summon-generate-plan')?.addEventListener('click', ()=> promptAndGenerate(3,7));
  document.getElementById('inline-generate-plan')?.addEventListener('click', ()=> promptAndGenerate(2,3));

  // wire existing inline chat (if present)
  const inlineSendBtn = document.getElementById('sendChat');
  if(inlineSendBtn){
    inlineSendBtn.addEventListener('click', ()=>{
      const i = document.getElementById('chatText');
      if(i) sendMessage(i.value.trim());
      if(i) i.value = '';
    });
  }

  // wire modal send
  summonSend?.addEventListener('click', ()=>{ const val = summonInput?.value || ''; if(val.trim()){ sendMessage(val.trim()); summonInput.value = ''; } });

  // Theme toggle (very basic)
  document.getElementById("themeBtn")?.addEventListener("click", ()=>{
    const html = document.documentElement;
    const cur = html.getAttribute("data-theme") || 'dark';
    html.setAttribute("data-theme", cur==='dark'?'light':'dark');
  });

  // --- GLOBAL SEARCH SUGGESTIONS ---
  // Create a simple suggestion popup for the global search box that matches mission titles
  const globalSearch = document.getElementById('globalSearch');
  let searchPopup = null;
  function ensureSearchPopup(){
    if(searchPopup) return searchPopup;
    searchPopup = document.createElement('div');
    searchPopup.id = 'search-suggestions';
    Object.assign(searchPopup.style, {position:'absolute',zIndex:1200,background:'#0b1220',color:'#fff',borderRadius:'6px',boxShadow:'0 8px 30px rgba(0,0,0,0.6)',padding:'6px',minWidth:'200px',display:'none',maxHeight:'220px',overflow:'auto'});
    document.body.appendChild(searchPopup);
    return searchPopup;
  }

  function positionSearchPopup(){
    if(!globalSearch) return;
    const rect = globalSearch.getBoundingClientRect();
    const sp = ensureSearchPopup();
    sp.style.left = (rect.left + window.scrollX) + 'px';
    sp.style.top = (rect.bottom + window.scrollY + 6) + 'px';
    sp.style.minWidth = Math.max(200, rect.width) + 'px';
  }

  function showSearchSuggestions(q){
    const sp = ensureSearchPopup();
    sp.innerHTML = '';
    if(!q || q.trim().length < 1){ sp.style.display='none'; return; }
    const term = q.trim().toLowerCase();
    const matches = state.missions.filter(m => (m.title||'').toLowerCase().includes(term)).slice(0,8);
    if(matches.length === 0){ sp.style.display='none'; return; }
    matches.forEach(m=>{
      const r = document.createElement('div');
      r.className = 'search-suggestion';
      r.textContent = m.title;
      Object.assign(r.style,{padding:'8px',cursor:'pointer',borderRadius:'4px'});
      r.addEventListener('click', ()=>{
        try{ globalSearch.value = m.title; sp.style.display='none'; }
        catch(e){}
      });
      r.addEventListener('mouseenter', ()=>{ r.style.background = 'rgba(255,255,255,0.04)'; });
      r.addEventListener('mouseleave', ()=>{ r.style.background = 'transparent'; });
      sp.appendChild(r);
    });
    positionSearchPopup();
    sp.style.display = 'block';
  }

  if(globalSearch){
    globalSearch.addEventListener('input', (e)=>{ try{ showSearchSuggestions(e.target.value); }catch(e){} });
    globalSearch.addEventListener('focus', (e)=>{ try{ positionSearchPopup(); showSearchSuggestions(e.target.value||''); }catch(e){} });
    globalSearch.addEventListener('blur', (e)=>{ setTimeout(()=>{ try{ const sp = ensureSearchPopup(); sp.style.display='none'; }catch(e){} }, 180); });
    window.addEventListener('resize', ()=>{ try{ positionSearchPopup(); }catch(e){} });
  }

  // Calendar sync btn sample
  document.getElementById("calendarSync")?.addEventListener("click", async (ev)=>{
    ev.preventDefault();
    try{
      await connectAndSyncCalendar({quiet:false});
    }catch(e){ showErrorOverlay('Calendar connect failed: ' + (e && e.message)); }
  });

  // === NEW: startCalendarOauth (convenience) ===
  async function startCalendarOauth() {
    try {
      const res = await fetch('/api/calendar/oauth_start', { credentials: 'include' });
      const data = await res.json().catch(()=>({}));
      console.log('[ChronoKen] oauth_start response', data);
      if(res.ok && data.auth_url){
        window.location.href = data.auth_url;
      } else {
        alert('Failed to start OAuth: ' + (data.error || JSON.stringify(data)));
      }
    } catch(err){
      alert('Network error starting OAuth: ' + err.message);
    }
  }

  // === REPLACED: connectAndSyncCalendar (improved) ===
  async function connectAndSyncCalendar(opts={quiet:true}) {
    const quiet = !!opts.quiet;
    const btn = document.getElementById('calendarSync');
    try {
      if(btn) { btn.disabled = true; btn.textContent = 'Connecting...'; }

      const r = await fetch('/api/calendar/oauth_start', { credentials: 'same-origin' });
      if(!r.ok){
        const j = await r.json().catch(()=>({}));
        throw new Error(j.error || 'Failed to start OAuth');
      }
      const j = await r.json();
      const authUrl = j.auth_url;
      if(!authUrl) throw new Error('No auth_url returned');

      // DEBUG: print the url so you can inspect client_id/redirect_uri in console
      console.log('[ChronoKen] OAuth auth_url returned:', authUrl);

      // open popup; if blocked fallback to same-window redirect
      const popup = window.open(authUrl, 'chrono_calendar_oauth', 'width=700,height=700');
      if(!popup || popup.closed || typeof popup.closed === 'undefined'){
        console.warn('[ChronoKen] Popup blocked — falling back to same-window redirect.');
        try{ sessionStorage.setItem('oauth_fallback','same-window'); }catch(_){}
        window.location.href = authUrl;
        return;
      }

      // poll for popup close
      await new Promise((resolve, reject) => {
        const t0 = Date.now();
        const timer = setInterval(() => {
          try {
            if (popup.closed) { clearInterval(timer); resolve(); return; }
            if (Date.now() - t0 > 1000*60*5) { clearInterval(timer); try{ popup.close(); }catch(_){} reject(new Error('OAuth timed out')); }
          } catch(e) { /* cross-origin while open — ignore */ }
        }, 500);
      });

      // after popup closed, call sync endpoint
      if(btn) btn.textContent = 'Syncing...';
      const syncResp = await fetch('/api/calendar/sync-today', { method: 'POST', credentials: 'same-origin' });
      const syncJson = await syncResp.json().catch(()=>({}));
      if(!syncResp.ok){ throw new Error(syncJson.error || JSON.stringify(syncJson)); }
      const created = syncJson.created || 0;
      if(!quiet) alert('Calendar sync complete — created ' + created + ' events.');
      return syncJson;

    } finally {
      if(btn) { btn.disabled = false; btn.textContent = 'Sync Calendar'; }
    }
  }

  // filtering & extra render
  document.getElementById("filterSearch")?.addEventListener("input", (e)=>{
    const q = e.target.value.toLowerCase();
    const out = document.getElementById("allMissions");
    if(!out) return;
    out.innerHTML = "";
    state.missions.filter(m=>m.title.toLowerCase().includes(q)).forEach(m=>{
      const li = document.createElement("li");
      li.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center"><div><strong>${escapeHtml(m.title)}</strong><div class="muted">${m.priority} • ${m.status}</div></div></div>`;
      out.appendChild(li);
    });
  });

}); // end DOMContentLoaded
