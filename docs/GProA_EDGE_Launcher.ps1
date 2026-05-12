<#
.SYNOPSIS
    GProA EDGE - Development Launcher (PowerShell version)
    Corrección: sin caracteres Unicode problemáticos, escape de &&.
#>

# ================= CONFIGURACIÓN =================
$BACKEND_PORT = 8000
$FRONTEND_PORT = 3000
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$ROOT_DIR = Split-Path -Parent $SCRIPT_DIR
$LOG_DIR = Join-Path $SCRIPT_DIR "logs"
if (-not (Test-Path $LOG_DIR)) { New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null }
$BACKEND_LOG = Join-Path $LOG_DIR "backend.log"
$FRONTEND_LOG = Join-Path $LOG_DIR "frontend.log"

# ================= FUNCIONES UI (ASCII-only) =================
function Write-Success { Write-Host "[OK] $($args[0])" -ForegroundColor Green }
function Write-Error   { Write-Host "[ERROR] $($args[0])" -ForegroundColor Red }
function Write-Warning { Write-Host "[WARN] $($args[0])" -ForegroundColor Yellow }
function Write-Info    { Write-Host "[INFO] $($args[0])" -ForegroundColor Cyan }
function Write-Separator { Write-Host ("=" * 60) -ForegroundColor DarkGray }

function Show-Banner {
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host "       G P r o A   E D G E   -   M E N U   D E   D E S A R R O L L O" -ForegroundColor Cyan
    Write-Host ("=" * 60) -ForegroundColor Cyan
}

function Show-MenuItem($num, $desc) {
    Write-Host "  [$num] $desc" -ForegroundColor Green
}

# ================= FUNCIONES LÓGICAS =================
function Test-Dependencies {
    try {
        $null = Get-Command python -ErrorAction Stop
        $null = Get-Command node -ErrorAction Stop
        Write-Success "Python y Node.js encontrados"
        return $true
    } catch {
        Write-Error "Dependencias faltantes: $($_.Exception.Message)"
        return $false
    }
}

function Get-ProcessByPort($port) {
    try {
        # Usar netstat que es mas confiable en todas las versiones de Windows
        $netstat = netstat -ano | Select-String ":$port\s+.*LISTENING" | Select-Object -First 1
        if ($netstat) {
            $pidStr = ($netstat.ToString().Split(' ') | Where-Object { $_ -ne "" })[-1]
            if ($pidStr -match '^\d+$') {
                $procId = [int]$pidStr
                $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue | Select-Object -First 1
                if ($proc) {
                    return @{ PID = $procId; Name = $proc.ProcessName; Memory = [math]::Round($proc.WorkingSet64 / 1MB, 2) }
                }
            }
        }
    } catch { }
    return $null
}

