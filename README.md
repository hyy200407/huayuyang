<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="Python 数据采集作品集" />
    <title>作品集</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Noto+Sans+SC:wght@400;500;600;700&display=swap" rel="stylesheet" />
    <link rel="stylesheet" href="style.css" />
  </head>
  <body>
    <canvas id="particle-canvas" aria-hidden="true"></canvas>

    <div class="theme-picker" role="region" aria-label="背景主题切换">
      <button class="theme-toggle" aria-label="切换背景主题" title="切换背景主题">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="5"/><line x1="12" y1="2" x2="12" y2="7"/><line x1="12" y1="17" x2="12" y2="22"/><line x1="2" y1="12" x2="7" y2="12"/><line x1="17" y1="12" x2="22" y2="12"/></svg>
      </button>
      <div class="theme-swatches" id="theme-swatches"></div>
    </div>

    <div class="scroll-progress" aria-hidden="true"><span></span></div>
    <header class="site-header" id="site-header">
      <a class="brand" href="#top" aria-label="回到顶部"><span>PY</span><span data-bind="shortName">LJ</span></a>
      <nav aria-label="主导航" id="main-nav">
        <a href="#work" data-section="work">作品</a>
        <a href="#about" data-section="about">关于我</a>
        <a href="#contact" data-section="contact">联系</a>
      </nav>
      <a class="header-link" data-bind-href="resumeUrl" data-visible="resumeUrl" target="_blank" rel="noreferrer">简历</a>
      <button class="hamburger" id="hamburger" aria-label="打开菜单" aria-expanded="false">
        <span></span><span></span><span></span>
      </button>
    </header>
    <div class="mobile-nav" id="mobile-nav" aria-hidden="true">
      <nav aria-label="移动端导航">
        <a href="#work" data-section="work">作品</a>
        <a href="#about" data-section="about">关于我</a>
        <a href="#contact" data-section="contact">联系</a>
      </nav>
      <a class="header-link mobile-resume" data-bind-href="resumeUrl" data-visible="resumeUrl" target="_blank" rel="noreferrer">简历</a>
    </div>

    <main id="top">
      <section class="intro section-shell" aria-labelledby="intro-title">
        <div class="intro-copy">
          <p class="eyebrow">PYTHON / DATA COLLECTION</p>
          <h1 id="intro-title">你好，我是<span data-bind="name">林嘉</span></h1>
          <p class="role" data-bind="title">Python 数据采集学习者</p>
          <p class="summary" data-bind="summary">用代码把开放数据变成可理解的信息。我专注网页采集、数据清洗与自动化流程。</p>
          <div class="actions">
            <a class="button primary" href="#work">查看作品</a>
            <a class="button secondary" data-bind-href="github" target="_blank" rel="noreferrer">GitHub</a>
            <a class="button secondary" data-bind-href="csdn" target="_blank" rel="noreferrer">CSDN</a>
            <a class="button secondary" data-bind-href="gitee" target="_blank" rel="noreferrer">gitee</a>
          </div>
        </div>
        <aside class="profile-panel" aria-label="个人资料">
          <div class="portrait" aria-hidden="true"><span data-bind="initials">LJ</span></div>
          <div class="profile-meta"><span>当前状态</span><strong data-bind="status">持续学习中</strong></div>
          <div class="profile-meta"><span>所在地</span><strong data-bind="location">中国 · 杭州</strong></div>
          <div class="profile-line"><span></span><span></span><span></span><span></span><span></span></div>
        </aside>
      </section>

      <section class="stats section-shell" aria-label="作品数据">
        <div><strong id="project-count">0</strong><span>精选项目</span></div>
        <div><strong data-bind="studyHours">120+</strong><span>学习时长</span></div>
        <div><strong data-bind="skillCount">06</strong><span>掌握工具</span></div>
      </section>

      <section class="work-section section-shell" id="work" aria-labelledby="work-title">
        <div class="section-heading">
          <div><p class="eyebrow">SELECTED WORK</p><h2 id="work-title">作品集</h2></div>
          <div class="filter-group" aria-label="筛选作品">
            <button class="filter active" data-filter="all">全部</button>
            <button class="filter" data-filter="crawler">爬虫采集</button>
            <button class="filter" data-filter="automation">自动化</button>
            <button class="filter" data-filter="analysis">数据分析</button>
            <button class="filter" data-filter="creative">创意作品</button>
          </div>
        </div>
        <div class="project-grid" id="project-grid"></div>
      </section>

      <section class="about-section section-shell" id="about" aria-labelledby="about-title">
        <div><p class="eyebrow">ABOUT ME</p><h2 id="about-title">不只采集，更关注数据的下一步。</h2></div>
        <div class="about-content">
          <p data-bind="about">我正在系统学习 Python 数据采集与自动化。每个项目都从一个具体问题出发，完成从抓取、清洗到可视化展示的完整流程。</p>
          <div class="skills" id="skills"></div>
        </div>
      </section>

      <section class="contact-section" id="contact" aria-labelledby="contact-title">
        <div class="section-shell contact-inner">
          <p class="eyebrow">GET IN TOUCH</p>
          <h2 id="contact-title">期待和你交流<br />有趣的数据问题。</h2>
          <a class="contact-mail" data-bind-href="emailLink" data-bind="email">hello@example.com</a>
        </div>
      </section>
    </main>

    <footer class="section-shell"><span>&copy; <span id="year"></span> <span data-bind="name">林嘉</span></span><span>Built with GitHub Pages</span></footer>
    <script src="content.js"></script>
    <script src="script.js"></script>
    <script src="effects.js"></script>
  </body>
</html>
