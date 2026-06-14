$ErrorActionPreference = "Continue"
$out = "--- Test started at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ---`n"

# Test port 5173
try {
    $r = Invoke-WebRequest -Uri 'http://localhost:5173/' -UseBasicParsing -TimeoutSec 5
    $out += "Port 5173 (Frontend): $($r.StatusCode)`n"
    $out += "Content length: $($r.Content.Length)`n"
} catch {
    $out += "Port 5173 (Frontend): ERROR - $($_.Exception.Message)`n"
}

# Test port 8080
try {
    $r = Invoke-WebRequest -Uri 'http://localhost:8080/api/rankings?siteCode=qidian&rankingType=daily' -UseBasicParsing -TimeoutSec 5 -Headers @{Authorization = "Bearer test"}
    $out += "Port 8080 (Backend /rankings): $($r.StatusCode)`n"
} catch {
    $out += "Port 8080 (Backend /rankings): ERROR - $($_.Exception.Message)`n"
    if ($_.Exception.Response) {
        try {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $out += "Body: $($reader.ReadToEnd())`n"
        } catch {}
    }
}

# Test backend API without auth (should fail with 401)
try {
    $r = Invoke-WebRequest -Uri 'http://localhost:8080/api/novels/2/records?pageNum=1&pageSize=10' -UseBasicParsing -TimeoutSec 5
    $out += "Backend /novels/2/records (no auth): $($r.StatusCode) - $($r.Content.Substring(0, [Math]::Min(200, $r.Content.Length)))`n"
} catch {
    $out += "Backend /novels/2/records (no auth): ERROR - $($_.Exception.Message)`n"
}

# Check processes
$out += "`n--- Processes ---`n"
$procs = Get-Process -Name java,node -ErrorAction SilentlyContinue
foreach ($p in $procs) {
    $out += "$($p.ProcessName) PID=$($p.Id) Started=$($p.StartTime)`n"
}

$out | Out-File -FilePath "e:\gitWork\javaWebWork\javaWebWork\logs\diag-result.txt" -Encoding utf8