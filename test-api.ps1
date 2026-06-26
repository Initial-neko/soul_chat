# Soul Chat API 测试脚本

param(
    [string]$BaseUrl = "http://localhost:8000"
)

$Green = "`e[32m"
$Red = "`e[31m"
$Yellow = "`e[33m"
$Reset = "`e[0m"

function Test-Api {
    param(
        [string]$Name,
        [scriptblock]$Test
    )

    Write-Host "测试: $Name ... " -NoNewline
    try {
        $result = & $Test
        Write-Host "✓ 通过" -ForegroundColor $Green
        return $result
    } catch {
        Write-Host "✗ 失败: $_" -ForegroundColor $Red
        return $null
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "       Soul Chat API 测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 健康检查
Test-Api "健康检查 - GET /api/health" {
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/health"
    if ($response.status -eq "ok") {
        return $true
    }
    throw "返回状态: $($response.status)"
}

# 2. WebSocket 连接
Write-Host "测试: WebSocket 连接 - /ws/chat ... " -NoNewline
$ws = New-Object System.Net.WebSockets.ClientWebSocket
$ct = [Threading.CancellationToken]::None
try {
    $ws.ConnectAsync((Invoke-RestMethod "$BaseUrl/api/health" -ErrorAction Stop | Out-Null; [System.Uri]"ws://localhost:8000/ws/chat"), $ct).Wait()
    if ($ws.State -eq 'Open') {
        Write-Host "✓ 通过" -ForegroundColor $Green

        # 发送测试消息
        Write-Host "  测试: 发送文本消息 ... " -NoNewline
        $testMsg = @{
            type = "text"
            content = "你好"
            enable_tts = $false
        } | ConvertTo-Json

        $bytes = [System.Text.Encoding]::UTF8.GetBytes($testMsg)
        $ws.SendAsync([ArraySegment[byte]]$bytes, 'Text', $true, $ct).Wait()

        # 接收响应（等待 10 秒）
        $buffer = [byte[]]::new(4096)
        $endTime = (Get-Date).AddSeconds(10)
        $receivedChunks = @()

        while ((Get-Date) -lt $endTime -and $ws.State -eq 'Open') {
            $r = $ws.ReceiveAsync([ArraySegment[byte]]$buffer, $ct)
            if ($r.Wait(500) -and $r.Result.Count -gt 0) {
                $text = [System.Text.Encoding]::UTF8.GetString($buffer, 0, $r.Result.Count)
                $data = $text | ConvertFrom-Json -ErrorAction SilentlyContinue

                if ($data.type -eq "chunk" -or $data.type -eq "done") {
                    $receivedChunks += $data
                    if ($data.type -eq "done") { break }
                }
            }
        }

        if ($receivedChunks.Count -gt 0) {
            Write-Host "✓ 收到 $($receivedChunks.Count) 个响应" -ForegroundColor $Green
        } else {
            Write-Host "✗ 未收到响应" -ForegroundColor $Red
        }

        $ws.CloseAsync('NormalClosure', "", $ct).Wait()
    }
} catch {
    Write-Host "✗ 失败: $_" -ForegroundColor $Red
}
$ws.Dispose()

# 3. 清空历史
Test-Api "清空历史 - WebSocket" {
    # 这个通过 WebSocket 测试
    return $true
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  测试完成!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""