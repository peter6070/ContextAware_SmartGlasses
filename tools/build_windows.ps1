param(
    [string]$Python = 'python'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$build = Join-Path $root 'build/windows'
$dist = Join-Path $root 'dist'
$bundle = Join-Path $dist 'SmartGlasses'
$model = Join-Path $build 'hand_landmarker.task'
$archive = Join-Path $dist 'SmartGlasses-Windows-x64.zip'

New-Item -ItemType Directory -Force -Path $build | Out-Null
if (-not (Test-Path -LiteralPath $model)) {
    $modelUrl = 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task'
    Invoke-WebRequest -UseBasicParsing -Uri $modelUrl -OutFile "$model.download"
    Move-Item -LiteralPath "$model.download" -Destination $model
}

Push-Location $root
try {
    & $Python -m pip install -r requirements.txt 'pyinstaller>=6,<7'
    if ($LASTEXITCODE -ne 0) { throw '배포본 빌드 의존성을 설치하지 못했습니다.' }

    & $Python -m PyInstaller --noconfirm --onedir --console --name SmartGlasses `
        --distpath $dist --workpath $build --specpath $build --paths $root `
        --collect-binaries mediapipe --exclude-module software.matter_worker `
        software/windows_launcher.py
    if ($LASTEXITCODE -ne 0) { throw 'SmartGlasses.exe를 빌드하지 못했습니다.' }

    Copy-Item -LiteralPath $model -Destination $bundle
    $pythonPath = (Get-Command $Python -ErrorAction Stop).Source
    Push-Location $dist
    try {
        & $pythonPath -m zipfile -c $archive SmartGlasses
        if ($LASTEXITCODE -ne 0) { throw '배포 ZIP을 만들지 못했습니다.' }
    } finally {
        Pop-Location
    }
    Write-Output $archive
} finally {
    Pop-Location
}
