# Only run in a disposable GitHub Windows runner, never in an existing user profile.
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -ne 'true') { throw 'This test requires a disposable GitHub Actions runner.' }
$destination = Join-Path $env:RUNNER_TEMP ("widget-install-" + [guid]::NewGuid())
$data = Join-Path $env:APPDATA 'windows-widget'
if (Test-Path $data) { throw 'Refusing to test over an existing Windows Widget profile.' }
$installer = (Get-ChildItem 'dist/windows-widget-*-x64-win.exe' | Select-Object -First 1).FullName
if (-not $installer) { throw 'Installer was not built.' }
try {
    $process = Start-Process -FilePath $installer -ArgumentList @('/S', "/D=$destination") -PassThru
    if (-not $process.WaitForExit(90000) -or $process.ExitCode -ne 0) { throw 'Silent installation failed.' }
    $exe = Join-Path $destination 'Widget Library.exe'
    $uninstaller = Join-Path $destination 'Uninstall Widget Library.exe'
    if (-not (Test-Path $exe) -or -not (Test-Path $uninstaller)) { throw 'Installed executable/uninstaller missing.' }
    $installed = Get-ItemProperty 'HKCU:\Software\WindowsWidget'
    if ($installed.InstallPath -ne $destination) { throw 'Per-user install registration mismatch.' }
    New-Item -ItemType Directory -Path $data | Out-Null
    Set-Content -Path (Join-Path $data 'preserve-test.txt') -Value 'local test state'
    Set-Content -Path (Join-Path $destination 'keep-test.txt') -Value 'unrelated destination file'
    $process = Start-Process -FilePath $uninstaller -ArgumentList '/S' -PassThru
    if (-not $process.WaitForExit(90000)) { throw 'Uninstaller timed out.' }
    $deadline = (Get-Date).AddSeconds(30)
    while ((Test-Path $exe) -and (Get-Date) -lt $deadline) { Start-Sleep -Milliseconds 300 }
    if (Test-Path $exe) { throw 'Application files were not removed.' }
    if (Test-Path 'HKCU:\Software\WindowsWidget') { throw 'Install registration was not removed.' }
    if (-not (Test-Path (Join-Path $data 'preserve-test.txt'))) { throw 'Uninstall removed user state.' }
    if (-not (Test-Path (Join-Path $destination 'keep-test.txt'))) { throw 'Uninstall removed unrelated destination files.' }
    Write-Output 'INSTALL OK: per-user silent install, registration, uninstall, user data and unrelated-file preservation'
} finally {
    # Both directories were created by this test after refusing existing profile data.
    if (Test-Path $destination) { Remove-Item -Recurse -Force $destination }
    if (Test-Path $data) { Remove-Item -Recurse -Force $data }
}
