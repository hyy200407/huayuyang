"""
多平台价格监控系统
整合淘宝、京东、1688三个平台的价格监控
"""
from flask import Flask, render_template, request, jsonify
from DrissionPage import ChromiumPage, ChromiumOptions
from serverchan_sdk import sc_send
import threading
import time
import json
import os

app = Flask(__name__)

# 商品数据 JSON 文件路径
PRODUCTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '商品.json')

# 全局监控状态
monitor_status = {
    'running': False,
    'result': None,
    'logs': [],
    'products': []  # 已添加的商品列表
}

# 登录状态缓存（每个平台对应一个浏览器页实例）
_login_states = {
    'jd': {'logged_in': False, 'page': None},
    'taobao': {'logged_in': False, 'page': None},
    '1688': {'logged_in': True, 'page': None},  # 1688 无需登录
}

# 无头模式浏览器实例（1688 专用 / 登录后使用）
_headless_page = None

# 平台是否需要登录
PLATFORM_NEEDS_LOGIN = {
    'jd': True,
    'taobao': True,
    '1688': False,
}

# 各平台用于检测登录状态的 URL 和判定文本
LOGIN_CHECK = {
    'jd': {
        'url': 'https://www.jd.com/',
        'check_js': 'return document.cookie.includes("pin=") || document.querySelector(".nickname") !== null || document.querySelector(".user-name") !== null',
    },
    'taobao': {
        'url': 'https://www.taobao.com/',
        'check_js': 'return document.cookie.includes("_tb_token_") || document.querySelector(".site-nav-login-info-small") === null',
    },
}


def load_products():
    """从 JSON 文件加载商品列表"""
    try:
        if os.path.exists(PRODUCTS_FILE):
            with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
                products = json.load(f)
                # 过滤掉非商品数据（如 success、message 等字段）
                monitor_status['products'] = [
                    {k: v for k, v in p.items() if k in ('image', 'platform', 'platform_name', 'price', 'title', 'url')}
                    for p in products
                ]
    except Exception as e:
        print(f'加载商品数据失败: {e}')
        monitor_status['products'] = []


def save_products():
    """将商品列表保存到 JSON 文件"""
    try:
        with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(monitor_status['products'], f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f'保存商品数据失败: {e}')


# 启动时加载已有商品
load_products()


def _create_headless_page():
    """创建无头模式浏览器（带反检测参数）"""
    global _headless_page
    co = ChromiumOptions()
    co.headless(True)
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-gpu')
    co.set_argument('--disable-dev-shm-usage')
    # 反检测：去掉自动化标记
    co.set_argument('--disable-blink-features=AutomationControlled')
    # 伪造常见 User-Agent
    co.set_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    # 隐藏 headless 特征
    co.set_argument('--disable-features=IsolateOrigins,site-per-process')
    co.set_argument('--disable-site-isolation-trials')
    _headless_page = ChromiumPage(co)

    # 注入 JS 隐藏 webdriver 等自动化痕迹
    try:
        _headless_page.run_js('''
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh']});
            window.chrome = {runtime: {}};
        ''')
    except Exception:
        pass

    return _headless_page


def _create_visible_page():
    """创建有界面浏览器（用于登录）"""
    return ChromiumPage()


def _is_page_alive(page):
    """检测浏览器页面是否仍然可用"""
    if page is None:
        return False
    try:
        # 尝试执行一个轻量 JS 来验证连接
        page.run_js('return 1')
        return True
    except Exception:
        return False


def _reset_headless_page():
    """重置无头浏览器实例（浏览器被关闭后调用）"""
    global _headless_page
    _headless_page = None
    log('无头浏览器已断开，已重置')


def _reset_visible_page(platform):
    """重置指定平台的可见浏览器实例"""
    _login_states[platform]['page'] = None
    _login_states[platform]['logged_in'] = False
    log(f'[{PLATFORM_CONFIG[platform]["name"]}] 浏览器已断开，已重置')


def get_headless_page():
    """获取无头浏览器实例（自动检测并重建已断开的连接）"""
    global _headless_page
    if _headless_page is not None and not _is_page_alive(_headless_page):
        _reset_headless_page()
    if _headless_page is None:
        _headless_page = _create_headless_page()
    return _headless_page


