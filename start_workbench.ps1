$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = "C:\Users\vedar\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$url = "http://127.0.0.1:8765"

try {
    $listener = Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction Stop
} catch {
    $listener = $null
}

if (-not $listener) {
    if (-not (Test-Path $python)) {
        $python = (Get-Command py -ErrorAction Stop).Source
    }
    Start-Process -FilePath $python `
        -ArgumentList @("app_server.py", "--no-browser") `
        -WorkingDirectory $root `
        -WindowStyle Hidden

    for ($attempt = 0; $attempt -lt 40; $attempt++) {
        Start-Sleep -Milliseconds 250
        try {
            $response = Invoke-WebRequest "$url/api/observations" -UseBasicParsing -TimeoutSec 1
            if ($response.StatusCode -eq 200) { break }
        } catch {
            continue
        }
    }
}

Start-Process $url

