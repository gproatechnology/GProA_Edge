<#
.SYNOPSIS
    GProA EDGE - Git Auto-Push a la rama tech-debt
.DESCRIPTION
    Este script automatiza el proceso de commit y push en la rama 'tech-debt'.
    Incluye validaciones, opción de seleccionar archivos y manejo de conflictos.
.NOTES
    Requiere: git instalado y configurado en el PATH.
#>

# ================= CONFIGURACIÓN =================
$BRANCH_NAME = "tech-debt"
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$ROOT_DIR = Split-Path -Parent $SCRIPT_DIR
$LOG_FILE = Join-Path $SCRIPT_DIR "git_push.log"

# ================= FUNCIONES DE UI =================
function Write-Success { Write-Host "[OK] $($args[0])" -ForegroundColor Green }
function Write-Error { Write-Host "[ERROR] $($args[0])" -ForegroundColor Red }
function Write-Warning { Write-Host "[WARN] $($args[0])" -ForegroundColor Yellow }
function Write-Info { Write-Host "[INFO] $($args[0])" -ForegroundColor Cyan }

function Show-Banner {
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host "       G P r o A   E D G E   -   G I T   A U T O - P U S H   ($BRANCH_NAME)" -ForegroundColor Cyan
    Write-Host ("=" * 60) -ForegroundColor Cyan
}

# ================= FUNCIONES DE GIT =================
function Test-GitInstalled {
    try {
        $null = git --version 2>&1
        return $true
    }
    catch {
        return $false
    }
}

function Test-GitRepository {
    try {
        $null = git rev-parse --git-dir 2>&1
        return $true
    }
    catch {
        return $false
    }
}

function Get-CurrentBranch {
    $branch = git rev-parse --abbrev-ref HEAD 2>$null
    return $branch
}

function Invoke-GitWithLog($command, $actionDescription) {
    Write-Info "$actionDescription..."
    $output = Invoke-Expression $command 2>&1
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        Write-Error "Fallo: $actionDescription"
        Write-Host $output -ForegroundColor Red
        # Registrar en log
        $logEntry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] ERROR: $actionDescription`n$output`n"
        Add-Content -Path $LOG_FILE -Value $logEntry
        return $false
    }
    else {
        if ($output) { Write-Host $output -ForegroundColor Gray }
        # Registrar en log
        $logEntry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] OK: $actionDescription`n"
        Add-Content -Path $LOG_FILE -Value $logEntry
        return $true
    }
}

# ================= MENÚ PRINCIPAL =================
Clear-Host
Show-Banner

# 1. Verificar git instalado
if (-not (Test-GitInstalled)) {
    Write-Error "Git no está instalado o no está en el PATH."
    Read-Host "Presiona Enter para salir"
    exit 1
}

# 2. Verificar que estamos en un repositorio git
Push-Location $ROOT_DIR
if (-not (Test-GitRepository)) {
    Write-Error "El directorio $ROOT_DIR no es un repositorio Git válido."
    Pop-Location
    Read-Host "Presiona Enter para salir"
    exit 1
}

# 3. Mostrar estado actual
Write-Host "`nEstado actual del repositorio:" -ForegroundColor Yellow
git status -s
if ($LASTEXITCODE -ne 0) { git status }

# 4. Verificar rama actual y crearla si no existe
$currentBranch = Get-CurrentBranch
if ($currentBranch -ne $BRANCH_NAME) {
    Write-Warning "Estás en la rama '$currentBranch', no en '$BRANCH_NAME'."
    $resp = Read-Host "¿Intentar cambiar a (o crear) la rama '$BRANCH_NAME'? (s/N)"
    
    if ($resp -eq 's') {
        # Intentamos cambiar primero
        # Usamos 'git checkout -b' si no existe, o 'git checkout' si ya existe
        $checkBranch = Invoke-GitWithLog "git checkout $BRANCH_NAME" "Cambiando a rama $BRANCH_NAME"
        
        if (-not $checkBranch) {
            Write-Info "La rama no existe localmente, intentando crearla..."
            if (-not (Invoke-GitWithLog "git checkout -b $BRANCH_NAME" "Creando rama $BRANCH_NAME")) {
                Pop-Location
                Read-Host "Presiona Enter para salir"
                exit 1
            }
        }
    }
    else {
        Write-Error "Operación cancelada. Debes estar en la rama $BRANCH_NAME para continuar."
        Pop-Location
        Read-Host "Presiona Enter para salir"
        exit 1
    }
}

# 5. Verificar cambios pendientes
$changes = git status --porcelain
if (-not $changes) {
    Write-Warning "No hay cambios para commitear."
    Pop-Location
    Read-Host "Presiona Enter para salir"
    exit 0
}
else {
    Write-Host "`nCambios detectados:" -ForegroundColor Yellow
    Write-Host $changes -ForegroundColor Gray
}

# 6. Opción de selección de archivos
Write-Host "`nOpciones:" -ForegroundColor Cyan
Write-Host "  [1] Agregar todos los cambios (git add .)"
Write-Host "  [2] Agregar archivos específicos (selección manual)"
Write-Host "  [3] Cancelar"
$opt = Read-Host "`nSelecciona (1-3)"