def check_platform_login(platform):
    """
    检测指定平台是否已登录。
    返回 True/False。
    对于不需要登录的平台（1688），直接返回 True。
    """
    if not PLATFORM_NEEDS_LOGIN.get(platform, True):
        return True

    # 先看缓存
    if _login_states[platform]['logged_in']:
        return True

    check_cfg = LOGIN_CHECK.get(platform)
    if not check_cfg:
        return True

    page = _login_states[platform].get('page')
    if page is None:
        return False

    # 检查页面是否还活着
    if not _is_page_alive(page):
        _login_states[platform]['page'] = None
        _login_states[platform]['logged_in'] = False
        return False

    try:
        page.get(check_cfg['url'])
        page.wait(5)
        result = page.run_js(check_cfg['check_js'])
        _login_states[platform]['logged_in'] = bool(result)
        return bool(result)
    except Exception as e:
        # 如果异常是断开连接，重置页面
        if 'disconnect' in str(e).lower() or 'closed' in str(e).lower():
            _reset_visible_page(platform)
        print(f'[{platform}] 登录检测失败: {e}')
        return False


def ensure_login(platform):
    """
    确保指定平台已登录。
    - 1688：不需要登录，返回 (True, page)
    - 京东/淘宝：先检测登录状态，已登录返回 (True, page)，
      未登录则打开有界面浏览器让用户登录，返回 (False, page)
    """
    if not PLATFORM_NEEDS_LOGIN.get(platform, True):
        # 1688：无需登录，直接用无头模式
        return True, get_headless_page()

    # 检查是否已有可见页面实例
    page = _login_states[platform].get('page')

    # 如果页面已断开，重置
    if page is not None and not _is_page_alive(page):
        _reset_visible_page(platform)
        page = None

    if page is None:
        # 首次打开或重连：打开有界面浏览器
        log(f'[{PLATFORM_CONFIG[platform]["name"]}] 正在打开浏览器，请登录...')
        page = _create_visible_page()
        _login_states[platform]['page'] = page

    # 检测登录状态
    if check_platform_login(platform):
        # 已登录，可以切到无头模式继续操作
        log(f'[{PLATFORM_CONFIG[platform]["name"]}] 已登录 ✓')
        _login_states[platform]['logged_in'] = True
        return True, get_headless_page()
    else:
        # 未登录：用可见页面打开登录页
        login_urls = {
            'jd': 'https://passport.jd.com/new/login.aspx',
            'taobao': 'https://login.taobao.com/member/login.jhtml',
        }
        login_url = login_urls.get(platform, PLATFORM_CONFIG[platform]['name'] + '登录页')
        try:
            page.get(login_url)
        except Exception:
            # 如果打开登录页失败（浏览器被关），重置并重试打开
            _reset_visible_page(platform)
            page = _create_visible_page()
            _login_states[platform]['page'] = page
            try:
                page.get(login_url)
            except Exception:
                pass
        log(f'[{PLATFORM_CONFIG[platform]["name"]}] 请在打开的浏览器中完成登录，登录后重试')
        return False, page


def get_platform_page(platform):
    """
    获取最佳页面用于操作：
    - 1688 或已登录平台 → 无头页面
    - 未登录 → 返回可见页面（已被 ensure_login 打开登录页）
    """
    if not PLATFORM_NEEDS_LOGIN.get(platform, True):
        return get_headless_page()

    if _login_states[platform]['logged_in']:
        return get_headless_page()
    else:
        return _login_states[platform].get('page') or get_headless_page()

# 三个平台的XPath配置
PLATFORM_CONFIG = {
    'jd': {
        'name': '京东',
        'title_xpath': 'xpath://span[@class="sku-title-name"]',
        'price_xpath': 'xpath://span[@class="product-price--value"]',
        "imgxpath":'xpath://img[@id="spec-img"]',
        'title_length': 10
    },
    'taobao': {
        'name': '淘宝',
        'title_xpath': 'xpath://span[@class="mainTitle--R75fTcZL"]',
        'price_xpath': 'xpath://div[@class="block2--MLcO9YdF"]//span[last()]',
        "imgxpath":'xpath://img[@id="J_ImgBooth"] | //img[@id="mainPicImageEl"] | //div[contains(@class,"PicGallery")]//img | //img[contains(@class,"mainPicImg")]',
        'title_length': 15
    },
    '1688': {
        'name': '1688',
        'title_xpath': 'xpath://div[@class="title-content"]/h1',
        'price_xpath': 'xpath://div[@class="price-info"]//span[@class="currency"]',
        "imgxpath":'xpath://div[@class="od-gallery-list-wapper"]/ul/li//img',
        'title_length': 15
    }
}


def log(message):
    """添加日志"""
    monitor_status['logs'].append(message)
    print(message)


