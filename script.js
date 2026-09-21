const bindText = (key, value) => {
  document.querySelectorAll(`[data-bind="${key}"]`).forEach((node) => { node.textContent = value; });
};

Object.entries(portfolio).forEach(([key, value]) => {
  if (typeof value === "string") bindText(key, value);
});

document.querySelectorAll("[data-bind-href]").forEach((node) => {
  const value = portfolio[node.dataset.bindHref];
  if (value) node.href = value;
  else node.hidden = true;
});

bindText("emailLink", `mailto:${portfolio.email}`);

// ═══════════════ 导航栏：滚动感知 + 活跃链接 + 进度条 ═══════════════
const siteHeader = document.getElementById("site-header");
const progressBar = document.querySelector(".scroll-progress span");
const navLinks = document.querySelectorAll("#main-nav a, .mobile-nav nav a");

// --- 滚动进度条 ---
function updateScrollProgress() {
  const scrollTop = window.scrollY;
  const docHeight = document.documentElement.scrollHeight - window.innerHeight;
  const progress = docHeight > 0 ? Math.min((scrollTop / docHeight) * 100, 100) : 0;
  progressBar.style.width = `${progress}%`;
}

// --- Header 紧凑模式 ---
function updateHeaderState() {
  const scrolled = window.scrollY > 20;
  siteHeader.classList.toggle("scrolled", scrolled);
}

// --- 活跃链接 (IntersectionObserver) ---
const sectionIds = ["work", "about", "contact"];
const sectionEls = sectionIds.map((id) => document.getElementById(id)).filter(Boolean);

const sectionObserver = new IntersectionObserver(
  (entries) => {
    let activeId = null;
    let minTop = Infinity;
    entries.forEach((entry) => {
      if (entry.isIntersecting && entry.boundingClientRect.top < minTop) {
        minTop = entry.boundingClientRect.top;
        activeId = entry.target.id;
      }
    });
    if (activeId) {
      navLinks.forEach((link) => {
        const isActive = link.dataset.section === activeId;
        link.classList.toggle("active", isActive);
      });
    }
  },
  { threshold: [0.15, 0.4], rootMargin: "-72px 0px -40% 0px" }
);

sectionEls.forEach((el) => sectionObserver.observe(el));

// --- 合并滚动回调 ---
let ticking = false;
window.addEventListener("scroll", () => {
  if (!ticking) {
    requestAnimationFrame(() => {
      updateScrollProgress();
      updateHeaderState();
      ticking = false;
    });
    ticking = true;
  }
}, { passive: true });

// 初始化
updateScrollProgress();
updateHeaderState();

// ═══════════════ 移动端菜单 ═══════════════
const hamburger = document.getElementById("hamburger");
const mobileNav = document.getElementById("mobile-nav");
let menuOpen = false;

function openMenu() {
  menuOpen = true;
  hamburger.classList.add("open");
  hamburger.setAttribute("aria-expanded", "true");
  hamburger.setAttribute("aria-label", "关闭菜单");
  mobileNav.classList.add("open");
  mobileNav.setAttribute("aria-hidden", "false");
  document.body.style.overflow = "hidden";
}

function closeMenu() {
  menuOpen = false;
  hamburger.classList.remove("open");
  hamburger.setAttribute("aria-expanded", "false");
  hamburger.setAttribute("aria-label", "打开菜单");
  mobileNav.classList.remove("open");
  mobileNav.setAttribute("aria-hidden", "true");
  document.body.style.overflow = "";
}

hamburger.addEventListener("click", () => {
  menuOpen ? closeMenu() : openMenu();
});

// 点击移动端菜单链接 → 关闭菜单
mobileNav.querySelectorAll("a").forEach((link) => {
  link.addEventListener("click", () => closeMenu());
});

// ESC 关闭
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && menuOpen) closeMenu();
});

document.title = `${portfolio.name} | Python 作品集`;
document.getElementById("year").textContent = new Date().getFullYear();

document.getElementById("project-count").textContent = String(portfolio.projects.length).padStart(2, "0");

// ═══════════════ 滚动入场动画 ═══════════════
// 必须定义在 renderProjects() 之前，避免 TDZ
const fadeObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add("visible");
      fadeObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.05, rootMargin: "0px 0px -12px 0px" });

function prepareAnimations() {
  document.querySelectorAll(".project-card, .stats div").forEach((el) => {
    fadeObserver.observe(el);
  });
  document.querySelectorAll(".project-card, .stats div").forEach((el, i) => {
    el.classList.add("fade-up");
    el.style.transitionDelay = `${i * 0.04}s`;
  });
}

const labels = { crawler: "爬虫采集", automation: "自动化", analysis: "数据分析", creative: "创意作品" };
const grid = document.getElementById("project-grid");
const renderProjects = (category = "all") => {
  const projects = category === "all" ? portfolio.projects : portfolio.projects.filter((project) => project.category === category);
  grid.innerHTML = projects.map((project) => `
    <article class="project-card accent-${project.accent}">
      <div class="card-thumb thumb-${project.accent}"${project.bgImage ? ` style="background-image:url('${project.bgImage}')"` : ""}></div>
      <div class="project-top"><span class="project-number">${project.number}</span><span class="project-category">${labels[project.category]}</span></div>
      <div class="project-body"><h3>${project.title}</h3><p>${project.description}</p></div>
      <div class="project-bottom"><div class="tags">${project.tags.map((tag) => `<span>${tag}</span>`).join("")}</div><a href="${project.link}" target="_blank" rel="noreferrer">查看项目</a></div>
    </article>`).join("");

  // 新卡片挂载入场动画
  prepareAnimations();
};

document.getElementById("skills").innerHTML = portfolio.skills.map((skill) => `<span>${skill}</span>`).join("");
renderProjects();

document.querySelectorAll(".filter").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelector(".filter.active").classList.remove("active");
    button.classList.add("active");
    renderProjects(button.dataset.filter);
  });
});

// 静态区块
document.querySelectorAll(".intro-copy, .profile-panel, .about-section > div, .contact-inner").forEach((el, i) => {
  el.classList.add("fade-up");
  el.style.transitionDelay = `${i * 0.06}s`;
  // 这些元素在首屏，直接用 timeout 触发动画
  setTimeout(() => el.classList.add("visible"), 60 + i * 60);
});
