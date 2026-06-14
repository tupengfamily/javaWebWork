$out = ""
$ports = @(8080, 5173, 3307)
foreach ($p in $ports) {
    $conn = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue
    if ($conn) {
        $out += "Port $p : LISTENING (PID $($conn.OwningProcess))`n"
    } else {
        $out += "Port $p : NOT LISTENING`n"
    }
}

$out += "---`n"
$out += "Testing backend API...`n"
try {
    $r = Invoke-WebRequest -Uri 'http://localhost:8080/api/novels/1' -UseBasicParsing -TimeoutSec 5 -Headers @{Authorization = "Bearer test"}
    $out += "GET /api/novels/1 -> $($r.StatusCode)`n"
    $out += "$($r.Content)`n"
} catch {
    $out += "GET /api/novels/1 -> ERROR: $($_.Exception.Message)`n"
    if ($_.Exception.Response) {
        try {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $out += "Body: $($reader.ReadToEnd())`n"
        } catch {}
    }
}

$out += "---`n"
$out += "Testing frontend...`n"
try {
    $r = Invoke-WebRequest -Uri 'http://localhost:5173/' -UseBasicParsing -TimeoutSec 5
    $out += "GET / -> $($r.StatusCode)`n"
} catch {
    $out += "GET / -> ERROR: $($_.Exception.Message)`n"
}

$out | Out-File -FilePath "e:\gitWork\javaWebWork\javaWebWork\logs\check-result.txt" -Encoding utf8