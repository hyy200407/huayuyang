/* ===== 粒子网络 + 背景主题 ===== */

const THEMES = {
  sky: {
    name: "天空蓝",
    bg: "#f4f7fa",
    border: "#e2e8ee",
    borderSubtle: "#edf1f5",
    text: "#141d26",
    textDim: "#5a6d7e",
    muted: "#889eae",
    particle: "0, 128, 154",
    particleLine: "0, 128, 154",
    glow1: "0, 160, 200",
    glow2: "60, 140, 210",
    glow3: "30, 140, 110",
  },
  mintLight: {
    name: "薄荷绿",
    bg: "#f2f8f5",
    border: "#d4e6dc",
    borderSubtle: "#e6f2ec",
    text: "#14241c",
    textDim: "#4d7864",
    muted: "#6e9884",
    particle: "50, 148, 106",
    particleLine: "50, 148, 106",
    glow1: "50, 170, 118",
    glow2: "40, 150, 100",
    glow3: "70, 170, 130",
  },
  warmWhite: {
    name: "暖白",
    bg: "#f9f6f2",
    border: "#e8e2d8",
    borderSubtle: "#f0ece4",
    text: "#262018",
    textDim: "#8a7660",
    muted: "#a89278",
    particle: "190, 138, 48",
    particleLine: "190, 138, 48",
    glow1: "210, 150, 58",
    glow2: "190, 120, 72",
    glow3: "210, 130, 50",
  },
  lavender: {
    name: "淡紫",
    bg: "#f6f4fa",
    border: "#e0daf0",
    borderSubtle: "#eeebf6",
    text: "#1a122e",
    textDim: "#6a56a0",
    muted: "#8a78b8",
    particle: "130, 90, 220",
    particleLine: "130, 90, 220",
    glow1: "145, 105, 235",
    glow2: "115, 75, 200",
    glow3: "160, 120, 230",
  },
  slateGray: {
    name: "雾灰",
    bg: "#f5f6f8",
    border: "#e0e2e6",
    borderSubtle: "#eeeff2",
    text: "#181c22",
    textDim: "#647080",
    muted: "#849098",
    particle: "60, 110, 190",
    particleLine: "60, 110, 190",
    glow1: "72, 130, 205",
    glow2: "55, 95, 175",
    glow3: "90, 140, 195",
  },
  coral: {
    name: "珊瑚粉",
    bg: "#fdf6f5",
    border: "#f0dcd8",
    borderSubtle: "#f7eae6",
    text: "#261816",
    textDim: "#a05850",
    muted: "#b87068",
    particle: "210, 85, 76",
    particleLine: "210, 85, 76",
    glow1: "225, 95, 85",
    glow2: "200, 95, 130",
    glow3: "220, 105, 95",
  },
};

const THEME_KEY = "portfolio-theme";
let currentTheme = localStorage.getItem(THEME_KEY) || "sky";

// 粒子颜色变量 —— 提前声明，供 applyTheme() 和粒子循环共用
let particleRGB = (THEMES[currentTheme] || THEMES.sky).particle;
let lineRGB    = (THEMES[currentTheme] || THEMES.sky).particleLine;

function buildBgImage(t) {
  return [
    `radial-gradient(ellipse 800px 600px at 85% 0%, rgba(${t.glow1},0.09) 0%, transparent 65%)`,
    `radial-gradient(ellipse 600px 500px at 5% 100%, rgba(${t.glow2},0.07) 0%, transparent 65%)`,
    `radial-gradient(ellipse 500px 400px at 95% 85%, rgba(${t.glow3},0.05) 0%, transparent 65%)`,
    `linear-gradient(180deg, rgba(${t.glow1},0.04) 0%, transparent 50%)`,
    `radial-gradient(circle, rgba(${t.glow1},0.10) 1px, transparent 1px)`,
  ].join(", ");
}

function applyTheme(id) {
  const t = THEMES[id] || THEMES.sky;
  currentTheme = id;
  localStorage.setItem(THEME_KEY, id);

  const root = document.documentElement;
  root.style.setProperty("--bg", t.bg);
  root.style.setProperty("--border", t.border);
  root.style.setProperty("--border-subtle", t.borderSubtle);
  root.style.setProperty("--text", t.text);
  root.style.setProperty("--text-dim", t.textDim);
  root.style.setProperty("--muted", t.muted);

  document.body.style.backgroundColor = t.bg;
  document.body.style.backgroundImage = buildBgImage(t);
  document.body.style.backgroundSize = "100% 100%, 100% 100%, 100% 100%, 100% 100%, 24px 24px";

  particleRGB  = t.particle;
  lineRGB     = t.particleLine;

  document.querySelectorAll(".swatch").forEach((el) => {
    el.classList.toggle("active", el.dataset.theme === id);
  });
}

