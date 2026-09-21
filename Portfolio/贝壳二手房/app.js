// 全局状态
let currentPage = 1;
const pageSize = 10;
let filteredData = [...houseData];
let currentSort = 'default';

// 初始化
document.addEventListener('DOMContentLoaded', function() {
  initAuthModal();
  if (window.location.pathname.includes('detail.html')) {
    initDetail();
    return;
  }
  initFilters();
  initSortTabs();
  renderHouseList();
  initNavSwitch();
});

// 初始化筛选器
function initFilters() {
  // 位置筛选
  document.querySelectorAll('#areaFilter .filter-option').forEach(opt => {
    opt.addEventListener('click', function() {
      document.querySelectorAll('#areaFilter .filter-option').forEach(o => o.classList.remove('active'));
      this.classList.add('active');
      applyFilters();
    });
  });

  // 价格筛选
  document.querySelectorAll('#priceFilter .filter-option').forEach(opt => {
    opt.addEventListener('click', function() {
      document.querySelectorAll('#priceFilter .filter-option').forEach(o => o.classList.remove('active'));
      this.classList.add('active');
      applyFilters();
    });
  });

  // 户型筛选
  document.querySelectorAll('#layoutFilter .filter-option').forEach(opt => {
    opt.addEventListener('click', function() {
      document.querySelectorAll('#layoutFilter .filter-option').forEach(o => o.classList.remove('active'));
      this.classList.add('active');
      applyFilters();
    });
  });

  // 搜索框
  document.getElementById('searchInput').addEventListener('keyup', function(e) {
    if (e.key === 'Enter') applyFilters();
  });
}

// 初始化排序标签
function initSortTabs() {
  document.querySelectorAll('.sort-tab').forEach(tab => {
    tab.addEventListener('click', function() {
      document.querySelectorAll('.sort-tab').forEach(t => t.classList.remove('active'));
      this.classList.add('active');
      currentSort = this.dataset.sort;
      applyFilters();
    });
  });
}

// 获取筛选值
function getFilterValue(containerId) {
  const active = document.querySelector(`#${containerId} .filter-option.active`);
  return active ? active.dataset.value : '';
}

// 应用筛选条件
function applyFilters() {
  const area = getFilterValue('areaFilter');
  const price = getFilterValue('priceFilter');
  const layout = getFilterValue('layoutFilter');
  const searchText = document.getElementById('searchInput').value.toLowerCase().trim();

  filteredData = houseData.filter(house => {
    // 位置筛选
    if (area && house.address !== area) return false;

    // 价格筛选
    if (price) {
      const [min, max] = price.split('-').map(Number);
      if (max && (house.totalPrice < min || house.totalPrice > max)) return false;
      if (!max && house.totalPrice < min) return false;
    }

    // 户型筛选
    if (layout && house.layout !== layout) return false;

    // 搜索筛选
    if (searchText) {
      const searchIn = (house.title + house.address + house.description).toLowerCase();
      if (!searchIn.includes(searchText)) return false;
    }

    return true;
  });

  // 排序
  if (currentSort === 'price-asc') {
    filteredData.sort((a, b) => a.totalPrice - b.totalPrice);
  } else if (currentSort === 'price-desc') {
    filteredData.sort((a, b) => b.totalPrice - a.totalPrice);
  } else if (currentSort === 'area-desc') {
    filteredData.sort((a, b) => b.area - a.area);
  }

  currentPage = 1;
  renderHouseList();
}

// 生成标签
function generateTags(house) {
  const tags = [];
  if (house.orientation.includes('南') && house.orientation.includes('北')) {
    tags.push({ text: '南北通透', cls: 'tag-blue' });
  }
  if (house.year && parseInt(house.year) < 2000) {
    tags.push({ text: '满五年', cls: 'tag-green' });
  }
  if (house.floor.includes('中楼层') || house.floor.includes('高楼层')) {
    tags.push({ text: '楼层好', cls: 'tag-orange' });
  }
  if (house.description.includes('精装修') || house.description.includes('精装')) {
    tags.push({ text: '精装修', cls: 'tag-red' });
  }
  if (house.description.includes('满五唯一') || house.description.includes('满5唯1')) {
    tags.push({ text: '满五唯一', cls: 'tag-green' });
  }
  if (house.description.includes('电梯')) {
    tags.push({ text: '有电梯', cls: 'tag-blue' });
  }
  return tags;
}

