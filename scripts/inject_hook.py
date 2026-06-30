"""把hook代码写入页面的localStorage，播放器cli eval再读取执行"""
import json

# 关闭modal+hook剪贴板
hook_js = r"""(
function(){
    var ms=document.querySelectorAll('.modal');
    for(var i=0;i<ms.length;i++){ms[i].classList.remove('show');ms[i].style.display='none'}
    var bk=document.querySelectorAll('.modal-backdrop');
    for(var i=0;i<bk.length;i++)bk[i].remove();
    document.body.classList.remove('modal-open');
    document.body.style.overflow='';
    window.__cap=null;
    var ow=navigator.clipboard.writeText;
    navigator.clipboard.writeText=function(t){window.__cap=t;return ow.call(navigator.clipboard,t)}
    document.addEventListener('copy',function(e){if(e.clipboardData)window.__cap=e.clipboardData.getData('text')})
    return 'hooked'
})()"""

# click V2RayN
click_v2ray = r"""(
function(){
    var btns=document.querySelectorAll('button');
    for(var i=0;i<btns.length;i++){
        if(btns[i].textContent.indexOf('V2RayN')>=0){btns[i].click();return'clicked v2ray'}
    }
    return'no v2ray'
})()"""

# click Clash 订阅
click_clash = r"""(
function(){
    var btns=document.querySelectorAll('button');
    for(var i=0;i<btns.length;i++){
        if(btns[i].textContent.indexOf('Clash')>=0&&btns[i].textContent.indexOf('订阅')>=0){btns[i].click();return'clicked clash'}
    }
    return'no clash'
})()"""

# click 复制订阅地址
click_copy = r"""(
function(){
    var all=document.querySelectorAll('*');
    for(var i=0;i<all.length;i++){
        if(all[i].childNodes.length===1&&all[i].textContent.trim()==='复制订阅地址'){all[i].click();return'clicked copy'}
    }
    return'not found'
})()"""

# API call
api_js = r"""(
async function(){
    try{var r=await fetch('/api/v1/user/getSubscribe');if(r.ok){var d=await r.json();return JSON.stringify(d)}}catch(e){}
    try{var r=await fetch('/api/user/getSubscribe');if(r.ok){var d=await r.json();return JSON.stringify(d)}}catch(e){}
    return'failed'
})()"""

# 查找所有链接
links_js = r"""(
function(){
    var r=[];
    document.querySelectorAll('a[href]').forEach(function(a){if(a.href.indexOf('sub')>=0||a.href.indexOf('token')>=0)r.push(a.href)});
    return r
})()"""

# 打印 playwright-cli eval 命令
print("# 粘贴以下命令到终端，逐条执行:")
print()
print("# 1. Hook剪贴板+清除modal")
print(f'playwright-cli eval "eval(JSON.parse({json.dumps(json.dumps(hook_js))}))"')
print()
print("# 2a. 点击V2RayN按钮")
print(f'playwright-cli eval "eval(JSON.parse({json.dumps(json.dumps(click_v2ray))})); window.__cap"')
print()
print("# 2b. 或者点Clash订阅")
print(f'playwright-cli eval "eval(JSON.parse({json.dumps(json.dumps(click_clash))})); window.__cap"')
print()
print("# 2c. 或者点复制订阅地址")
print(f'playwright-cli eval "eval(JSON.parse({json.dumps(json.dumps(click_copy))})); window.__cap"')
print()
print("# 3. 查API结果")
print(f'playwright-cli eval "eval(JSON.parse({json.dumps(json.dumps(api_js))}))"')
print()
print("# 4. 查链接")
print(f'playwright-cli eval "eval(JSON.parse({json.dumps(json.dumps(links_js))}))"')
