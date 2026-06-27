"""连接到已打开的宝可梦浏览器页面，拦截clipboard获取订阅链接"""
import asyncio, json, subprocess, time, yaml, os

# 先读取playwright-cli的ws连接信息
# playwright-cli使用固定的browser实例
# 我们通过CDP连接

# 方法：用playwright-cli eval注入clipboard拦截，然后重新点击按钮
# 直接在playwright-cli里执行

# 方案：写一个独立的script，用playwright的connectOverCDP
CLI_DIR = r"E:\API获取工具\.playwright-cli"

# 查看CDP endpoint
# playwright-cli打开的浏览器会有CDP端口
# 找最新的endpoint

# 更简单的方法：直接用playwright-cli open复用当前页面
# 先注入拦截代码

# 最简单：用powershell调用playwright cli的组合命令
script = """
// 拦截clipboard
navigator.clipboard.writeText = function(text) {
    window.__captured_clipboard = text;
    console.log('CLIPBOARD_CAPTURED:', text);
    return Promise.resolve();
};

// 找到复制订阅链接按钮并点击
var btns = document.querySelectorAll('button');
for (var b of btns) {
    if (b.textContent.includes('复制通用订阅链接')) {
        b.click();
        break;
    }
}

// 等待100ms后返回结果
setTimeout(function() {
    console.log('RESULT:', window.__captured_clipboard);
}, 500);

window.__captured_clipboard;
"""

with open(os.path.join(CLI_DIR, "inject.js"), 'w', encoding='utf-8') as f:
    f.write(script)

print(f"Script written to {CLI_DIR}/inject.js")
print("Now run: playwright-cli eval with the script content")