function Show-ServiceStatus {
    Write-Host ("-" * 60) -ForegroundColor DarkGray
    Write-Host "ESTADO DE SERVICIOS" -ForegroundColor Cyan
    Write-Host ("-" * 60) -ForegroundColor DarkGray
    # Backend
    $be = Get-ProcessByPort $BACKEND_PORT
    if ($be) {
        $proc = $be
        $status = "ACTIVO"
        $name = "BACKEND"
        $port = $BACKEND_PORT
        $color = "Green"
        $uniquePid = $proc.PID
        Write-Host "[$status] $name - Puerto $port (PID: $uniquePid) " -ForegroundColor $color -NoNewline
        Write-Host ""
        Write-Host "         Proceso: $($proc.Name)   Memoria: $($proc.Memory) MB" -ForegroundColor Gray
    } else {
        Write-Host "[INACTIVO] BACKEND - Puerto $BACKEND_PORT libre" -ForegroundColor Red
    }
    # Frontend
    $fe = Get-ProcessByPort $FRONTEND_PORT
    if ($fe) {
        $proc = $fe
        $status = "ACTIVO"
        $name = "FRONTEND"
        $port = $FRONTEND_PORT
        $color = "Green"
        $uniquePid = $proc.PID
        Write-Host "[$status] $name - Puerto $port (PID: $uniquePid) " -ForegroundColor $color -NoNewline
        Write-Host ""
        Write-Host "         Proceso: $($proc.Name)   Memoria: $($proc.Memory) MB" -ForegroundColor Gray
    } else {
        Write-Host "[INACTIVO] FRONTEND - Puerto $FRONTEND_PORT libre" -ForegroundColor Red
    }
    Write-Host "ACCESO DIRECTO" -ForegroundColor Cyan
    Write-Host "  Frontend: http://localhost:$FRONTEND_PORT" -ForegroundColor Yellow
    Write-Host "  Backend:  http://localhost:$BACKEND_PORT/api" -ForegroundColor Yellow
    Write-Host "  Swagger:  http://localhost:$BACKEND_PORT/docs" -ForegroundColor Yellow
    Write-Host "DIAGNOSTICO DE CONECTIVIDAD" -ForegroundColor Cyan
    try {
        $url = "http://127.0.0.1:$BACKEND_PORT/api"
        $check = Invoke-RestMethod -Uri $url -TimeoutSec 5 -ErrorAction Stop
        Write-Success "API Backend:  ONLINE ($($check.message))"
    } catch {
        Write-Warning "API Backend:  OFFLINE o cargando..."
    }
    
    # Intento de verificar DB (solo si el backend esta activo)
    if ($be) {
        try {
            $dbCheck = Invoke-RestMethod -Uri "http://127.0.0.1:$BACKEND_PORT/api/projects" -TimeoutSec 3 -ErrorAction Stop
            Write-Success "Base de Datos: ACCESIBLE ($( @($dbCheck).Count ) proyectos)"
        } catch {
            Write-Warning "Base de Datos: ERROR DE CONEXION"
        }
    }
    Write-Host ("-" * 60) -ForegroundColor DarkGray
}

function Show-Diagnostic {
    Show-Banner
    Write-Host ("-" * 60) -ForegroundColor DarkGray
    Write-Host "DIAGNOSTICO AVANZADO" -ForegroundColor Cyan
    Write-Host ("-" * 60) -ForegroundColor DarkGray
    Write-Info "Versiones de Entorno:"
    Write-Host "  Python:    $(python --version 2>&1)" -ForegroundColor Gray
    Write-Host "  Node:      $(node --version 2>&1)" -ForegroundColor Gray
    Write-Host "  NPM:       $(npm --version 2>&1)" -ForegroundColor Gray
    Write-Host ("-" * 60) -ForegroundColor DarkGray
    
    Write-Info "Integridad de Archivos:"
    $bePath = Join-Path $ROOT_DIR "backend"
    $fePath = Join-Path $ROOT_DIR "frontend"
    $venvCheck = if (Test-Path (Join-Path $bePath "venv")) { "[OK]" } else { "[MISSING]" }
    $nmCheck = if (Test-Path (Join-Path $fePath "node_modules")) { "[OK]" } else { "[MISSING]" }
    $envCheck = if (Test-Path (Join-Path $bePath ".env")) { "[OK]" } else { "[MISSING]" }
    $vColor = if ($venvCheck -eq "[OK]") { "Green" } else { "Red" }
    $nColor = if ($nmCheck -eq "[OK]") { "Green" } else { "Red" }
    $eColor = if ($envCheck -eq "[OK]") { "Green" } else { "Red" }
    
    Write-Host "  Backend Venv:     $venvCheck" -ForegroundColor $vColor
    Write-Host "  Frontend Modules: $nmCheck" -ForegroundColor $nColor
    Write-Host "  Archivo .env:     $envCheck" -ForegroundColor $eColor
    Write-Host ("-" * 60) -ForegroundColor DarkGray

    Write-Info "Estado de Servicios y Puertos:"
    Show-ServiceStatus
    Write-Host ("-" * 60) -ForegroundColor DarkGray
    Write-Info "Variables de entorno:"
    Write-Host "  ROOT_DIR       = $ROOT_DIR" -ForegroundColor Gray
    Write-Host "  BACKEND_PORT   = $BACKEND_PORT" -ForegroundColor Gray
    Write-Host "  FRONTEND_PORT  = $FRONTEND_PORT" -ForegroundColor Gray
    Write-Host "  LOG_DIR        = $LOG_DIR" -ForegroundColor Gray
    Write-Host ("-" * 60) -ForegroundColor DarkGray
    Write-Info "Espacio en disco:"
    $drive = Get-PSDrive -Name (Split-Path $ROOT_DIR -Qualifier).TrimEnd(':')
    Write-Host "  Libre: $([math]::Round($drive.Free/1GB,2)) GB" -ForegroundColor Gray
    Write-Host ("-" * 60) -ForegroundColor DarkGray
    Write-Info "Ultimas lineas de logs:"
    if (Test-Path $BACKEND_LOG) {
        Write-Host "  --- Backend log ---" -ForegroundColor DarkGray
        Get-Content $BACKEND_LOG -Tail 5 | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
    }
    if (Test-Path $FRONTEND_LOG) {
        Write-Host "  --- Frontend log ---" -ForegroundColor DarkGray
        Get-Content $FRONTEND_LOG -Tail 5 | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
    }
    Write-Host ("=" * 60) -ForegroundColor Cyan
}

