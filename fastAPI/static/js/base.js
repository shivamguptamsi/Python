/* NeuronIQ — base.js */

// ── NAV SCROLL EFFECT ──
const nav = document.getElementById('mainNav');
if (nav) {
  window.addEventListener('scroll', () => {
    nav.classList.toggle('scrolled', window.scrollY > 40);
  }, { passive: true });
}

// ── HAMBURGER / MOBILE DRAWER ──
const hamburger    = document.getElementById('hamburger');
const mobileDrawer = document.getElementById('mobileDrawer');
const drawerOverlay= document.getElementById('drawerOverlay');

function openDrawer() {
  hamburger?.classList.add('open');
  mobileDrawer?.classList.add('open');
  drawerOverlay?.classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeDrawer() {
  hamburger?.classList.remove('open');
  mobileDrawer?.classList.remove('open');
  drawerOverlay?.classList.remove('open');
  document.body.style.overflow = '';
}
hamburger?.addEventListener('click', () => {
  mobileDrawer?.classList.contains('open') ? closeDrawer() : openDrawer();
});
drawerOverlay?.addEventListener('click', closeDrawer);
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeDrawer(); });

// ── AVATAR DROPDOWN ──
const avatarBtn   = document.getElementById('avatarBtn');
const navDropdown = document.getElementById('navDropdown');
if (avatarBtn && navDropdown) {
  avatarBtn.addEventListener('click', e => {
    e.stopPropagation();
    avatarBtn.closest('.nav-user-menu').classList.toggle('open');
  });
  document.addEventListener('click', () => {
    document.querySelector('.nav-user-menu')?.classList.remove('open');
  });
}

// ── SCROLL REVEAL ──
const revealEls = document.querySelectorAll('.reveal');
if (revealEls.length) {
  const ro = new IntersectionObserver(entries => {
    entries.forEach((e, i) => {
      if (e.isIntersecting) {
        setTimeout(() => e.target.classList.add('visible'), i * 40);
      }
    });
  }, { threshold: 0.1 });
  revealEls.forEach(el => ro.observe(el));
}

// ── FLASH AUTO-DISMISS ──
document.querySelectorAll('.flash').forEach(el => {
  setTimeout(() => {
    el.style.transition = 'opacity 0.4s, transform 0.4s';
    el.style.opacity = '0';
    el.style.transform = 'translateX(120%)';
    setTimeout(() => el.remove(), 400);
  }, 5000);
});

// ── TABS ──
document.querySelectorAll('.tab-btn[data-tab]').forEach(btn => {
  btn.addEventListener('click', () => {
    const group = btn.closest('[data-tabs]') || btn.closest('section') || btn.parentElement.parentElement;
    group.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    group.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    const target = document.getElementById(btn.dataset.tab);
    target?.classList.add('active');
  });
});

// ── ACTIVE NAV LINK ──
document.querySelectorAll('.nav-link').forEach(a => {
  if (a.href === window.location.href) a.classList.add('nav-active');
});

// ── RIPPLE EFFECT ON BUTTONS ──
document.querySelectorAll('.btn-primary, .btn-accent, .btn-green').forEach(btn => {
  btn.addEventListener('click', function(e) {
    const r = document.createElement('span');
    const d = Math.max(btn.clientWidth, btn.clientHeight);
    const rect = btn.getBoundingClientRect();
    r.style.cssText = `position:absolute;width:${d}px;height:${d}px;left:${e.clientX - rect.left - d/2}px;top:${e.clientY - rect.top - d/2}px;border-radius:50%;background:rgba(255,255,255,0.25);transform:scale(0);animation:ripple 0.5s ease;pointer-events:none;`;
    btn.style.position = 'relative';
    btn.style.overflow = 'hidden';
    btn.appendChild(r);
    setTimeout(() => r.remove(), 600);
  });
});
// Inject ripple keyframe once
if (!document.getElementById('rippleStyle')) {
  const s = document.createElement('style');
  s.id = 'rippleStyle';
  s.textContent = '@keyframes ripple{to{transform:scale(2.5);opacity:0;}}';
  document.head.appendChild(s);
}

// ── SIDEBAR TOGGLE (dashboard pages) ──
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebar = document.querySelector('.sidebar');
sidebarToggle?.addEventListener('click', () => {
  sidebar?.classList.toggle('open');
});

// ── CONFIRM DIALOGS ──
document.querySelectorAll('[data-confirm]').forEach(el => {
  el.addEventListener('click', e => {
    if (!confirm(el.dataset.confirm)) e.preventDefault();
  });
});

// ── COPY TO CLIPBOARD ──
document.querySelectorAll('[data-copy]').forEach(btn => {
  btn.addEventListener('click', () => {
    navigator.clipboard.writeText(btn.dataset.copy).then(() => {
      const orig = btn.textContent;
      btn.textContent = 'Copied!';
      setTimeout(() => btn.textContent = orig, 2000);
    });
  });
});