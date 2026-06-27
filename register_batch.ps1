[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}
$proxy = New-Object System.Net.WebProxy("http://127.0.0.1:7897")
$ua = "Mozilla/5.0 Chrome/131.0.0.0"

$emails = @(
    @{e="sanchezquinncu3w1kkhtuc74@outlook.com";p="3pKPx5!rE9%9nJDLJC"},
    @{e="hendricktamm95v80awzaxli@outlook.com";p='@^NdxP5KN#s9G2Hqu0!'},
    @{e="parker738403dcp34kfdl6j@outlook.com";p="oo^5v=Q%&RU$pdDrax"}
)

$airports = @(
    @{n="Speedy"; u="https://cloud.speedypro.xyz/api/v1/passport/auth/register"},
    @{n="FSCloud"; u="https://dash.fscloud.app/api/v1/passport/auth/register"},
    @{n="TaishanNet"; u="https://www.taishan.pro/api/v1/passport/auth/register"},
    @{n="DouMao"; u="https://doucat.top/api/v1/passport/auth/register"},
    @{n="YuYan"; u="https://yuyan.online/api/v1/passport/auth/register"},
    @{n="NaiYun"; u="https://www.v2ny.com/api/v1/passport/auth/register"},
    @{n="YiYuan"; u="https://xn--4gq62f52gdss.top/api/v1/passport/auth/register"}
)

$outDir = "E:\API获取工具\自动集成免费代理服务\01-机场VPN注册机\register_results"
New-Item $outDir -ItemType Directory -Force | Out-Null

function Do-Post($url, $jsonStr) {
    $bytes = [Text.Encoding]::UTF8.GetBytes($jsonStr)
    $req = [Net.WebRequest]::Create($url)
    $req.Proxy = $proxy
    $req.Method = "POST"
    $req.ContentType = "application/json"
    $req.Timeout = 15000
    $req.UserAgent = $ua
    $req.ContentLength = $bytes.Length
    try {
        $rs = $req.GetRequestStream()
        $rs.Write($bytes, 0, $bytes.Length)
        $rs.Close()
        $resp = $req.GetResponse()
        $sr = [IO.StreamReader]::new($resp.GetResponseStream())
        $body = $sr.ReadToEnd()
        $sr.Close(); $resp.Close()
        return @{ok=$true; code=200; body=$body}
    } catch [Net.WebException] {
        $code = 0; $body = ""
        if ($_.Exception.Response) {
            $code = $_.Exception.Response.StatusCode.value__
            try {
                $sr2 = [IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
                $body = $sr2.ReadToEnd(); $sr2.Close()
            } catch { $body = "stream_err" }
        } else { $body = $_.Exception.Message }
        return @{ok=$false; code=$code; body=$body}
    } catch { return @{ok=$false; code=0; body=$_.Exception.Message} }
}

$results = @()
$subLinks = @()

Write-Host "=== START: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="

foreach ($ap in $airports) {
    Write-Host ""
    Write-Host "[$($ap.n)] $($ap.u.Substring(0,[Math]::Min(50,$ap.u.Length)))" -ForegroundColor Yellow

    foreach ($u in $emails) {
        Write-Host "  $($u.e.Substring(0,28))... " -NoNewline

        # v1: minimal
        $p1 = "{`"email`":`"$($u.e)`",`"password`":`"$($u.p)`"}"
        $r1 = Do-Post $ap.u $p1
        $s1 = $r1.body.Substring(0, [Math]::Min(150, $r1.body.Length))

        if ($r1.ok) {
            Write-Host "OK(200) $s1" -ForegroundColor Green
            $results += @{a=$ap.n; e=$u.e; s="ok"; t=$r1.body}
            # extract token & get sub
            $token = ""
            try { $d = $r1.body | ConvertFrom-Json; $token = $d.data.token } catch {}
            if ($token) {
                $base = ([uri]$ap.u).GetLeftPart('Authority')
                $subUrl = "$base/api/v1/user/getSubscribe"
                try {
                    $sr = [Net.WebRequest]::Create($subUrl)
                    $sr.Proxy = $proxy; $sr.Method = "GET"; $sr.Timeout = 8000; $sr.UserAgent = $ua
                    $sr.Headers.Add("Authorization", "Bearer $token")
                    $srp = $sr.GetResponse(); $srs = [IO.StreamReader]::new($srp.GetResponseStream())
                    $sb = $srs.ReadToEnd(); $srs.Close(); $srp.Close()
                    $sd = $sb | ConvertFrom-Json -ErrorAction SilentlyContinue
                    if ($sd.data -is [string] -and $sd.data -like "*://*") {
                        $subLinks += "$($ap.n) | $($u.e) | $($sd.data)"
                        Write-Host "    SUB: $($sd.data)" -ForegroundColor Green
                    } elseif ($sd.data.subscribe_url -and $sd.data.subscribe_url -like "*://*") {
                        $subLinks += "$($ap.n) | $($u.e) | $($sd.data.subscribe_url)"
                        Write-Host "    SUB: $($sd.data.subscribe_url)" -ForegroundColor Green
                    }
                } catch {}
            }
            continue
        }

        if ($r1.body -match "email_code|yan_zheng|verify|required|not empty|can not be empty") {
            # v2: with empty email_code
            $p2 = "{`"email`":`"$($u.e)`",`"password`":`"$($u.p)`",`"email_code`":`"`",`"invite_code`":`"`",`"recaptcha_data`":`"`"}"
            $r2 = Do-Post $ap.u $p2
            $s2 = $r2.body.Substring(0, [Math]::Min(150, $r2.body.Length))

            if ($r2.ok) {
                Write-Host "OK-v2(200) $s2" -ForegroundColor Green
                $results += @{a=$ap.n; e=$u.e; s="ok"; t=$r2.body}
                continue
            } elseif ($r2.body -match "wrong|incorrect|error|invalid|cuo_wu") {
                # v3: need real email code
                Write-Host "NEED_REAL_CODE $s2" -ForegroundColor DarkYellow
                $results += @{a=$ap.n; e=$u.e; s="need_code"; c=$r2.code}
            } else {
                Write-Host "FAIL-v2($($r2.code)) $s2" -ForegroundColor Red
                $results += @{a=$ap.n; e=$u.e; s="fail"; c=$r2.code; b=$s2}
            }
        } else {
            Write-Host "FAIL($($r1.code)) $s1" -ForegroundColor Red
            $results += @{a=$ap.n; e=$u.e; s="fail"; c=$r1.code; b=$s1}
        }

        Start-Sleep -Milliseconds 1200
    }
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host "========== RESULTS ==========" -ForegroundColor Cyan
$ok = ($results | ?{$_.s -eq "ok"}).Count
$nc = ($results | ?{$_.s -eq "need_code"}).Count
$fl = $results.Count - $ok - $nc
Write-Host "OK: $ok | NEED_CODE: $nc | FAIL: $fl" -ForegroundColor Cyan

if ($subLinks.Count -gt 0) {
    Write-Host ""
    Write-Host "=== SUB LINKS ===" -ForegroundColor Green
    $subLinks | %{ Write-Host $_ -ForegroundColor Green }
}

$results | ConvertTo-Json -Depth 3 | Out-File "$outDir\results.json" -Encoding utf8
$subLinks -join "`n" | Out-File "$outDir\subscriptions.txt" -Encoding utf8
Write-Host "SAVED: $outDir\results.json + subscriptions.txt" -ForegroundColor Cyan
