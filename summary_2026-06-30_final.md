# 机场VPN注册机 — 2026-06-30 凌晨 最终战果

## ✅ 本轮新获取的有效订阅链接（4个）

| 机场 | 订阅链接 | 节点 | 流量 | 邮箱 |
|------|----------|------|------|------|
| **v2ny/奈云** | `https://c0d97821eafa5.nydy.cc/sleep/96c0e07c0c503cb31c949c34e1705c8c` | 22 | 2GB/1天 | averymorga4g0jfbs6q2up@outlook.com |
| **FLYBIT** | `https://s.fb.22na.cn/api/v1/ss/9728287fbc6d93ba75fcbe668bac0056` | 74 | 2GB测试 | colemanbroovp9xyduj92hubhn@outlook.com |
| **99吧** | `https://ycexbktkoctx.sealosgzg.site/api/sub/27402f01d057a6bea4f8cef3fca2fa0e` | 48 | 1GB/24h | aiden533ju9y2wx2bjmd@outlook.com |
| **cd520** | `https://cd520.xyz/api/v1/client/subscribe?token=344152b3febea62d68208b5696615036` | ? | 5GB/3天 | hendricktamm95v80awzaxli@outlook.com |

## ✅ 验证通过的历史订阅（1个）
| **v2ny/奈云** | `https://c0d97821eafa5.nydy.cc/sleep/35348eeac78327d3215b48e4a8075dfc` | 22 | 2GB |

## ❌ 确认全死
- v2ny_old2 (80e835): 返回空
- FLYBIT_old (b863fc): 返回空
- 99ba_old (4927953): 返回空
- COCODUCK (037e8dd): 500错误
- cd520_old (cdc502.online): SSL EOF
- TANZCLOUD/FSCloud/iKuuu/SSLAR/大哥云: 全部不可用

## 关键逆向经验
1. NaiveUI面板登录页多数是**完整邮箱输入**（无select下拉）
2. 注册页才用前缀+select后缀
3. 按钮文字有"登入"和"登录"两种
4. localStorage key统一是 `VUE_NAIVE_ACCESS_TOKEN`
5. cd520 v1.7.1自定义面板ant-modal拦截导航
6. COCODUCK是WordPress站，不是V2Board面板