def fetch_product_info(platform, url):
    """获取商品信息（自动处理浏览器断开重连）"""
    config = PLATFORM_CONFIG[platform]

    for attempt in range(2):
        page = get_platform_page(platform)
        try:
            page.get(url)
            page.wait(8)

            # 获取标题
            title_elem = page.ele(config['title_xpath'])
            title = title_elem.text[:config['title_length']] if title_elem else "未知商品"

            # 获取价格
            price_elem = page.ele(config['price_xpath'])
            price_text = price_elem.text if price_elem else "0"
            price_clean = ''.join(c for c in price_text if c.isdigit() or c == '.')
            price = float(price_clean) if price_clean else 0

            # 获取图片
            img_elem = page.ele(config['imgxpath'])
            img_url = ""
            if img_elem:
                # 等待图片加载
                page.wait(2)
                # 尝试多个可能的属性（按优先级）
                img_url = (img_elem.attr('src') or
                          img_elem.attr('data-src') or
                          img_elem.attr('data-original') or
                          img_elem.attr('data-lazy-src') or
                          img_elem.attr('data-ks-lazyload') or
                          img_elem.attr('data-lazyload') or
                          img_elem.attr('data-img') or "")
                # 如果属性方式获取不到，尝试通过 JS 获取真正的 src 属性
                if not img_url:
                    try:
                        img_url = img_elem.run_js('return this.src') or ''
                    except Exception:
                        pass
                # 确保是完整URL
                if img_url and img_url.startswith('//'):
                    img_url = 'https:' + img_url
                # 如果是相对路径，补全域名
                elif img_url and img_url.startswith('/'):
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    img_url = f"{parsed.scheme}://{parsed.netloc}{img_url}"

            return {
                'success': True,
                'platform': platform,
                'platform_name': config['name'],
                'title': title,
                'price': price,
                'image': img_url,
                'url': url
            }

        except Exception as e:
            err_msg = str(e)
            is_disconnect = 'disconnect' in err_msg.lower() or 'closed' in err_msg.lower() or 'not connected' in err_msg.lower()
            if attempt == 0 and is_disconnect:
                # 浏览器断开，重置并重试一次
                if PLATFORM_NEEDS_LOGIN.get(platform, True):
                    _reset_visible_page(platform)
                else:
                    _reset_headless_page()
                log(f'[{config["name"]}] 浏览器断开，正在重新连接...')
                continue
            return {
                'success': False,
                'message': err_msg
            }


def check_price(page, product, ideal_price):
    """检查单个商品的价格"""
    platform = product['platform']
    config = PLATFORM_CONFIG[platform]
    
    try:
        page.get(product['url'])
        page.wait(8)
        
        # 获取最新价格
        price_elem = page.ele(config['price_xpath'])
        if not price_elem:
            log(f"[{config['name']}] 无法获取价格")
            return None
        
        price_text = price_elem.text
        price_clean = ''.join(c for c in price_text if c.isdigit() or c == '.')
        price = float(price_clean)
        
        log(f"[{config['name']}] {product['title']} 当前价格: {price}元")
        
        if price < ideal_price:
            return {
                'platform': config['name'],
                'title': product['title'],
                'price': price,
                'url': product['url'],
                'image': product.get('image', '')
            }
        
    except Exception as e:
        log(f"[{config['name']}] 检查失败: {str(e)}")
    
    return None


def monitor_task(products, ideal_price, sendkey, interval):
    """后台监控任务（自动处理浏览器断开重连）"""
    page = get_headless_page()

    try:
        while monitor_status['running']:
            # 每次循环前检查页面存活，断连则重建
            if not _is_page_alive(page):
                _reset_headless_page()
                page = get_headless_page()
                log('监控浏览器断开，已重新连接')

            # 检查所有商品
            for product in products:
                if not monitor_status['running']:
                    break

                try:
                    result = check_price(page, product, ideal_price)
                except Exception as e:
                    log(f"[{product.get('platform_name', '')}] 检查异常: {str(e)}")
                    result = None

                if result:
                    # 找到符合条件的商品
                    monitor_status['result'] = result
                    monitor_status['running'] = False

                    # 发送微信通知
                    if sendkey:
                        title = f"【{result['platform']}】{result['title']}已降价"
                        desc = f"当前价格: {result['price']}元\n点击购买: {result['url']}"
                        try:
                            sc_send(sendkey, title, desc)
                            log(f"✓ 微信通知已发送")
                        except Exception as e:
                            log(f"✗ 微信通知发送失败: {str(e)}")

                    log(f"✓ 发现符合条件的商品！{result['platform']} - {result['title']} - {result['price']}元")
                    break

            # 按设定的间隔等待
            if monitor_status['running']:
                time.sleep(interval)

    finally:
        log("监控已停止")


