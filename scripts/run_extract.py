"""直接执行订阅提取"""
import json, subprocess, sys, os

os.chdir(r"E:\API获取工具")

def run_eval(js_code):
    """运行 playwright-cli eval"""
    cmd = f'playwright-cli eval "{js_code}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    output = result.stdout + result.stderr
    # 提取 ### Result 后面的内容
    if '### Result' in output:
        output = output.split('### Result', 1)[1].strip()
    return output

# Hook代码 - 关闭modal+hook剪贴板
hook = """eval(JSON.parse("\\"(\\\\nfunction(){\\\\n    var ms=document.querySelectorAll('.modal');\\\\n    for(var i=0;i<ms.length;i++){ms[i].classList.remove('show');ms[i].style.display='none'}\\\\n    var bk=document.querySelectorAll('.modal-backdrop');\\\\n    for(var i=0;i<bk.length;i++)bk[i].remove();\\\\n    document.body.classList.remove('modal-open');\\\\n    document.body.style.overflow='';\\\\n    window.__cap=null;\\\\n    var ow=navigator.clipboard.writeText;\\\\n    navigator.clipboard.writeText=function(t){window.__cap=t;return ow.call(navigator.clipboard,t)}\\\\n    document.addEventListener('copy',function(e){if(e.clipboardData)window.__cap=e.clipboardData.getData('text')})\\\\n    return 'hooked'\\\\n})()\\""))"""

# 点击V2RayN订阅按钮
click_v2ray = """eval(JSON.parse("\\"(\\\\nfunction(){\\\\n    var btns=document.querySelectorAll('button');\\\\n    for(var i=0;i<btns.length;i++){\\\\n        if(btns[i].textContent.indexOf('V2RayN')>=0){btns[i].click();return'clicked'}\\\\n    }\\\\n    return'not found'\\\\n})()\\""))"""

# 点Clash订阅 
click_clash = """eval(JSON.parse("\\"(\\\\nfunction(){\\\\n    var btns=document.querySelectorAll('button');\\\\n    for(var i=0;i<btns.length;i++){\\\\n        var t=btns[i].textContent;\\\\n        if(t.indexOf('Clash')>=0&&t.indexOf('\\\\u8ba2\\\\u9605')>=0){btns[i].click();return'clicked'}\\\\n    }\\\\n    return'not found'\\\\n})()\\""))"""

get_cap = "window.__cap"

api_call = """eval(JSON.parse("\\"(\\\\nasync function(){\\\\n    try{var r=await fetch('/api/v1/user/getSubscribe');if(r.ok){var d=await r.json();return JSON.stringify(d)}}catch(e){}\\\\n    try{var r=await fetch('/api/user/getSubscribe');if(r.ok){var d=await r.json();return JSON.stringify(d)}}catch(e){}\\\\n    return'failed'\\\\n})()\\""))"""

find_links = """eval(JSON.parse("\\"(\\\\nfunction(){\\\\n    var r=[];\\\\n    document.querySelectorAll('a[href]').forEach(function(a){if(a.href.indexOf('sub')>=0||a.href.indexOf('token')>=0)r.push(a.href)});\\\\n    return r\\\\n})()\\""))"""

print("=== 疾风云订阅提取 ===")
print("1. Hook+关闭modal:", run_eval(hook)[:200])

# 点V2RayN按钮
r = run_eval(click_v2ray)
print("2. 点V2RayN:", r[:100])

# 检查剪贴板
cap = run_eval(get_cap)
print("3. 剪贴板:", cap[:200] if cap else "null/undefined")

if not cap or cap == 'null':
    # 点Clash
    r = run_eval(click_clash)
    print("4. 点Clash:", r[:100])
    import time; time.sleep(1)
    cap = run_eval(get_cap)
    print("5. 剪贴板:", cap[:200] if cap else "null/undefined")

# API
r = run_eval(api_call)
print("6. API结果:", r[:300])

# 链接
r = run_eval(find_links)
print("7. 链接:", r[:300])

if cap and cap != 'null' and len(cap) > 5:
    print(f"\n>>> 疾风云订阅链接: {cap}")
else:
    print("\n>>> 未捕获到订阅链接，需要其他方法")