function buildSwatches() {
  const container = document.getElementById("theme-swatches");
  container.innerHTML = Object.entries(THEMES)
    .map(([id, t]) =>
      `<button class="swatch${id === currentTheme ? " active" : ""}" data-theme="${id}" aria-label="${t.name}" title="${t.name}"><span style="background:${t.bg}"></span></button>`)
    .join("");

  container.addEventListener("click", (e) => {
    const btn = e.target.closest(".swatch");
    if (!btn) return;
    applyTheme(btn.dataset.theme);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  buildSwatches();
  applyTheme(currentTheme);

  const toggle = document.querySelector(".theme-toggle");
  const picker = document.querySelector(".theme-picker");
  if (toggle && picker) {
    toggle.addEventListener("click", () => picker.classList.toggle("open"));
    document.addEventListener("click", (e) => {
      if (!picker.contains(e.target)) picker.classList.remove("open");
    });
  }
});

// ═══════════════ 粒子系统 ═══════════════
const canvas = document.getElementById("particle-canvas");
const ctx    = canvas.getContext("2d");

const PARTICLE_COUNT = 60;
const CONNECT_DIST   = 130;
const MOUSE_RADIUS   = 200;
const MOUSE_FORCE    = 0.028;

let particles = [];
let mouse     = { x: -9999, y: -9999 };

function resize() {
  canvas.width  = window.innerWidth;
  canvas.height = document.body.scrollHeight;
}
window.addEventListener("resize", resize);
window.addEventListener("scroll", () => { canvas.height = document.body.scrollHeight; });

document.addEventListener("mousemove", (e) => {
  mouse.x = e.clientX;
  mouse.y = e.clientY + window.scrollY;
});
document.addEventListener("mouseleave", () => { mouse.x = -9999; mouse.y = -9999; });
document.addEventListener("touchmove", (e) => {
  mouse.x = e.touches[0].clientX;
  mouse.y = e.touches[0].clientY + window.scrollY;
}, { passive: true });
document.addEventListener("touchend", () => { mouse.x = -9999; mouse.y = -9999; });

function createParticle() {
  return {
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    vx: (Math.random() - 0.5) * 0.4,
    vy: (Math.random() - 0.5) * 0.4,
    r: Math.random() * 1.6 + 0.8,
    opacity: Math.random() * 0.3 + 0.18,
  };
}

particles = Array.from({ length: PARTICLE_COUNT }, createParticle);

(function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  for (let i = 0; i < particles.length; i++) {
    const p = particles[i];
    p.x += p.vx;
    p.y += p.vy;
    if (p.x < -30) p.x = canvas.width + 30;
    if (p.x > canvas.width + 30) p.x = -30;
    if (p.y < -30) p.y = canvas.height + 30;
    if (p.y > canvas.height + 30) p.y = -30;

    const dxm = p.x - mouse.x;
    const dym = p.y - mouse.y;
    const distM = Math.sqrt(dxm * dxm + dym * dym);
    if (distM < MOUSE_RADIUS && distM > 0) {
      const force = ((MOUSE_RADIUS - distM) / MOUSE_RADIUS) * MOUSE_FORCE;
      p.vx += (dxm / distM) * force;
      p.vy += (dym / distM) * force;
    }
    p.vx *= 0.999;
    p.vy *= 0.999;
    const speed = Math.sqrt(p.vx * p.vx + p.vy * p.vy);
    if (speed > 1.0) {
      p.vx = (p.vx / speed) * 1.0;
      p.vy = (p.vy / speed) * 1.0;
    }

    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(${particleRGB}, ${p.opacity})`;
    ctx.fill();

    for (let j = i + 1; j < particles.length; j++) {
      const q = particles[j];
      const dx = p.x - q.x;
      const dy = p.y - q.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < CONNECT_DIST) {
        const alpha = (1 - dist / CONNECT_DIST) * 0.18;
        ctx.beginPath();
        ctx.moveTo(p.x, p.y);
        ctx.lineTo(q.x, q.y);
        ctx.strokeStyle = `rgba(${lineRGB}, ${alpha})`;
        ctx.lineWidth = 0.4;
        ctx.stroke();
      }
    }
  }

  if (mouse.x > 0 && mouse.y > 0) {
    const grd = ctx.createRadialGradient(mouse.x, mouse.y, 0, mouse.x, mouse.y, MOUSE_RADIUS);
    grd.addColorStop(0,   `rgba(${particleRGB}, 0.08)`);
    grd.addColorStop(0.5, `rgba(${particleRGB}, 0.03)`);
    grd.addColorStop(1,   `rgba(${particleRGB}, 0)`);
    ctx.beginPath();
    ctx.arc(mouse.x, mouse.y, MOUSE_RADIUS, 0, Math.PI * 2);
    ctx.fillStyle = grd;
    ctx.fill();
  }

  requestAnimationFrame(draw);
})();

resize();
