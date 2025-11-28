// Homepage interactive behaviors + 3D tilt effect
document.addEventListener("DOMContentLoaded", () => {
  // theme toggle
  const themeToggle = document.getElementById("themeToggle");
  const html = document.documentElement;
  const stored = localStorage.getItem("ssc-theme");
  if (stored) {
    html.setAttribute("data-theme", stored);
    themeToggle.checked = stored === "dark";
  } else {
    // default dark
    html.setAttribute("data-theme", "dark");
    themeToggle.checked = true;
  }
  themeToggle.addEventListener("change", () => {
    const theme = themeToggle.checked ? "dark" : "light";
    html.setAttribute("data-theme", theme);
    localStorage.setItem("ssc-theme", theme);
  });

  // set year
  document.getElementById("year").textContent = new Date().getFullYear();

  // contact form (demo behavior)
  const contactForm = document.getElementById("contactForm");
  const contactResult = document.getElementById("contactResult");
  contactForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const name = document.getElementById("contactName").value.trim();
    const email = document.getElementById("contactEmail").value.trim();
    const message = document.getElementById("contactMessage").value.trim();
    contactResult.textContent = "Sending...";

    // Simulate sending (replace with real API call)
    setTimeout(() => {
      contactResult.textContent = `Thanks ${name}! Your message has been received. We'll contact you at ${email}.`;
      contactForm.reset();
    }, 900);
  });

  // copy email button
  const copyEmailBtn = document.getElementById("copyEmail");
  copyEmailBtn.addEventListener("click", () => {
    const email = document.getElementById("leadEmail").textContent;
    navigator.clipboard.writeText(email).then(() => {
      copyEmailBtn.textContent = "Copied!";
      setTimeout(() => (copyEmailBtn.textContent = "Copy Email"), 1500);
    });
  });

  // demo buttons
  document.getElementById("tryBtn").addEventListener("click", () => {
    alert("Demo: Launching the agent UI (connect to your app backend).");
  });
  document.getElementById("demoBtn").addEventListener("click", () => {
    alert("Demo requested — you will be contacted via the address in the Contact form.");
  });
  document.getElementById("launchBtn").addEventListener("click", () => {
    alert("Launching agent... (wire to your app's /app or /dashboard route).");
  });
  document.getElementById("addToCalendarBtn").addEventListener("click", () => {
    alert("This will trigger 'Add Today Plan to Google Calendar' (wire to your /api/calendar endpoint).");
  });

  // small floating motion for preview card is handled by CSS animation,
  // we add a 3D tilt on mouse move (Pinterest-like)
  const floatCards = document.querySelectorAll(".float-3d-wrapper .float-3d");
  floatCards.forEach(card => {
    const wrapper = card.parentElement;
    // smoothing parameters
    let currentX = 0, currentY = 0, targetX = 0, targetY = 0, rafId = null;

    function applyTransform() {
      // lerp for smoothness
      currentX += (targetX - currentX) * 0.12;
      currentY += (targetY - currentY) * 0.12;
      card.style.transform = `rotateX(${currentY}deg) rotateY(${currentX}deg) translateZ(12px)`;
      rafId = requestAnimationFrame(applyTransform);
    }

    wrapper.addEventListener("mousemove", (e) => {
      const rect = wrapper.getBoundingClientRect();
      const x = e.clientX - rect.left; 
      const y = e.clientY - rect.top;
      const cx = rect.width / 2;
      const cy = rect.height / 2;
      // sensitivity: smaller divisor = more tilt
      const rotateY = (x - cx) / 20; // rotateY
      const rotateX = -(y - cy) / 20; // rotateX
      targetX = rotateY;
      targetY = rotateX;
      if (!rafId) applyTransform();
    });

    wrapper.addEventListener("mouseleave", () => {
      targetX = 0;
      targetY = 0;
      // after smoothing, cancel raf
      setTimeout(() => {
        if (rafId) { cancelAnimationFrame(rafId); rafId = null; }
      }, 300);
    });

    // touch: small parallax on touchmove
    wrapper.addEventListener("touchmove", (ev) => {
      if (!ev.touches || !ev.touches.length) return;
      const t = ev.touches[0];
      const rect = wrapper.getBoundingClientRect();
      const x = t.clientX - rect.left;
      const y = t.clientY - rect.top;
      const cx = rect.width / 2;
      const cy = rect.height / 2;
      targetX = (x - cx) / 25;
      targetY = -(y - cy) / 25;
      if (!rafId) applyTransform();
    });

    wrapper.addEventListener("touchend", () => {
      targetX = 0;
      targetY = 0;
      setTimeout(() => {
        if (rafId) { cancelAnimationFrame(rafId); rafId = null; }
      }, 300);
    });
  });
});
