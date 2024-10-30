param (
    [string]$Thumbprint,
    [string]$CabName
)

Write-Host "Thumbprint: $Thumbprint" -ForegroundColor Green
Write-Host "CAB Name: $CabName" -ForegroundColor Green

# Check if required tools exist
$latestBinPath = (Get-ChildItem -Path "$([Environment]::GetFolderPath('ProgramFilesX86'))\Windows Kits\10\bin" -Directory | Where-Object { $_.Name -match '^\d+\.\d+\.\d+\.\d+$' } | Sort-Object { [Version]$_.Name } -Descending | Select-Object -First 1).FullName
$makecatPath = "$latestBinPath\x64\makecat.exe"
$signToolPath = "$latestBinPath\x64\signtool.exe"

if (-Not (Test-Path $makecatPath)) {
    Write-Host "Makecat tool not found at: $makecatPath" -ForegroundColor Red
}
if (-Not (Test-Path $signToolPath)) {
    Write-Host "SignTool not found at: $signToolPath" -ForegroundColor Red
}

# Ensure tools are present before continuing
if (-Not (Test-Path $makecatPath) -or -Not (Test-Path $signToolPath)) {
    Write-Host "Required tools not found in the specified paths. Aborting." -ForegroundColor Red
    exit 1
}

Write-Output "Making CAT..."
$cat = & $makecatPath update.cdf 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to make CAT! Error: $cat" -ForegroundColor Red
} else {
    Write-Host "Successfully created CAT." -ForegroundColor Green
}

Write-Output "Signing CAT..."
$cat1 = & $signToolPath sign /debug /sm /uw /sha1 $Thumbprint /fd SHA256 update.cat 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to sign CAT! Error: $cat1" -ForegroundColor Red
} else {
    Write-Host "Successfully signed CAT." -ForegroundColor Green
}

Write-Output "Making CAB..."
$cab = & makecab.exe /d "CabinetName1=$CabName" /f files.txt 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to make CAB! Error: $cab" -ForegroundColor Red
} else {
    Write-Host "Successfully created CAB." -ForegroundColor Green
}
Remove-Item -Path "setup.*" -Force -ErrorAction SilentlyContinue

Write-Output "Signing CAB..."
$cab1 = & $signToolPath sign /debug /sm /uw /sha1 $Thumbprint /fd SHA256 "disk1\$CabName" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to sign CAB! Error: $cab1" -ForegroundColor Red
} else {
    Write-Host "Successfully signed CAB." -ForegroundColor Green
}

Write-Output "Copying CAB to main directory..."
try {
    Copy-Item -Path "disk1\*.cab" -Destination "$env:USERPROFILE\Desktop" -Force
    Write-Host "CAB copied to desktop." -ForegroundColor Green
} catch {
    Write-Host "Failed to copy CAB: $_" -ForegroundColor Red
}

Write-Host "Processing complete. Press Enter to exit..."
pause
