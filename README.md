# 机场VPN注册机 — 全自动批量注册+订阅链接提取

## 项目概述

自动化注册机场VPN账号，提取真实可导入Clash的订阅链接。已累计注册12个机场，3个确认有真实免费节点。

## 技术栈

- **浏览器自动化**: playwright-cli v0.1.14 + Edge Chromium（穿GFW）
- **验证码读取**: Microsoft Graph API（Outlook/Hotmail邮箱）
- **订阅链接提取**: 多种方式（见下文"各系统订阅链接获取方法"）

## 快速开始

```bash
# 1. 杀死残留浏览器进程
taskkill /f /im msedge.exe

# 2. 打开机场注册页
cd "E:\API获取工具"
playwright-cli open <机场URL> --browser=msedge

# 3. 分析页面结构
playwright-cli snapshot

# 4. 填表注册（完整流程见下方"注册流程"）
```

## 注册流程（已验证可行）

### 第一步：分析表单类型

```
playwright-cli snapshot   # 看有无域名下拉框/验证码/完整邮箱
```

两种常见表单：
- **A. 域名下拉框式**：邮箱前缀 + 域名下拉框（需选@outlook.com）
- **B. 完整邮箱式**：一个输入框直接填完整邮箱（如奈云、肥猫云）

### 第二步：A型 — 域名下拉框选中outlook

```bash
# JS选中+触发Vue响应（关键！单纯设sel.value不够）
playwright-cli eval "(sel=document.querySelector('select'), sel.value='outlook.com', sel.dispatchEvent(new Event('change',{bubbles:true})), sel.dispatchEvent(new InputEvent('input',{bubbles:true})))"
```

### 第三步：填表

```bash
playwright-cli fill <邮箱ref> "邮箱前缀"         # A型只填前缀
playwright-cli fill <邮箱ref> "xxx@outlook.com"  # B型填完整
playwright-cli fill <密码ref> "VpnTest2026!"
playwright-cli fill <确认密码ref> "VpnTest2026!"
```

### 第四步：发送验证码

```bash
playwright-cli click <发送按钮ref>
```

### 第五步：轮询Outlook收验证码

```bash
cd scripts
python -c "from outlook_code_reader import load_all_tokens,wait_for_code;email='xxx@outlook.com';ti=load_all_tokens().get(email.lower());code,err=wait_for_code(email,ti,timeout=60,interval=2);print(f'CODE:{code}')"
```

### 第六步：填验证码 + 注册

```bash
playwright-cli fill <验证码ref> "验证码"
playwright-cli click <注册按钮ref>
```

### 第七步：登录Dashboard提取真实订阅链接

```bash
# 登录
playwright-cli fill <邮箱ref> "xxx@outlook.com"
playwright-cli fill <密码ref> "VpnTest2026!"
playwright-cli click <登录按钮ref>

# 提取订阅链接（关键！不能用UUID拼装）
playwright-cli eval "(raw=localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN'), parsed=JSON.parse(raw), tok=parsed.value, fetch('/api/v1/user/getSubscribe',{headers:{'Authorization':tok}}).then(function(r){return r.text()}).then(function(t){window.__sub=t}), 'ok')"

# 读取真实链接
playwright-cli eval "(r=window.__sub, idx=r.indexOf('subscribe_url'), r.substring(idx,idx+130))"
```

## 各系统订阅链接获取方法（重要！每个都不同）

### 1. V2Board系统（FlyBit/99吧/稳连云/大象/TaiShan）
- auth token在localStorage: `VUE_NAIVE_ACCESS_TOKEN`（JSON格式取value）
- 调用 `/api/v1/user/getSubscribe`
- 返回的 `subscribe_url` 域名和面板域名不同！
- 实际域名示例：flybit.vip → s.fb.22na.cn, 99ba.fyi → sealosgzg.site

### 2. SSPANEL系统（网际快车/三毛）
- 登录后进入 `/#/user_info`
- 页面显示"订阅密钥"（bind token）
- 订阅URL格式：`{面板域名}/link/{token}?sub=1`

### 3. Mala-Pro系统（宝可梦）
- localStorage直接存 `subscribe_url`

### 4. 奈云定制系统
- auth在localStorage: `naiun.auth.header`
- 订阅token: `naiun.subscribe.token`
- 调用 `/api/v1/user/getSubscribe`
- 真实域名：c0d97821eafa5.nydy.cc（不是v2ny.com）

### 5. 传统Web系统（肥猫云）
- 无localStorage token
- 服务端渲染，订阅URL在HTML中或需特定页面操作

## 关键教训

1. **绝不能用UUID拼订阅链接** — 每个机场的真实订阅域名都不同
2. **域名下拉框必须dispatch change+input事件** — Vue不认单纯的sel.value改动
3. **playwright-cli eval语法限制** — 只能用逗号操作符(a=1,b=2,c)，不能用var/function/for/if/||/?
4. **绝大多数机场拒收@outlook.com** — 域名下拉框只含@qq.com/@163.com/@gmail.com
5. **非Microsoft邮箱是解锁30+机场的钥匙**

## 目录结构

```
01-机场VPN注册机/
├── scripts/
│   ├── outlook_code_reader.py    # Outlook验证码读取(Graph API)
│   ├── universal_register.py     # SSPANEL/hidexx通用注册引擎
│   ├── free_sub_collector.py     # GitHub免费订阅收集器
│   ├── scan_outlook_support.py   # 批量扫描机场outlook支持
│   ├── batch_register_v4.py      # 批量注册引擎
│   └── airport_discovery_20260628.md  # 机场发现报告
├── register_results/
│   ├── live_register_20260628.jsonl   # 实时注册结果
│   └── batch_register_results.jsonl   # 批量注册结果
├── 可用订阅链接_20260628.md           # 最终可用订阅链接
├── 新会话接续词.md                   # 跨会话续接
└── README.md                          # 本文件
```

## 注册成果（12个机场）

| # | 机场 | 免费套餐 | 订阅有节点 |
|---|------|----------|-----------|
| 1 | 稳连云 | 无 | ❌ |
| 2 | 大象网络 | 无 | ❌ |
| 3 | 宝可梦 | 需兑换码 | ❌ |
| 4 | 三毛/网际快车 | 无 | ❌ |
| 5 | 魔戒 | 无 | ❌ |
| 6 | aiguobit | 公共SSR | ✅ |
| 7 | TaiShan Net | 无 | ❌ |
| 8 | **奈云v2ny** | 2GB/1天 | ✅ 8节点 |
| 9 | **99吧** | 1GB/24h | ✅ |
| 10 | SSLAR | 待激活 | ❌ |
| 11 | **FLYBIT** | 2GB/24h | ✅ |
| 12 | 肥猫云 | Free/0MB | ❌ |

## 密码统一
**VpnTest2026!**
