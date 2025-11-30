// Auth animations & interactions
document.addEventListener("DOMContentLoaded", () => {
  const card = document.getElementById("authCard");
  const showSignup = document.getElementById("showSignup");
  const showLogin = document.getElementById("showLogin");
  const hero = document.getElementById("heroImg");

  // toggle login/signup
  showSignup.addEventListener("click", () => card.setAttribute("data-state", "signup"));
  showLogin.addEventListener("click", () => card.setAttribute("data-state", "login"));

  // small tilt effect on hero (follow mouse)
  const wrapper = document.querySelector(".hero-3d-wrapper");
  if (wrapper && hero) {
    let raf = null, tx = 0, ty = 0, gx = 0, gy = 0;
    wrapper.addEventListener("mousemove", e => {
      const r = wrapper.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width - 0.5;
      const y = (e.clientY - r.top) / r.height - 0.5;
      tx = x * 12; ty = y * 10;
      if (!raf) animateHero();
    });
    wrapper.addEventListener("mouseleave", () => {
      tx = 0; ty = 0;
      if (!raf) animateHero();
    });
    function animateHero(){
      raf = requestAnimationFrame(() => {
        gx += (tx - gx) * 0.12;
        gy += (ty - gy) * 0.12;
        hero.style.transform = `rotateX(${ -gy }deg) rotateY(${ gx }deg) translateZ(10px)`;
        raf = null;
      });
    }
  }

  // simple demo handlers (replace with actual auth)
  document.getElementById("loginForm").addEventListener("submit", (e) => {
    e.preventDefault();
    // demo validation
    const email = document.getElementById("loginEmail").value;
    const pass = document.getElementById("loginPass").value;
    if (!email || !pass) return alert("Enter email and password");

    // basic email format check
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    let correctedEmail = email.trim();
    if (!emailPattern.test(correctedEmail)){
      // try to auto-correct common gmail typos in the domain
      try{
        const parts = correctedEmail.split('@');
        if(parts.length === 2){
          const local = parts[0];
          let domain = parts[1].toLowerCase();
          const commonTypos = {
            'gmi.com': 'gmail.com',
            'gmal.com': 'gmail.com',
            'gmial.com': 'gmail.com',
            'gmai.com': 'gmail.com',
            'gnail.com': 'gmail.com',
            'gmail.con': 'gmail.com'
          };
          if(commonTypos[domain]){
            correctedEmail = `${local}@${commonTypos[domain]}`;
            // reflect correction in the input field
            document.getElementById("loginEmail").value = correctedEmail;
          }
        }
      }catch(err){/* ignore */}
    }

    // re-validate after potential correction
    if (!emailPattern.test(correctedEmail)){
      return alert('Please enter a valid email address');
    }

    // simulate success: set demo logged-in flag
    try{ localStorage.setItem('loggedIn','true'); }catch(ex){}

    // send welcome email via backend (SendGrid) — fire-and-forget for demo
    try{
      fetch('/api/send_welcome', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({email: correctedEmail, name: ''})
      }).catch(()=>{});
    }catch(e){}

    alert(`Welcome back, ${correctedEmail}!\n(Replace with real authentication call.)`);
    // If there is a pending agent draft (Try Agent flow), return to the main page
    // otherwise go to the dashboard page after login
    try{
      const pending = sessionStorage.getItem('pendingTask');
      if(pending){
        window.location.href = 'index.html';
      } else {
        window.location.href = 'dashboard.html';
      }
    }catch(e){
      window.location.href = 'dashboard.html';
    }
  });

  document.getElementById("signupForm").addEventListener("submit", (e) => {
    e.preventDefault();
    const name = document.getElementById("signupName").value;
    const email = document.getElementById("signupEmail").value;
    const pass = document.getElementById("signupPass").value;
    if (!name || !email || !pass) return alert("Complete all fields");
    // simulate account creation: call welcome endpoint then switch to login
    try{
      fetch('/api/send_welcome', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({email: email, name: name})
      }).catch(()=>{});
    }catch(e){}
    alert("Account created! (Hook this to your backend to actually create user)");
    card.setAttribute("data-state", "login");
  });

  // small keyboard accessibility: Esc returns to login
  document.addEventListener("keydown", (ev)=>{
    if(ev.key === "Escape") card.setAttribute("data-state","login");
  });
});
