# 快速批量扫描所有剩余机场
$ErrorActionPreference = "Continue"
cd "E:\API获取工具"

$airports = @(
    @("NOW加速", "https://nowjiasu.com"),
    @("瞬云", "https://shunyun.xyz"),
    @("仙路湾", "https://xianluwan.com"),
    @("山水云", "https://shanshuiyun.com"),
    @("NICE加速", "https://nicejiasu.com"),
    @("锦云", "https://jinyun.pro"),
    @("寰宇云", "https://huanyuyun.com"),
    @("秒秒云", "https://miaomiaoyun.com"),
    @("大哥云", "https://dageyun.com"),
    @("SKYLUMO", "https://skylumo.com"),
    @("宇宙云", "https://yuzhouyun.com"),
    @("光年梯", "https://guangnianti.com"),
    @("闪狐云", "https://shanhuyun.com"),
    @("FSCloud", "https://dash.fscloud.app"),
    @("奈云v2ny", "https://www.v2ny.com"),
    @("雨燕云", "https://yuyan.online"),
    @("逗猫", "https://douchat.top"),
    @("泰山Net", "https://www.taishan.pro"),
    @("一元机场old", "https://xn--4gq62f52gdss.top"),
    @("极光加速", "https://jiguang.pro"),
    @("besnow", "https://besnow.me"),
    @("aiguobit", "https://a.aiguobit.com"),
    @("hidexx", "https://a.hidexx.com"),
    @("69云", "https://69yun69.com"),
    @("淘气兔面板", "https://vip.xn--h5qy56dzhb.vip/#/register"),
    @("COCODUCK", "https://www.cocoduck.live")
)

taskkill /f /im chromium.exe 2>$null
Start-Sleep -Seconds 1

Write-Host "Opening browser..."
playwright-cli open "https://wenlianyun.com" --browser=msedge 2>&1 | Out-Null
Start-Sleep -Seconds 2

foreach ($a in $airports) {
    $name = $a[0]
    $url = $a[1]
    Write-Host "`n[$name] $url" -ForegroundColor Yellow
    
    try {
        $output = playwright-cli goto $url 2>&1 | Out-String
        Start-Sleep -Seconds 3
        
        # Check current URL and title
        $snap = playwright-cli eval "document.title + '|||' + window.location.href + '|||' + (document.body.innerText||'').substring(0,300).replace(/\n/g,' ')" 2>&1 | Out-String
        
        if ($snap -match '"([^"]*)\|\|\|([^"]*)\|\|\|([^"]*)"') {
            $title = $Matches[1]
            $finalUrl = $Matches[2]
            $body = $Matches[3]
        } else {
            $title = "N/A"
            $finalUrl = $url
            $body = ""
        }
        
        # 判断状态
        $dead = $body -match "domain.*sale|域名.*出售|parked|godaddy|afternic|buy this domain|域名已过期"
        $reg = $body -match "注册|register|sign.?up|登录"
        $captcha = $body -match "recaptcha|captcha|turnstile|人机"
        
        if ($dead) {
            Write-Host "  DEAD - 域名出售/已死" -ForegroundColor Red
        } elseif ($reg) {
            Write-Host "  ONLINE - 有注册入口 | $title" -ForegroundColor Green
            if ($captcha) { Write-Host "  [!] 有验证码 (captcha/recaptcha)" -ForegroundColor DarkYellow }
        } else {
            Write-Host "  ONLINE - $title" -ForegroundColor Cyan
        }
        Write-Host "  URL: $finalUrl"
    } catch {
        Write-Host "  ERROR: $_" -ForegroundColor Red
    }
}

playwright-cli close 2>&1 | Out-Null
Write-Host "`nDONE"
