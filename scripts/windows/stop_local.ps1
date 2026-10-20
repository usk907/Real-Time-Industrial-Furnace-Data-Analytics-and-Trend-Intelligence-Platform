# IEIP - Stop All Local Services
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   IEIP - Stopping All Local Services" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

$ports = @(8000, 8001, 5173)
foreach ($port in $ports) {
    Write-Host "Checking port $port..." -ForegroundColor Yellow
    $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conns) {
        foreach ($conn in $conns) {
            $pidToKill = $conn.OwningProcess
            if ($pidToKill -and $pidToKill -ne 0) {
                try {
                    Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
                    Write-Host "  -> Terminated process on port $port (PID: $pidToKill)" -ForegroundColor Green
                } catch {
                    Write-Host "  -> Could not stop PID $pidToKill: $_" -ForegroundColor Red
                }
            }
        }
    } else {
        Write-Host "  -> Port $port is already free." -ForegroundColor DarkGray
    }
}

Write-Host "Checking for SCADA Simulator processes..." -ForegroundColor Yellow
$simProcs = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*scada_simulator.py*' }
if ($simProcs) {
    foreach ($proc in $simProcs) {
        try {
            Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
            Write-Host "  -> Terminated simulator process (PID: $($proc.ProcessId))" -ForegroundColor Green
        } catch {
            Write-Host "  -> Could not stop simulator PID $($proc.ProcessId): $_" -ForegroundColor Red
        }
    }
} else {
    Write-Host "  -> No running SCADA simulator processes detected." -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " All IEIP services have been stopped." -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