// 渲染房源列表
function renderHouseList() {
  const listContainer = document.getElementById('houseList');
  if (!listContainer) return;

  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const pageData = filteredData.slice(startIndex, endIndex);

  const resultCount = document.getElementById('resultCount');
  if (resultCount) resultCount.textContent = filteredData.length;

  if (pageData.length === 0) {
    listContainer.innerHTML = '<div style="text-align:center;padding:80px 0;color:#999;font-size:16px;">抱歉，没有找到符合条件的房源</div>';
    document.getElementById('pagination').innerHTML = '';
    return;
  }

  listContainer.innerHTML = pageData.map(house => {
    const tags = generateTags(house);
    return `
      <div class="house-card" onclick="goToDetail(${house.id})">
        <div class="house-thumb">
          <img src="images/house_${house.id}.jpg" alt="${house.title}" style="width:100%;height:100%;object-fit:cover;">
          <div class="vr-badge">VR</div>
        </div>
        <div class="house-info">
          <div class="house-info-top">
            <div class="house-name">${house.title}</div>
            <div class="house-meta">
              ${house.address} <span>|</span> ${house.floor} <span>|</span> ${house.layout} <span>|</span> ${house.area}㎡ <span>|</span> ${house.orientation}
            </div>
            <div class="house-tags">
              ${tags.map(t => `<span class="tag ${t.cls}">${t.text}</span>`).join('')}
            </div>
          </div>
          <div class="house-bottom">
            <div class="house-price-area">
              <div class="house-total-price">${house.totalPrice}<em>万</em></div>
              <div class="house-unit-price">${house.unitPrice}</div>
            </div>
            <div class="house-follow">
              <span class="follow-icon">♡</span>
              <span class="follow-text">关注</span>
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');

  renderPagination();
}

// 渲染分页
function renderPagination() {
  const pagination = document.getElementById('pagination');
  if (!pagination) return;

  const totalPages = Math.ceil(filteredData.length / pageSize);
  if (totalPages <= 1) { pagination.innerHTML = ''; return; }

  let html = `<button class="page-btn" onclick="changePage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>上一页</button>`;

  for (let i = 1; i <= totalPages; i++) {
    if (i === 1 || i === totalPages || (i >= currentPage - 1 && i <= currentPage + 1)) {
      html += `<button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="changePage(${i})">${i}</button>`;
    } else if (i === currentPage - 2 || i === currentPage + 2) {
      html += `<span style="color:#999;">...</span>`;
    }
  }

  html += `<button class="page-btn" onclick="changePage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>下一页</button>`;
  pagination.innerHTML = html;
}

// 切换页码
function changePage(page) {
  const totalPages = Math.ceil(filteredData.length / pageSize);
  if (page < 1 || page > totalPages) return;
  currentPage = page;
  renderHouseList();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// 跳转到详情页
function goToDetail(id) {
  window.location.href = `detail.html?id=${id}`;
}

// 详情页初始化
function initDetail() {
  const urlParams = new URLSearchParams(window.location.search);
  const id = parseInt(urlParams.get('id'));
  const house = houseData.find(h => h.id === id);

  if (!house) {
    document.querySelector('.detail-wrapper').innerHTML = '<div style="text-align:center;padding:80px;color:#999;">房源不存在或已下架</div>';
    return;
  }

  document.getElementById('detailImage').src = `images/house_${house.id}.jpg`;
  document.getElementById('detailImage').alt = house.title;
  document.getElementById('detailTitle').textContent = house.title;
  document.getElementById('detailTotalPrice').innerHTML = `${house.totalPrice}<em>万</em>`;
  document.getElementById('detailUnitPrice').textContent = house.unitPrice;

  document.getElementById('detailInfoTable').innerHTML = `
    <tr><td>房屋户型</td><td>${house.layout}</td></tr>
    <tr><td>建筑面积</td><td>${house.area}㎡</td></tr>
    <tr><td>套内面积</td><td>${(house.area * 0.82).toFixed(2)}㎡</td></tr>
    <tr><td>房屋朝向</td><td>${house.orientation}</td></tr>
    <tr><td>所在楼层</td><td>${house.floor}</td></tr>
    <tr><td>建筑年代</td><td>${house.year || '暂无数据'}</td></tr>
    <tr><td>房屋用途</td><td>普通住宅</td></tr>
    <tr><td>产权年限</td><td>70年</td></tr>
    <tr><td>所属小区</td><td>${house.address}</td></tr>
    <tr><td>挂牌时间</td><td>${Math.floor(Math.random() * 12) + 1}个月前</td></tr>
  `;

  document.getElementById('detailDesc').textContent = house.description;
}

// ═══════════════ 登录/注册弹窗 ═══════════════
function initAuthModal() {
  const overlay = document.getElementById('authModal');
  if (!overlay) return;
  const closeBtn = document.getElementById('modalClose');
  const tabs = overlay.querySelectorAll('.modal-tab');
  const loginForm = document.getElementById('loginForm');
  const registerForm = document.getElementById('registerForm');
  const msg = document.getElementById('modalMsg');

  function closeModal() { overlay.hidden = true; }
  function switchTab(tab) {
    tabs.forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
    if (loginForm) loginForm.hidden = tab !== 'login';
    if (registerForm) registerForm.hidden = tab !== 'register';
  }
  function openModal(tab) {
    overlay.hidden = false;
    switchTab(tab || 'login');
    if (msg) { msg.textContent = ''; msg.classList.remove('error'); }
  }

  tabs.forEach(t => t.addEventListener('click', () => switchTab(t.dataset.tab)));
  if (closeBtn) closeBtn.addEventListener('click', closeModal);
  overlay.addEventListener('click', (e) => { if (e.target === overlay) closeModal(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });

  const loginLink = document.getElementById('loginLink');
  const registerLink = document.getElementById('registerLink');
  if (loginLink) loginLink.addEventListener('click', (e) => { e.preventDefault(); openModal('login'); });
  if (registerLink) registerLink.addEventListener('click', (e) => { e.preventDefault(); openModal('register'); });

  if (loginForm) loginForm.addEventListener('submit', (e) => {
    e.preventDefault();
    msg.textContent = '登录成功，欢迎回来！';
    msg.classList.remove('error');
    setTimeout(closeModal, 1200);
  });
  if (registerForm) registerForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const inputs = registerForm.querySelectorAll('input');
    if (inputs[1].value !== inputs[2].value) {
      msg.textContent = '两次输入的密码不一致';
      msg.classList.add('error');
      return;
    }
    msg.textContent = '注册成功，请登录';
    msg.classList.remove('error');
    setTimeout(() => { switchTab('login'); registerForm.reset(); }, 1200);
  });
}

// ═══════════════ 导航栏栏目切换 ═══════════════
function initNavSwitch() {
  const navLinks = document.querySelectorAll('.nav-links a[data-nav]');
  const breadcrumbLinks = document.querySelectorAll('.breadcrumb a');
  breadcrumbLinks.forEach(a => a.addEventListener('click', (e) => e.preventDefault()));

  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      navLinks.forEach(l => l.classList.remove('active'));
      link.classList.add('active');
      const nav = link.dataset.nav;
      const listContainer = document.getElementById('houseList');
      const resultCount = document.getElementById('resultCount');
      const pagination = document.getElementById('pagination');
      if (nav === 'ershou') {
        document.querySelectorAll('#areaFilter .filter-option, #priceFilter .filter-option, #layoutFilter .filter-option')
          .forEach(o => o.classList.toggle('active', o.dataset.value === ''));
        applyFilters();
      } else {
        if (listContainer) listContainer.innerHTML = '<div class="empty-state">该栏目演示数据暂未整理，敬请期待～</div>';
        if (resultCount) resultCount.textContent = '0';
        if (pagination) pagination.innerHTML = '';
      }
    });
  });
}
