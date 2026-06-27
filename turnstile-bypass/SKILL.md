# Turnstile Bypass Skill

## 自动触发关键词
当用户提到以下任何关键词时，自动加载此技能：
- **Turnstile** / **turnstile** / **cf-turnstile**
- **Cloudflare验证** / **cloudflare验证** / **CF验证** / **CF挑战**
- **人机验证** / **人机识别** / **机器人验证**
- **Cloudflare拦截** / **CF拦截** / **被Cloudflare挡住**
- **Turnstyle** (常见拼写错误)
- **点击验证** / **验证框** / **checkbox验证**

## 使用场景
1. 注册机场时遇到Cloudflare Turnstile验证
2. 登录页面被Turnstile拦截
3. 任何需要过Cloudflare人机验证的自动化场景

## 技术方案（三层）

### 第1层：Chrome扩展（最强，需提前安装）
```
扩展路径: turnstile-bypass/
安装方法: Chrome → 扩展程序 → 加载已解压的扩展程序 → 选择turnstile-bypass文件夹
Playwright加载: launch_with_turnstile_bypass()
```
10层防御：MouseEvent/PointerEvent screenX/Y劫持, window伪装, navigator.webdriver, 
userAgentData, plugins补全, chrome.runtime, Canvas噪声, WebGL, permissions, Shadow DOM

### 第2层：playwright-cli eval注入（最灵活）
```bash
# 复制 turnstile_patch.py 中的 TURNSTILE_PATCH_SCRIPT 内容
playwright-cli eval "(完整patch_script)"
```

### 第3层：Python Playwright API（编程使用）
```python
from turnstile_patch import inject_turnstile_patch_sync, click_turnstile_sync, bypass_turnstile_sync

inject_turnstile_patch_sync(page)  # 注入10层防御
click_turnstile_sync(page)         # 主动点击checkbox
bypass_turnstile_sync(page)       # 一站式绕过
```

## 核心原理
Cloudflare Turnstile检测 `MouseEvent.screenX === clientX` 判定机器人。
真实用户 screenX = clientX + 窗口左边距(80~400px)。
补丁给 screenX/Y 加上随机偏移量 + jitter 模拟真实用户。