@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/fetch_product', methods=['POST'])
def fetch_product():
    """获取商品信息"""
    data = request.json
    platform = data.get('platform', '')
    url = data.get('url', '').strip()
    
    if platform not in PLATFORM_CONFIG:
        return jsonify({'success': False, 'message': '无效的平台'})
    
    if not url:
        return jsonify({'success': False, 'message': '请输入商品链接'})

    # 京东/淘宝需要先确保登录
    if PLATFORM_NEEDS_LOGIN.get(platform, True):
        is_logged, _ = ensure_login(platform)
        if not is_logged:
            return jsonify({
                'success': False,
                'message': f'请在打开的浏览器中完成{PLATFORM_CONFIG[platform]["name"]}登录，完成后重试'
            })

    result = fetch_product_info(platform, url)
    return jsonify(result)


@app.route('/start', methods=['POST'])
def start_monitor():
    """开始监控"""
    if monitor_status['running']:
        return jsonify({'success': False, 'message': '监控已在运行中'})
    
    data = request.json
    ideal_price = float(data.get('ideal_price', 0))
    interval = int(data.get('interval', 30))
    sendkey = data.get('sendkey', '').strip()
    products = monitor_status.get('products', [])

    if not products:
        return jsonify({'success': False, 'message': '请先添加至少一个商品'})

    if ideal_price <= 0:
        return jsonify({'success': False, 'message': '预期价格必须大于0'})

    if interval < 5:
        return jsonify({'success': False, 'message': '监控间隔不能小于5秒'})

    # 确保所有涉及平台都已登录（京东/淘宝需要登录，1688 不需要）
    platforms_needed = set(p['platform'] for p in products)
    for plat in platforms_needed:
        if PLATFORM_NEEDS_LOGIN.get(plat, True):
            is_logged, _ = ensure_login(plat)
            if not is_logged:
                return jsonify({
                    'success': False,
                    'message': f'请先在打开的浏览器中完成{PLATFORM_CONFIG[plat]["name"]}登录，再点击开始'
                })

    # 重置状态
    monitor_status['running'] = True
    monitor_status['result'] = None
    monitor_status['logs'] = [f'开始监控，每{interval}秒检查一次...']

    # 启动后台线程
    thread = threading.Thread(
        target=monitor_task,
        args=(products, ideal_price, sendkey, interval),
        daemon=True
    )
    thread.start()

    return jsonify({'success': True, 'message': f'监控已开始，间隔{interval}秒'})


@app.route('/stop', methods=['POST'])
def stop_monitor():
    """停止监控"""
    monitor_status['running'] = False
    return jsonify({'success': True, 'message': '监控已停止'})


@app.route('/login_status/<platform>')
def login_status(platform):
    """查询指定平台的登录状态，供前端轮询"""
    if platform not in PLATFORM_CONFIG:
        return jsonify({'logged_in': False, 'message': '无效的平台'})

    if not PLATFORM_NEEDS_LOGIN.get(platform, True):
        return jsonify({'logged_in': True, 'needs_login': False})

    logged_in = check_platform_login(platform)
    return jsonify({'logged_in': logged_in, 'needs_login': True})


@app.route('/sync_products', methods=['POST'])
def sync_products():
    """同步前端商品列表到后端"""
    data = request.json
    products = data.get('products', [])
    monitor_status['products'] = products
    save_products()
    return jsonify({'success': True, 'message': f'已同步 {len(products)} 件商品'})


@app.route('/add_product', methods=['POST'])
def add_product():
    """添加商品到监控列表"""
    data = request.json
    product = data.get('product')
    
    if not product:
        return jsonify({'success': False, 'message': '无效的商品数据'})

    # 去重：相同 URL 不重复添加
    for p in monitor_status['products']:
        if p.get('url') == product.get('url'):
            return jsonify({'success': False, 'message': '该商品已存在'})

    monitor_status['products'].append(product)
    save_products()
    return jsonify({'success': True, 'message': '商品已添加'})


@app.route('/remove_product', methods=['POST'])
def remove_product():
    """从监控列表移除商品"""
    data = request.json
    index = data.get('index')
    
    if index is None or index < 0 or index >= len(monitor_status['products']):
        return jsonify({'success': False, 'message': '无效的商品索引'})
    
    monitor_status['products'].pop(index)
    save_products()
    return jsonify({'success': True, 'message': '商品已移除'})


@app.route('/status')
def get_status():
    """获取监控状态"""
    return jsonify({
        'running': monitor_status['running'],
        'result': monitor_status['result'],
        'logs': monitor_status['logs'],
        'products': monitor_status['products']
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