function Start-Backend {
    $bd = Join-Path $ROOT_DIR "backend"
    if (-not (Test-Path $bd)) {
        Write-Error "Carpeta backend no encontrada en $bd"
        return $false
    }
    # Crear venv si no existe
    $venvPath = Join-Path $bd "venv"
    if (-not (Test-Path $venvPath)) {
        Write-Info "Creando entorno virtual..."
        Push-Location $bd
        python -m venv venv
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Fallo creacion de venv"
            Pop-Location
            return $false
        }
        Write-Info "Instalando dependencias (puede tardar)..."
        & "$venvPath\Scripts\Activate.ps1"
        pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Fallo instalacion de dependencias"
            Pop-Location
            return $false
        }
        Pop-Location
    }
    # Configurar .env si no existe
    $envFile = Join-Path $bd ".env"
    if (-not (Test-Path $envFile)) {
        $exampleRoot = Join-Path $ROOT_DIR ".env.example"
        $exampleBackend = Join-Path $bd ".env.example"
        if (Test-Path $exampleRoot) {
            Copy-Item $exampleRoot $envFile
            Write-Success ".env creado desde raiz/.env.example"
        } elseif (Test-Path $exampleBackend) {
            Copy-Item $exampleBackend $envFile
            Write-Success ".env creado desde backend/.env.example"
        } else {
            Write-Warning "No se encontro .env.example. Creando .env basico."
            "BACKEND_PORT=$BACKEND_PORT" | Out-File -FilePath $envFile -Encoding utf8
        }
    }
    # Verificar puerto libre
    if (Get-ProcessByPort $BACKEND_PORT) {
        Write-Error "El puerto $BACKEND_PORT ya esta en uso. Deten el servicio primero."
        return $false
    }
    Write-Info "Iniciando Backend..."
    Write-Host ("-" * 60) -ForegroundColor Cyan
    Write-Info "API Base : http://localhost:$BACKEND_PORT/api"
    Write-Info "Swagger  : http://localhost:$BACKEND_PORT/docs"
    Write-Info "ReDoc    : http://localhost:$BACKEND_PORT/redoc"
    Write-Host ("-" * 60) -ForegroundColor Cyan
    # Lanzar proceso en ventana separada con titulo y color (0B = Cyan)
    $arguments = '/k title GProA EDGE - BACKEND & color 0B & cd /d "' + $bd + '" & call venv\Scripts\activate.bat & uvicorn app.main:app --port ' + $BACKEND_PORT
    Start-Process -FilePath "cmd.exe" -ArgumentList $arguments -WindowStyle Normal
    Write-Success "Backend lanzado (log en $BACKEND_LOG)"
    return $true
}

