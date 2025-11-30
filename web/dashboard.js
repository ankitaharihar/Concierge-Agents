// ChronoKen dashboard script (interactive demo)
document.addEventListener("DOMContentLoaded", () => {
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

  // --- VIEW SWITCH ---
  const menuItems = document.querySelectorAll(".menu-item");
  const views = document.querySelectorAll(".view");
  menuItems.forEach(btn => {
    btn.addEventListener("click", () => {
      menuItems.forEach(m=>m.classList.remove("active"));
      btn.classList.add("active");
      const view = btn.dataset.view;
      // If the clicked view is 'summon', open the floating chat modal instead of navigating
      if(view === 'summon'){
        openSummonModal();
        return;
      }
      // If the clicked view corresponds to an internal dashboard panel, keep the dashboard
      // active and only apply the grid "focus" modifier so the user stays on the dashboard page.
      const dashboardPanelViews = ['dashboard','missions','timeslices','timeline','focus','scrolls','analytics'];
      views.forEach(v=>v.classList.remove("active"));
      if(dashboardPanelViews.includes(view)){
        document.getElementById('view-dashboard').classList.add('active');
      } else {
        document.getElementById("view-"+view).classList.add("active");
      }
      // Adjust dashboard-grid compact classes so the dashboard can remember a "focus" modifier
      const grid = document.querySelector('#view-dashboard .grid');
      if(grid){
        // remove any previous show-* modifiers
        grid.classList.remove('show-today-only','show-missions-only','show-timeline-only','show-focus-only','show-scrolls-only','show-analytics-only','show-summon-only');
        // apply modifier matching the clicked menu item so dashboard can focus that panel when relevant
        if(view === 'dashboard') grid.classList.add('show-today-only');
        if(view === 'missions') grid.classList.add('show-missions-only');
        if(view === 'timeslices' || view === 'timeline') grid.classList.add('show-timeline-only');
        if(view === 'focus') grid.classList.add('show-focus-only');
        if(view === 'scrolls') grid.classList.add('show-scrolls-only');
        if(view === 'analytics') grid.classList.add('show-analytics-only');
        // 'summon' navigates to the full chat view (handled by view activation above)
      }
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
    todayTasks.innerHTML = "";
    state.missions.filter(m => m.status !== "done").slice(0,5).forEach(m => {
      const li = document.createElement("li");
      li.innerHTML = `<div class="mission-meta"><strong>${m.title}</strong><span class="muted">${m.hours} hrs • ${m.priority}</span></div>
                      <div><button class="btn small" data-id="${m.id}" onclick="markInProgress(${m.id})">Start</button></div>`;
      todayTasks.appendChild(li);
    });
  }

  // expose helper for inline handler above
  window.markInProgress = (id) => {
    const f = state.missions.find(m=>m.id===id);
    if(f) { f.status="in_progress"; renderToday(); renderMissionsList(); }
  }

  function renderMissionsList() {
    const list = document.getElementById("missionsList");
    list.innerHTML = "";
    state.missions.forEach(m => {
      const li = document.createElement("li");
      li.innerHTML = `<div>
          <div style="display:flex;gap:10px;align-items:center">
            <strong>${m.title}</strong>
            <span class="${m.priority==='high'?'priority-high':m.priority==='medium'?'priority-medium':'priority-low'}" style="margin-left:8px">${m.priority}</span>
          </div>
          <div class="muted small">${m.hours} hrs • ${m.status}</div>
        </div>
        <div>
          <button class="btn small" onclick="completeMission(${m.id})">Done</button>
          <button class="btn ghost small" onclick="editMission(${m.id})">Edit</button>
        </div>`;
      list.appendChild(li);
    });
  }

  window.completeMission = (id) => {
    const m = state.missions.find(x=>x.id===id);
    if(m) m.status="done";
    renderToday(); renderMissionsList(); updateAnalytics();
  }
  window.editMission = (id) => {
    const m = state.missions.find(x=>x.id===id);
    if(!m) return alert("Not found");
    const newTitle = prompt("Edit title", m.title);
    if(newTitle) { m.title = newTitle; renderMissionsList(); renderToday(); }
  }

  // create mission
  document.getElementById("createTaskBtn").addEventListener("click", () => {
    const title = document.getElementById("newTaskTitle").value.trim();
    const priority = document.getElementById("newTaskPriority").value;
    const hours = parseFloat(document.getElementById("newTaskHours").value) || 1;
    if(!title) return alert("Enter a mission title");
    const id = Date.now();
    state.missions.push({id,title,hours,priority,status:"pending"});
    document.getElementById("newTaskTitle").value="";
    renderMissionsList(); renderToday(); updateAnalytics();
  });

  // Render all missions view
  function renderAllMissions(){
    const out = document.getElementById("allMissions");
    out.innerHTML = "";
    state.missions.forEach(m=>{
      const li = document.createElement("li");
      li.className="missions-list-item";
      li.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center">
        <div><strong>${m.title}</strong><div class="muted">${m.hours} hrs • ${m.priority} • ${m.status}</div></div>
        <div><button class="btn small" onclick="completeMission(${m.id})">Done</button></div>
      </div>`;
      out.appendChild(li);
    });
  }

  // NOTES
  document.getElementById("saveNote").addEventListener("click", ()=>{
    const t = document.getElementById("quickNote").value.trim();
    if(!t) return;
    state.notes.push({id:Date.now(),text:t});
    document.getElementById("quickNote").value="";
    renderNotes();
  });
  function renderNotes(){
    const out = document.getElementById("notesList");
    out.innerHTML="";
    state.notes.forEach(n=>{
      const li = document.createElement("li");
      li.innerHTML = `<div>${n.text}</div><div style="margin-top:6px"><button class="btn small" onclick="noteToMission(${n.id})">Convert to Mission</button></div>`;
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
    plans.innerHTML = "";
    // naive plan: schedule all pending tasks sequentially
    const pending = state.missions.filter(m=>m.status!=="done");
    pending.forEach((p, i)=>{
      const card = document.createElement("div");
      card.className="card";
      card.style.marginBottom="10px";
      card.innerHTML = `<div style="display:flex;justify-content:space-between"><strong>${p.title}</strong><span class="muted">${p.hours} hrs</span></div>
        <div class="muted small">Start: +${i*2}h • End: +${(i*2)+p.hours}h</div>
        <div style="margin-top:8px"><button class="btn small" onclick="addPlanToCalendarSample('${p.title}')">Add to Calendar</button></div>`;
      plans.appendChild(card);
    });
  }

  // Today plan UI
  function renderTodayPlan(){
    const el = document.getElementById("todayPlan");
    el.innerHTML="";
    const pending = state.missions.filter(m=>m.status!=="done").slice(0,4);
    pending.forEach(m=>{
      const div = document.createElement("div");
      div.className="plan-slot";
      div.innerHTML = `<strong>${m.title}</strong><div class="muted small">${m.hours} hrs • ${m.priority}</div>`;
      el.appendChild(div);
    });
  }

  // Analytics simple
  function updateAnalytics(){
    const focused = Math.round(state.focusedMinutes / 60);
    document.getElementById("timeFocused").textContent = `${focused}h`;
    const completed = state.missions.filter(m=>m.status==="done").length;
    const pct = Math.round((completed / Math.max(1, state.missions.length))*100);
    document.getElementById("completePct").textContent = pct+"%";
    document.getElementById("completeBar").style.width = pct + "%";
    document.getElementById("focusBar").style.width = Math.min(100, (focused*12)) + "%";
  }

  // INITIAL RENDERS
  renderToday(); renderMissionsList(); renderNotes(); renderTodayPlan(); updateAnalytics();

  // Default: show only the Today's Snapshot card on initial dashboard load
  (function ensureTodayOnlyView(){
    const grid = document.querySelector('#view-dashboard .grid');
    if(grid){
      grid.classList.add('show-today-only');
      // ensure the dashboard view is active
      document.querySelectorAll('.view').forEach(v=>v.classList.remove('active'));
      const dv = document.getElementById('view-dashboard');
      if(dv) dv.classList.add('active');
      // mark the sidebar dashboard item active
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
      timerDisplay.textContent = formatTime(timer.remaining);
      bigTimer.textContent = formatTime(timer.remaining);
      if(timer.remaining % 60 === 0) { state.focusedMinutes++; updateAnalytics(); }
      if(timer.remaining===0){ timer.running=false; clearInterval(timer.interval); state.sessions++; document.getElementById("sessionCount").textContent = state.sessions; alert("Session complete — great work!"); }
    }
  }
  document.getElementById("startTimer").addEventListener("click", ()=>{
    if(!timer.running){
      timer.running=true;
      timer.interval = setInterval(tick,1000);
    }
  });
  document.getElementById("pauseTimer").addEventListener("click", ()=>{
    timer.running=false; clearInterval(timer.interval);
  });
  document.getElementById("resetTimer").addEventListener("click", ()=>{
    timer.running=false; clearInterval(timer.interval); timer.remaining = 25*60; timerDisplay.textContent=formatTime(timer.remaining); bigTimer.textContent=formatTime(timer.remaining);
  });

  // big controls
  document.getElementById("bigStart").addEventListener("click", ()=>document.getElementById("startTimer").click());
  document.getElementById("bigPause").addEventListener("click", ()=>document.getElementById("pauseTimer").click());
  document.getElementById("bigReset").addEventListener("click", ()=>document.getElementById("resetTimer").click());

  // Focus quick start
  document.getElementById("startFocusBtn").addEventListener("click", ()=>{
    // switch to focus view and start
    document.querySelector('[data-view="focus"]').click();
    document.getElementById("bigStart").click();
  });

  // Add to calendar placeholder (calls your backend)
  document.getElementById("addPlanToCalendar").addEventListener("click", ()=>{
    alert("This will call /api/calendar/sync-today to push today's plan to Google Calendar (implement endpoint).");
    // Example: fetch('/api/calendar/sync-today').then(...)
  });

  window.addPlanToCalendarSample = (title) => {
    alert("Would add event: " + title + " → (Implement API call to /api/calendar/sync-today)");
  }

  // CREATE quick new mission floating
  document.getElementById("addTaskFloating").addEventListener("click", ()=>{
    document.querySelector('[data-view="missions"]').click();
    document.getElementById("newTaskTitle").focus();
  });

  // Chat (Summon Ken) modal wiring
  document.getElementById("openSummon").addEventListener("click", ()=> openSummonModal());

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
    _spinnerInterval = setInterval(()=>{
      if(!summonElapsedEl || !_spinnerStart) return;
      const s = Math.floor((Date.now()-_spinnerStart)/1000);
      summonElapsedEl.textContent = s + 's';
    }, 500);
  }
  function stopSpinner(){
    if(!summonStatus) return;
    summonStatus.classList.remove('active');
    summonStatus.setAttribute('aria-hidden','true');
    clearInterval(_spinnerInterval); _spinnerInterval = null; _spinnerStart = null;
    if(summonElapsedEl) summonElapsedEl.textContent = '';
  }

  function openSummonModal(){
    // open modal and focus input
    if(summonModal){
      summonModal.classList.add('open');
      summonModal.setAttribute('aria-hidden','false');
      setTimeout(()=>summonInput?.focus(), 150);
      // insert a greeting if chat empty
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
  // close on overlay click
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
      // Format the plan nicely
      let out = '<strong>Generated Timetable:</strong><br/>';
      for(const [date, slots] of Object.entries(plan)){
        out += `<div style="margin-top:8px"><strong>${date}</strong><ul style="margin:6px 0 0 18px;padding:0">`;
        if(!slots || slots.length===0){
          out += '<li>No tasks scheduled</li>';
        } else {
          for(const s of slots){
            out += `<li>${s.title} — ${s.hours}h</li>`;
          }
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
  // Determine API base (use explicit global override if set, otherwise use page origin)
  const API_BASE = (window.__API_BASE__ && String(window.__API_BASE__).trim()) || (location.protocol + '//' + location.host) || 'http://127.0.0.1:8000';

  // reuse appendChatBubble above

  function ensureWs(){
    // Return an open WebSocket or attempt to create one with a short timeout.
    // If the socket doesn't open within `timeoutMs` we reject so callers can
    // fall back to POST quickly instead of waiting indefinitely.
    const timeoutMs = 4000;
    if(wsChat && wsChat.readyState === WebSocket.OPEN) return Promise.resolve(wsChat);
    return new Promise((resolve, reject)=>{
      try{
        // prefer explicit API_BASE when available (handles file:// and mismatched origins)
        try{
          const base = API_BASE;
          const wsScheme = base.startsWith('https') ? 'wss://' : (base.startsWith('http') ? 'ws://' : (location.protocol === 'https:' ? 'wss://' : 'ws://'));
          // strip protocol from base to append host+path correctly
          const hostPart = base.replace(/^https?:\/\//, '');
          wsChat = new WebSocket(wsScheme + hostPart + '/ws/chat');
        }catch(e){ wsChat = null; return reject(e); }
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
    appendChatBubble('user', text);
    // placeholder for assistant
    const assistantEl = appendChatBubble('ken', '<em>Thinking...</em>');
    startSpinner();
    let partial = '';
    try{
      const ws = await ensureWs();
      const onMessage = (ev)=>{
        try{
          const d = JSON.parse(ev.data);
          if(d.partial){
            partial += d.partial;
            assistantEl.innerHTML = partial.replace(/\n/g,'<br>');
            const cw = getActiveChatWindow(); if(cw) cw.scrollTop = cw.scrollHeight;
          }
          if(d.reply){
            assistantEl.innerHTML = d.reply.replace(/\n/g,'<br>');
            stopSpinner();
            ws.removeEventListener('message', onMessage);
          }
          if(d.error){
            assistantEl.innerHTML = '<em>Error: '+(d.error||'unknown')+'</em>';
            stopSpinner();
            ws.removeEventListener('message', onMessage);
          }
        }catch(err){ console.warn('ws parse err', err, ev.data); }
      };
      ws.addEventListener('message', onMessage);
      ws.send(JSON.stringify({message: text}));
    }catch(err){
      // fallback to POST
      try{
        const r = await fetch(API_BASE + '/api/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({message: text})});
        const data = await r.json();
        if(data.reply) assistantEl.innerHTML = data.reply.replace(/\n/g,'<br>');
        else assistantEl.innerHTML = '<em>No reply</em>';
        stopSpinner();
      }catch(e2){ assistantEl.innerHTML = '<em>Failed to send message</em>'; stopSpinner(); }
    }
  }

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
  summonSend?.addEventListener('click', ()=>{
    const val = summonInput?.value || '';
    if(val.trim()){ sendMessage(val.trim()); summonInput.value = ''; }
  });

  // Theme toggle (very basic)
  document.getElementById("themeBtn").addEventListener("click", ()=>{
    const html = document.documentElement;
    const cur = html.getAttribute("data-theme") || 'dark';
    html.setAttribute("data-theme", cur==='dark'?'light':'dark');
  });

  // Calendar sync btn sample
  document.getElementById("calendarSync").addEventListener("click", ()=>{
    alert("Calendar sync: implement OAuth & /api/calendar/sync-today backend as shown in previous instructions.");
  });

  // filtering & extra render
  document.getElementById("filterSearch")?.addEventListener("input", (e)=>{
    const q = e.target.value.toLowerCase();
    const out = document.getElementById("allMissions");
    out.innerHTML = "";
    state.missions.filter(m=>m.title.toLowerCase().includes(q)).forEach(m=>{
      const li = document.createElement("li");
      li.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center"><div><strong>${m.title}</strong><div class="muted">${m.priority} • ${m.status}</div></div></div>`;
      out.appendChild(li);
    });
  });

});