if ($opt -eq "3") {
    Write-Info "Operación cancelada por el usuario."
    Pop-Location
    Read-Host "Presiona Enter para salir"
    exit 0
}
elseif ($opt -eq "2") {
    Write-Info "Archivos modificados (ejemplo: archivo1.txt archivo2.js):"
    $files = Read-Host "Escribe los nombres separados por espacio"
    if (-not $files) {
        Write-Error "No se especificaron archivos. Cancelando."
        Pop-Location
        Read-Host "Presiona Enter para salir"
        exit 1
    }
    $addResult = Invoke-GitWithLog "git add $files" "Agregando archivos específicos"
    if (-not $addResult) { 
        Pop-Location
        Read-Host "Presiona Enter para salir"; exit 1 
    }
}
else {
    $addResult = Invoke-GitWithLog "git add ." "Agregando todos los archivos"
    if (-not $addResult) { 
        Pop-Location
        Read-Host "Presiona Enter para salir"; exit 1 
    }
}

# 7. Mensaje del commit
$defaultMsg = "auto: updates"
$msg = Read-Host "`nIntroduce el mensaje del commit (Enter para '$defaultMsg')"
if ([string]::IsNullOrWhiteSpace($msg)) { $msg = $defaultMsg }

$commitResult = Invoke-GitWithLog "git commit -m `"$msg`"" "Creando commit"
if (-not $commitResult) { 
    Pop-Location
    Read-Host "Presiona Enter para salir"; exit 1 
}

# 8. Antes de push, hacer pull para evitar conflictos (opcional)
$pullOption = Read-Host "`n¿Hacer 'git pull' antes de push para sincronizar? (s/N)"
if ($pullOption -eq 's') {
    Invoke-GitWithLog "git pull origin $BRANCH_NAME" "Sincronizando con remote"
    # Si el pull falla, se puede preguntar si continuar
}

# 9. Push
$pushResult = Invoke-GitWithLog "git push origin $BRANCH_NAME" "Subiendo a $BRANCH_NAME"

# 10. Guardar lista de archivos commithead (obtenida justo después del commit)
# Para eso, debemos capturar los archivos antes o después. La forma más fiable es justo después del commit.
# Pero como el commit ya ocurrió, podemos usar git show --name-only

# 11. Push
$pushResult = Invoke-GitWithLog "git push origin $BRANCH_NAME" "Subiendo a $BRANCH_NAME"

# 12. Generar informe final
Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "                     INFORME FINAL" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan

# Obtener información del último commit
$lastCommitHash = git rev-parse --short HEAD 2>$null
$lastCommitMsg = git log -1 --pretty=%B 2>$null
$lastCommitDate = git log -1 --pretty=%cd --date=local 2>$null
$commitStats = git show --stat --oneline -1 2>$null
$commitFiles = git show --name-only --pretty=format: 2>$null | Where-Object { $_ -ne "" }

Write-Info "Hash del commit: $lastCommitHash"
Write-Info "Fecha: $lastCommitDate"
Write-Info "Mensaje: $lastCommitMsg"
Write-Info "Rama destino: $BRANCH_NAME"

# Mostrar estadísticas de archivos
$fileCount = ($commitFiles | Measure-Object).Count
Write-Info "Archivos modificados/creados: $fileCount"

if ($fileCount -gt 0 -and $fileCount -le 20) {
    Write-Host "`n[Lista de archivos]" -ForegroundColor Yellow
    foreach ($file in $commitFiles) {
        Write-Host "  - $file" -ForegroundColor Gray
    }
}
elseif ($fileCount -gt 20) {
    Write-Host "`n(Más de 20 archivos. Para ver la lista completa, ejecuta 'git show --name-only')" -ForegroundColor DarkGray
}

# Mostrar estadísticas resumidas del commit
Write-Host "`n[Estadísticas del commit]" -ForegroundColor Yellow
Write-Host $commitStats -ForegroundColor Gray

# Resultado del push
Write-Host ""
if ($pushResult) {
    Write-Host ("=" * 60) -ForegroundColor Green
    Write-Success "Cambios subidos exitosamente a la rama '$BRANCH_NAME'."
}
else {
    Write-Host ("=" * 60) -ForegroundColor Red
    Write-Error "Hubo un problema al subir los cambios. Revisa los mensajes anteriores."
}
Write-Host ("=" * 60) -ForegroundColor DarkGray

# Registrar informe en el log (opcional)
$logReport = @"
`n=== INFORME FINAL ===
Hash: $lastCommitHash
Fecha: $lastCommitDate
Mensaje: $lastCommitMsg
Rama: $BRANCH_NAME
Archivos: $fileCount
Resultado push: $(if ($pushResult) { "ÉXITO" } else { "FALLO" })
"@
Add-Content -Path $LOG_FILE -Value $logReport

Pop-Location
Read-Host "`nPresiona Enter para salir"