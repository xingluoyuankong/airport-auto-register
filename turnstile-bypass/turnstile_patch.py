"""Cloudflare Turnstile Bypass Module for Playwright
融合 ZO注册 v4.0(10层防御) + grok-register(DrissionPage动态点击) 技术

用法：
    # 方法1: 加载Chrome扩展（推荐，最强）
    from turnstile_patch import launch_with_turnstile_bypass
    browser = launch_with_turnstile_bypass()

    # 方法2: 注入init script（lightweight）
    from turnstile_patch import inject_turnstile_patch
    await inject_turnstile_patch(page)

    # 方法3: 主动点击Turnstile checkbox
    from turnstile_patch import click_turnstile
    token = await click_turnstile(page)

自动触发关键词: Turnstile, turnstile, cf-turnstile, cloudflare验证, 人机验证, CF挑战
"""

import os
import time
import json

EXTENSION_DIR = os.path.dirname(os.path.abspath(__file__))

# ============ Turnstile JS Patch (ZO v4.0 精简版，供 playwright-cli eval 使用) ============
TURNSTILE_PATCH_SCRIPT = """
(function(){
    if(window.__TURNSTILE_BYPASS_V4__) return;
    window.__TURNSTILE_BYPASS_V4__=true;
    var _offX=Math.floor(Math.random()*401)+80;
    var _offY=Math.floor(Math.random()*201)+60;
    var _dp=function(obj,prop,getter){
        try{Object.defineProperty(obj,prop,{get:getter,configurable:true,enumerable:true});}catch(e){}
    };
    // L1: MouseEvent screenX/Y 核心绕过
    _dp(MouseEvent.prototype,'screenX',function(){return(this.clientX||0)+_offX+Math.floor(Math.random()*5-2);});
    _dp(MouseEvent.prototype,'screenY',function(){return(this.clientY||0)+_offY+Math.floor(Math.random()*5-2);});
    if(typeof PointerEvent!=='undefined'){
        _dp(PointerEvent.prototype,'screenX',function(){return(this.clientX||0)+_offX+Math.floor(Math.random()*5-2);});
        _dp(PointerEvent.prototype,'screenY',function(){return(this.clientY||0)+_offY+Math.floor(Math.random()*5-2);});
    }
    // L2: window dimensions
    try{if(window.top===window){
        _dp(window,'outerWidth',function(){return window.innerWidth+16+Math.floor(Math.random()*2);});
        _dp(window,'outerHeight',function(){return window.innerHeight+80+Math.floor(Math.random()*5);});
    }}catch(e){}
    // L3: navigator伪装
    _dp(navigator,'webdriver',function(){return undefined;});
    try{Object.defineProperty(Navigator.prototype,'webdriver',{get:function(){return false;},configurable:true});}catch(e){}
    _dp(navigator,'languages',function(){return['zh-CN','zh','en-US','en'];});
    _dp(navigator,'hardwareConcurrency',function(){return 8;});
    _dp(navigator,'deviceMemory',function(){return 8;});
    // userAgentData (2026 CF头号检测向量)
    try{_dp(navigator,'userAgentData',function(){
        var brands=[{brand:'Google Chrome',version:'131'},{brand:'Chromium',version:'131'},{brand:'Not_A Brand',version:'24'}];
        return{brands:brands,mobile:false,platform:'Windows',getHighEntropyValues:async function(){return{platform:'Windows',platformVersion:'10.0.0',architecture:'x86',uaFullVersion:'131.0.6778.265',bitness:'64'};},toJSON:function(){return{brands:brands,mobile:false,platform:'Windows'};}};
    });}catch(e){}
    // L4: plugins补全
    try{_dp(navigator,'plugins',function(){var arr=[{name:'Chrome PDF Plugin',filename:'internal-pdf-viewer',description:'Portable Document Format',length:1},{name:'Chrome PDF Viewer',filename:'mhjfbmdgcfjbbpaeojofohoefgiehjai',description:'',length:1},{name:'Native Client',filename:'internal-nacl-plugin',description:'',length:1}];arr.item=function(i){return this[i]||null;};arr.namedItem=function(n){for(var i=0;i<this.length;i++){if(this[i].name===n)return this[i];}return null;};arr.refresh=function(){};Object.setPrototypeOf(arr,PluginArray.prototype);return arr;});}catch(e){}
    // L5: chrome.runtime
    try{if(!window.chrome)window.chrome={};if(!window.chrome.runtime){window.chrome.runtime={connect:function(){return{onMessage:{addListener:function(){},removeListener:function(){}},postMessage:function(){},disconnect:function(){}};},sendMessage:function(){},onMessage:{addListener:function(){},removeListener:function(){}},onConnect:{addListener:function(){}}};}}catch(e){}
    // L6: 删cdc_标记
    for(var key in window){if(/^cdc_/.test(key)){try{delete window[key];}catch(e){}}}
    // L7: Canvas噪声
    try{var _td=HTMLCanvasElement.prototype.toDataURL;HTMLCanvasElement.prototype.toDataURL=function(){var ctx=this.getContext('2d');if(ctx){var d=ctx.getImageData(0,0,1,1);if(d&&d.data){d.data[0]=d.data[0]^(Math.random()>0.5?1:0);}}return _td.apply(this,arguments);};}catch(e){}
    // L8: WebGL
    try{var _gcp=WebGLRenderingContext.prototype.getParameter;WebGLRenderingContext.prototype.getParameter=function(p){if(p===37445)return'Intel Inc.';if(p===37446)return'Intel Iris OpenGL Engine';return _gcp.call(this,p);};}catch(e){}
    // L9: permissions
    try{var _pq=window.navigator.permissions.query;window.navigator.permissions.query=function(p){if(p.name==='notifications'){return Promise.resolve({state:Notification.permission});}return _pq.call(this,p);};}catch(e){}
    // L10: Shadow DOM跟踪
    try{var _as=Element.prototype.attachShadow;Element.prototype.attachShadow=function(init){var shadow=_as.call(this,init);if(init&&init.mode==='closed'){window.__lastClosedShadowRoot=shadow;}return shadow;};}catch(e){}
    console.log('[TurnstileBypass] v4.0 patches active');
})();
"""