function Start-Frontend {
    $fd = Join-Path $ROOT_DIR "frontend"
    if (-not (Test-Path $fd)) {
        Write-Error "Carpeta frontend no encontrada en $fd"
        return $false
    }
    $nodeModules = Join-Path $fd "node_modules"
    if (-not (Test-Path $nodeModules)) {
        Write-Info "Instalando dependencias frontend (npm install --legacy-peer-deps)..."
        Push-Location $fd
        npm install --legacy-peer-deps
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Fallo npm install"
            Pop-Location
            return $false
        }
        Pop-Location
    }
    if (Get-ProcessByPort $FRONTEND_PORT) {
        Write-Error "El puerto $FRONTEND_PORT ya esta en uso. Deten el servicio primero."
        return $false
    }
    Write-Info "Iniciando Frontend (React)..."
    # Lanzar proceso en ventana separada con titulo y color (0E = Amarillo)
    $arguments = '/k title GProA EDGE - FRONTEND & color 0E & cd /d "' + $fd + '" & set "REACT_APP_BACKEND_URL=http://127.0.0.1:' + $BACKEND_PORT + '" & npm start'
    Start-Process -FilePath "cmd.exe" -ArgumentList $arguments -WindowStyle Normal
    Write-Success "Frontend lanzado (log en $FRONTEND_LOG)"
    return $true
}

function Stop-AllServices {
    Write-Info "Deteniendo procesos GProA EDGE..."
    # Matar por titulo de ventana
    Get-Process | Where-Object { $_.MainWindowTitle -like "Administrador: GProA EDGE -*" } | ForEach-Object { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue }
    # Matar por puerto
    foreach ($port in @($BACKEND_PORT, $FRONTEND_PORT)) {
        $proc = Get-ProcessByPort $port
        if ($proc) {
            Write-Info "Matando PID $($proc.PID) (puerto $port)"
            Stop-Process -Id $proc.PID -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Seconds 1
    # Rotar logs
    if (Test-Path $BACKEND_LOG) { Move-Item $BACKEND_LOG "$BACKEND_LOG.old" -Force -ErrorAction SilentlyContinue }
    if (Test-Path $FRONTEND_LOG) { Move-Item $FRONTEND_LOG "$FRONTEND_LOG.old" -Force -ErrorAction SilentlyContinue }
    Write-Success "Todos los servicios detenidos"
}

function Invoke-SeedData {
    Write-Info "Cargando datos mock en http://127.0.0.1:$BACKEND_PORT/api/debug/seed..."
    try {
        # Validar sin barra final y con mas tiempo
        $null = Invoke-WebRequest -Uri "http://127.0.0.1:$BACKEND_PORT/api" -TimeoutSec 5 -ErrorAction Stop
    } catch {
        Write-Error "El backend no esta disponible en el puerto $BACKEND_PORT (127.0.0.1). Inicialo primero."
        return
    }
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$BACKEND_PORT/api/debug/seed" -Method POST -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Success "Datos cargados exitosamente"
        } else {
            Write-Error "La carga fallo con codigo $($response.StatusCode)"
        }
    } catch {
        Write-Error "Error al cargar datos: $($_.Exception.Message)"
    }
}

function Invoke-ClearData {
    Write-Warning "Esto eliminara TODOS los proyectos y archivos de la base de datos."
    $confirm = Read-Host -Prompt "¿Estas seguro? (s/n)"
    if ($confirm -ne "s") { return }

    Write-Info "Limpiando base de datos en http://127.0.0.1:$BACKEND_PORT/api/debug/clear..."
    try {
        $null = Invoke-WebRequest -Uri "http://127.0.0.1:$BACKEND_PORT/api" -TimeoutSec 5 -ErrorAction Stop
    } catch {
        Write-Error "El backend no esta disponible. Inicialo primero."
        return
    }
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$BACKEND_PORT/api/debug/clear" -Method POST -UseBasicParsing -ErrorAction Stop
        Write-Success "Base de datos limpiada correctamente"
    } catch {
        Write-Error "Error al limpiar datos: $($_.Exception.Message)"
    }
}

