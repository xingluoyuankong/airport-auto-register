# 机场VPN注册机 — 2026-06-30 凌晨 验证轮次总结

## 已验证可用的订阅链接（4个新增）

| # | 机场 | 订阅链接 | 节点 | 来源 |
|---|------|----------|------|------|
| 1 | **v2ny/奈云** | `https://c0d97821eafa5.nydy.cc/sleep/96c0e07c0c503cb31c949c34e1705c8c` | 22节点 | 本会话新获取(1天2GB) |
| 2 | **FLYBIT** | `https://s.fb.22na.cn/api/v1/ss/9728287fbc6d93ba75fcbe668bac0056` | 74节点 | 本会话新获取(2GB测试) |
| 3 | **99吧** | `https://ycexbktkoctx.sealosgzg.site/api/sub/27402f01d057a6bea4f8cef3fca2fa0e` | 48节点 | 本会话新获取(1GB/24h) |
| 4 | **v2ny/奈云** | `https://c0d97821eafa5.nydy.cc/sleep/35348eeac78327d3215b48e4a8075dfc` | 22节点 | register_results历史 |

## 已确认失效

| 机场 | 原因 |
|------|------|
| v2ny_old2 (80e835) | 返回空(过期) |
| FLYBIT_old (b863fc) | 返回空(过期) |
| 99ba_old (4927953) | 返回空(过期) |
| COCODUCK (037e8dd) | 500错误(服务器问题) |
| cd520 (cdc502.online) | SSL EOF(域名已死) |
| TANZCLOUD | 密码错误，账号不存在 |
| iKuuu | 域名ikuu.win DNS解析失败 |
| SSLAR | 无有效套餐，无优惠码入口 |
| 大哥云 | SPA可登录但/user路由404 |
| FSCloud | 需Gmail验证码无法获取 |

## 关键逆向发现

### 登录页表单模式总结
- **99ba**: 注册=前缀+下拉选后缀, 登录=完整邮箱输入, 按钮"登入"
- **FLYBIT**: 注册=前缀+select后缀, 登录=完整邮箱输入(无select), 按钮"登入"
- **v2ny**: 注册=完整邮箱+id(#reg-email), 登录=id(#login-email)+#login-password, 按钮"登录"
- **cd520**: 注册=前缀+select后缀, 登录=完整邮箱输入, 按钮"登入", 仪表盘有ant-modal弹窗
- **COCODUCK**: WordPress站点，非V2Board/NaiveUI面板, #/login路由不加载登录表单

### localStorage Token Key
- NaiveUI面板: `VUE_NAIVE_ACCESS_TOKEN` (value含Bearer+token)
- 自定义面板(cd520 v1.7.1): 不同key

## 下一步
1. 修复cd520 ant-modal拦截 → 提取订阅
2. COCODUCK重新逆向(WordPress)
3. 继续搜索新机场