def get_launch_args_with_extension():
    """获取带Turnstile扩展的Playwright launch参数"""
    return {
        "args": [
            f"--disable-extensions-except={EXTENSION_DIR}",
            f"--load-extension={EXTENSION_DIR}",
            "--disable-blink-features=AutomationControlled",
        ],
        "ignore_default_args": ["--enable-automation"],
    }


def launch_with_turnstile_bypass(playwright_instance, channel="msedge", headless=False):
    """启动带Turnstile绕过的浏览器（加载Chrome扩展）
    
    Args:
        playwright_instance: sync_playwright() 返回的 playwright 对象
        channel: 浏览器通道 (msedge/chrome/chromium)
        headless: 是否无头模式
    
    Returns:
        browser 实例
    """
    from playwright.sync_api import sync_playwright
    
    kwargs = {
        "headless": headless,
        "channel": channel,
        "args": [
            f"--disable-extensions-except={EXTENSION_DIR}",
            f"--load-extension={EXTENSION_DIR}",
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
        ],
        "ignore_default_args": ["--enable-automation"],
    }
    
    return playwright_instance.chromium.launch(**kwargs)


async def inject_turnstile_patch(page):
    """向已打开的页面注入Turnstile绕过补丁（Playwright async版本）"""
    await page.evaluate(TURNSTILE_PATCH_SCRIPT)
    print("[TurnstileBypass] Patch injected into page")


def inject_turnstile_patch_sync(page):
    """向已打开的页面注入Turnstile绕过补丁（Playwright sync版本）"""
    page.evaluate(TURNSTILE_PATCH_SCRIPT)
    print("[TurnstileBypass] Patch injected into page")


def get_turnstile_patch_for_eval():
    """返回供 playwright-cli eval 使用的简洁版patch脚本
    用法: playwright-cli eval "(脚本内容)"
    """
    return TURNSTILE_PATCH_SCRIPT.replace('"', '\\"')


# ============ Turnstile 主动点击方案（grok-register 方案） ============

