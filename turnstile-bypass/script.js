/**
 * ZO Turnstile Bypass v4.0
 * 
 * 核心原理：Turnstile 检测 MouseEvent.screenX === clientX → 机器人
 * 真实用户 screenX = clientX + 窗口左边距（80~400px）
 * 
 * ★ v4 修复：移除了 v3.0 的 CF iframe 守卫，补丁在所有 frame 中运行
 * ★ 参考 grok-register-main 成熟方案，增加 userAgentData + Canvas noise
 * ★ 每个 frame 独立随机偏移，避免模式检测
 * 
 * 部署方式：Chrome MV3 扩展，world: "MAIN" + all_frames: true + run_at: "document_start"
 */

(function() {
    'use strict';

    // 防重入
    if (window.__TURNSTILE_BYPASS_V4__) return;
    window.__TURNSTILE_BYPASS_V4__ = true;

    // ============================================================
    // 每个 frame 独立随机偏移量
    // ============================================================
    var _offX = Math.floor(Math.random() * 401) + 80;   // 80~480
    var _offY = Math.floor(Math.random() * 201) + 60;   // 60~260

    var _dp = function(obj, prop, getter) {
        try {
            Object.defineProperty(obj, prop, {
                get: getter,
                configurable: true,
                enumerable: true
            });
        } catch(e) {}
    };

    // ============================================================
    // L1: MouseEvent screenX/screenY — 核心反检测
    // ============================================================
    _dp(MouseEvent.prototype, 'screenX', function() {
        return (this.clientX || 0) + _offX + Math.floor(Math.random() * 5 - 2);
    });
    _dp(MouseEvent.prototype, 'screenY', function() {
        return (this.clientY || 0) + _offY + Math.floor(Math.random() * 5 - 2);
    });
    _dp(MouseEvent.prototype, 'x', function() {
        return this.clientX || 0;
    });
    _dp(MouseEvent.prototype, 'y', function() {
        return this.clientY || 0;
    });

    // PointerEvent（Turnstile 也使用）
    if (typeof PointerEvent !== 'undefined') {
        _dp(PointerEvent.prototype, 'screenX', function() {
            return (this.clientX || 0) + _offX + Math.floor(Math.random() * 5 - 2);
        });
        _dp(PointerEvent.prototype, 'screenY', function() {
            return (this.clientY || 0) + _offY + Math.floor(Math.random() * 5 - 2);
        });
    }

    // ============================================================
    // L2: window 尺寸伪装（仅顶层窗口）
    // ============================================================
    try {
        if (window.top === window) {
            _dp(window, 'outerWidth', function() {
                return window.innerWidth + 16 + Math.floor(Math.random() * 2);
            });
            _dp(window, 'outerHeight', function() {
                return window.innerHeight + 80 + Math.floor(Math.random() * 5);
            });
        }
    } catch(e) {}

    // ============================================================
    // L3: navigator 属性伪装
    // ============================================================
    // webdriver — 最基本
    try {
        _dp(navigator, 'webdriver', function() { return undefined; });
        var nd = Object.getOwnPropertyDescriptor(Navigator.prototype, 'webdriver');
        if (nd) {
            Object.defineProperty(Navigator.prototype, 'webdriver', {
                get: function() { return false; },
                configurable: true
            });
        }
    } catch(e) {}

    // languages
    try {
        _dp(navigator, 'languages', function() {
            return ['zh-CN', 'zh', 'en-US', 'en'];
        });
    } catch(e) {}
    try {
        _dp(navigator, 'language', function() { return 'zh-CN'; });
    } catch(e) {}

    // ★ userAgentData（2026年 Cloudflare 头号检测向量）
    // grok-register-main 采用此方案
    try {
        _dp(navigator, 'userAgentData', function() {
            var brands = [
                { brand: 'Google Chrome', version: '131' },
                { brand: 'Chromium', version: '131' },
                { brand: 'Not_A Brand', version: '24' }
            ];
            return {
                brands: brands,
                mobile: false,
                platform: 'Windows',
                getHighEntropyValues: async function() {
                    return {
                        platform: 'Windows',
                        platformVersion: '10.0.0',
                        architecture: 'x86',
                        uaFullVersion: '131.0.6778.265',
                        bitness: '64'
                    };
                },
                toJSON: function() {
                    return { brands: brands, mobile: false, platform: 'Windows' };
                }
            };
        });
    } catch(e) {}

    // hardware
    try {
        _dp(navigator, 'hardwareConcurrency', function() { return 8; });
    } catch(e) {}
    try {
        _dp(navigator, 'deviceMemory', function() { return 8; });
    } catch(e) {}

    // ============================================================
    // L4: plugins 补全（无头浏览器 plugins.length === 0）
    // ============================================================
    try {
        _dp(navigator, 'plugins', function() {
            var arr = [
                { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format', length: 1 },
                { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '', length: 1 },
                { name: 'Native Client', filename: 'internal-nacl-plugin', description: '', length: 1 }
            ];
            arr.item = function(i) { return this[i] || null; };
            arr.namedItem = function(name) {
                for (var i = 0; i < this.length; i++) {
                    if (this[i].name === name) return this[i];
                }
                return null;
            };
            arr.refresh = function() {};
            arr[Symbol.iterator] = function*() {
                for (var i = 0; i < this.length; i++) yield this[i];
            };
            Object.setPrototypeOf(arr, PluginArray.prototype);
            return arr;
        });
    } catch(e) {}

    // ============================================================
    // L5: chrome.runtime 补全
    // ============================================================
    try {
        if (!window.chrome) window.chrome = {};
        if (!window.chrome.runtime) {
            window.chrome.runtime = {
                connect: function() {
                    return {
                        onMessage: { addListener: function(){}, removeListener: function(){} },
                        postMessage: function(){},
                        disconnect: function(){}
                    };
                },
                sendMessage: function() {},
                onMessage: { addListener: function(){}, removeListener: function(){} },
                onConnect: { addListener: function(){} }
            };
        }
    } catch(e) {}

    // ============================================================
    // L6: 隐藏自动化痕迹
    // ============================================================
    // 删除 cdc_ 属性
    for (var key in window) {
        if (/^cdc_/.test(key)) {
            try { delete window[key]; } catch(e) {}
        }
    }

    // ============================================================
    // L7: Canvas 指纹噪声
    // ============================================================
    try {
        var _td = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function() {
            var ctx = this.getContext('2d');
            if (ctx) {
                var d = ctx.getImageData(0, 0, 1, 1);
                if (d && d.data) {
                    d.data[0] = d.data[0] ^ (Math.random() > 0.5 ? 1 : 0);
                }
            }
            return _td.apply(this, arguments);
        };
    } catch(e) {}

    // ============================================================
    // L8: WebGL 指纹噪声 (extra)
    // ============================================================
    try {
        var _gcp = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(p) {
            if (p === 37445) return 'Intel Inc.';  // UNMASKED_VENDOR
            if (p === 37446) return 'Intel Iris OpenGL Engine'; // UNMASKED_RENDERER
            return _gcp.call(this, p);
        };
    } catch(e) {}

    // ============================================================
    // L9: 权限查询拦截
    // ============================================================
    try {
        var _pq = window.navigator.permissions.query;
        window.navigator.permissions.query = function(p) {
            if (p.name === 'notifications') {
                return Promise.resolve({ state: Notification.permission });
            }
            return _pq.call(this, p);
        };
    } catch(e) {}

    // ============================================================
    // L10: Shadow DOM 跟踪（any-auto-register 方案）
    // ============================================================
    try {
        var _as = Element.prototype.attachShadow;
        Element.prototype.attachShadow = function(init) {
            var shadow = _as.call(this, init);
            if (init && init.mode === 'closed') {
                window.__lastClosedShadowRoot = shadow;
            }
            return shadow;
        };
    } catch(e) {}

    // 日志（DEBUG: 仅在 non-Turnstile iframe 或顶层窗口打印）
    var _frameUrl = (function() {
        try { return window.location.href; } catch(e) { return ''; }
    })();
    if (window.top === window || !(/turnstile|cloudflare|challenges/i.test(_frameUrl))) {
        console.log('[TurnstileBypass v4] ✅ All patches active in: ' + _frameUrl.substring(0, 60));
    }
})();