function Show-Logs {
    do {
        Clear-Host
        Write-Host ("=" * 40) -ForegroundColor Cyan
        Write-Host "VISUALIZACION DE LOGS" -ForegroundColor Cyan
        Write-Host ("=" * 40) -ForegroundColor Cyan
        Show-MenuItem "1" "Ver log del Backend"
        Show-MenuItem "2" "Ver log del Frontend"
        Show-MenuItem "3" "Volver"
        $logopt = Read-Host -Prompt "`nOpcion"
        switch ($logopt) {
            "1" {
                if (Test-Path $BACKEND_LOG) {
                    Get-Content $BACKEND_LOG -Tail 50 | more
                } else {
                    Write-Warning "No hay log aun. Inicia el backend primero."
                    Read-Host "`nPresiona Enter para continuar"
                }
            }
            "2" {
                if (Test-Path $FRONTEND_LOG) {
                    Get-Content $FRONTEND_LOG -Tail 50 | more
                } else {
                    Write-Warning "No hay log aun. Inicia el frontend primero."
                    Read-Host "`nPresiona Enter para continuar"
                }
            }
            "3" { break }
            default { Write-Warning "Opcion invalida" }
        }
    } while ($logopt -ne "3")
}

# ================= MENU PRINCIPAL =================
Clear-Host
if (-not (Test-Dependencies)) {
    Write-Error "Faltan dependencias. Pulsa una tecla para salir."
    Read-Host
    exit 1
}

do {
    Clear-Host
    Show-Banner
    Write-Info "Ruta: $ROOT_DIR"
    Write-Host ""
    Show-ServiceStatus
    Write-Host ""
    Show-MenuItem "1" "Iniciar Todo"
    Show-MenuItem "2" "Iniciar Backend"
    Show-MenuItem "3" "Iniciar Frontend"
    Show-MenuItem "4" "Ver Estado"
    Show-MenuItem "5" "Ver Logs"
    Show-MenuItem "6" "Detener Servicios"
    Show-MenuItem "7" "Diagnostico"
    Show-MenuItem "8" "Limpiar y Reiniciar (venv / node_modules)"
    Show-MenuItem "9" "Cargar Datos Mock (Seed)"
    Show-MenuItem "10" "Limpiar Base de Datos (Vaciar)"
    Show-MenuItem "0" "Salir"
    Write-Host ""
    $opt = Read-Host -Prompt "Selecciona (0-9)"

    switch ($opt) {
        "1" {
            Start-Backend
            Start-Sleep -Seconds 2
            Start-Frontend
            Read-Host "`nPresiona Enter para continuar"
        }
        "2" {
            Start-Backend
            Read-Host "`nPresiona Enter para continuar"
        }
        "3" {
            Start-Frontend
            Read-Host "`nPresiona Enter para continuar"
        }
        "4" {
            Clear-Host
            Show-ServiceStatus
            Read-Host "`nPresiona Enter para continuar"
        }
        "5" { Show-Logs }
        "6" {
            Stop-AllServices
            Read-Host "`nPresiona Enter para continuar"
        }
        "7" {
            Clear-Host
            Show-Diagnostic
            Read-Host "`nPresiona Enter para continuar"
        }
        "8" {
            Write-Warning "Esto eliminara venv y node_modules y los recreara."
            $confirm = Read-Host "¿Continuar? (s/N)"
            if ($confirm -eq 's') {
                Stop-AllServices
                Write-Info "Eliminando venv..."
                $venvPath = Join-Path $ROOT_DIR "backend\venv"
                if (Test-Path $venvPath) { Remove-Item -Recurse -Force $venvPath }
                Write-Info "Eliminando node_modules..."
                $nmPath = Join-Path $ROOT_DIR "frontend\node_modules"
                if (Test-Path $nmPath) { Remove-Item -Recurse -Force $nmPath }
                Write-Success "Limpieza completada."
            }
            Read-Host "`nPresiona Enter para continuar"
        }
        "9" {
            Invoke-SeedData
            Read-Host "`nPresiona Enter para continuar"
        }
        "10" {
            Invoke-ClearData
            Read-Host "`nPresiona Enter para continuar"
        }
        "0" {
            Stop-AllServices
            Write-Success "Saliendo..."
        }
        default { Write-Warning "Opcion invalida" }
    }
} while ($opt -ne "0")