TURNSTILE_CLICK_SCRIPT = """
(function(){
    // 方法1: 使用 Turnstile API
    try {
        if (typeof turnstile !== 'undefined') {
            turnstile.reset();
            setTimeout(function() {
                var token = turnstile.getResponse();
                if (token) {
                    var input = document.querySelector('input[name="cf-turnstile-response"]');
                    if (input) { input.value = token; input.dispatchEvent(new Event('change',{bubbles:true})); }
                }
            }, 3000);
        }
    } catch(e) {}
    
    // 方法2: Shadow DOM穿透点击checkbox
    try {
        var wrapper = document.querySelector('.cf-turnstile, [id*="turnstile"], [class*="turnstile"]');
        if (!wrapper) {
            var inputs = document.querySelectorAll('input[name="cf-turnstile-response"]');
            if (inputs.length > 0) wrapper = inputs[0].parentElement;
        }
        if (wrapper && wrapper.shadowRoot) {
            var iframe = wrapper.shadowRoot.querySelector('iframe');
            if (iframe && iframe.contentDocument) {
                var body = iframe.contentDocument.body;
                if (body && body.shadowRoot) {
                    var checkbox = body.shadowRoot.querySelector('input[type="checkbox"], label');
                    if (checkbox) checkbox.click();
                }
            }
        }
    } catch(e) {}
    
    return 'click_attempted';
})();
"""


def click_turnstile_sync(page, max_wait=30):
    """在页面上主动点击Turnstile验证框并等待通过（Playwright sync版本）
    
    Args:
        page: Playwright page对象
        max_wait: 最大等待秒数
    
    Returns:
        token字符串或None
    """
    # 先注入补丁
    inject_turnstile_patch_sync(page)
    page.wait_for_timeout(1000)
    
    # 尝试主动点击
    page.evaluate(TURNSTILE_CLICK_SCRIPT)
    
    # 轮询等待token
    deadline = time.time() + max_wait
    while time.time() < deadline:
        token = page.evaluate("""
            (function() {
                try {
                    if (typeof turnstile !== 'undefined') {
                        return turnstile.getResponse() || null;
                    }
                } catch(e) {}
                var input = document.querySelector('input[name="cf-turnstile-response"]');
                return input ? input.value || null : null;
            })()
        """)
        if token:
            print(f"[TurnstileBypass] Token obtained: {token[:20]}...")
            return token
        time.sleep(2)
    
    print("[TurnstileBypass] Timeout waiting for Turnstile token")
    return None


# ============ 检测函数 ============

def detect_turnstile(page):
    """检测页面是否有Turnstile挑战"""
    result = page.evaluate("""
        (function() {
            var input = document.querySelector('input[name="cf-turnstile-response"]');
            if (!input) return 'not-found';
            if (input.value) return 'ready';
            return 'pending';
        })()
    """)
    return result


def has_cloudflare_challenge(page):
    """检测是否在CF挑战页面"""
    title = page.title()
    body = page.evaluate("document.body ? document.body.innerText.substring(0,200) : ''")
    cf_keywords = ["just a moment", "attention required", "checking your browser", 
                   "verifying you are human", "ddos protection", "cf-browser-verification"]
    return any(kw in title.lower() or kw in body.lower() for kw in cf_keywords)


# ============ 完整绕过流程 ============

def bypass_turnstile_sync(page, max_wait=30):
    """一站式的Turnstile绕过流程（同步版）
    1. 注入10层防御补丁
    2. 检测CF挑战
    3. 主动点击checkbox
    4. 轮询等待token
    5. 验证挑战是否消失
    """
    # Step 1: 注入补丁
    inject_turnstile_patch_sync(page)
    page.wait_for_timeout(2000)
    
    # Step 2: 等待CF挑战出现或消失
    for i in range(max_wait // 2):
        has_cf = has_cloudflare_challenge(page)
        ts_state = detect_turnstile(page)
        
        print(f"[TurnstileBypass] CF={has_cf}, TS={ts_state}, attempt={i+1}")
        
        if ts_state == 'ready':
            return True  # 已经有了token
        if ts_state == 'pending':
            click_turnstile_sync(page, max_wait=10)
        if not has_cf and ts_state == 'not-found':
            return True  # 没有CF挑战，可能是隐形模式
        
        page.wait_for_timeout(2000)
    
    return False


print("[TurnstileBypass] Module loaded. Methods: launch_with_turnstile_bypass, inject_turnstile_patch_sync, click_turnstile_sync, bypass_turnstile_sync, detect_turnstile, has_cloudflare_challenge")
