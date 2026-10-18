; Per-user installer. Compiles directly without running an intermediate EXE in Wine.
Unicode true
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "x64.nsh"
Name "${PRODUCT_NAME}"
InstallDir "$LOCALAPPDATA\Programs\Windows Widget"
InstallDirRegKey HKCU "Software\WindowsWidget" "InstallPath"
RequestExecutionLevel user
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\Widget Library.exe"
!define MUI_FINISHPAGE_RUN_NOTCHECKED
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Function .onInit
  SetShellVarContext current
  ${IfNot} ${RunningX64}
    MessageBox MB_OK|MB_ICONSTOP "Windows 11 64-bit is required."
    Abort
  ${EndIf}
  SetRegView 64
  ReadRegStr $0 HKLM "SOFTWARE\Microsoft\Windows NT\CurrentVersion" "CurrentBuildNumber"
  ${If} $0 < 22000
    MessageBox MB_OK|MB_ICONSTOP "Windows 11 (build 22000 or later) is required."
    Abort
  ${EndIf}
  checkRunning:
    FindWindow $0 "" "Widget Library"
    ${If} $0 != 0
      MessageBox MB_RETRYCANCEL|MB_ICONEXCLAMATION "Exit Widget Library using its tray menu, then retry." IDRETRY checkRunning
      Abort
    ${EndIf}
FunctionEnd

Section "Widget Library"
  InitPluginsDir
  SetOutPath "$PLUGINSDIR"
  SetCompress off
  !ifdef APP_ARM64
    File /oname=app.7z "${APP_ARM64}"
  !else
    File /oname=app.7z "${APP_64}"
  !endif
  SetCompress auto
  SetOutPath "$INSTDIR"
  Nsis7z::Extract "$PLUGINSDIR\app.7z"
  IfFileExists "$INSTDIR\Widget Library.exe" +3 0
    MessageBox MB_OK|MB_ICONSTOP "Could not extract application files. Check the destination and retry."
    Abort
  WriteUninstaller "$INSTDIR\Uninstall Widget Library.exe"
  CreateDirectory "$SMPROGRAMS\Widget Library"
  CreateShortcut "$SMPROGRAMS\Widget Library\Widget Library.lnk" "$INSTDIR\Widget Library.exe" "" "$INSTDIR\Widget Library.exe" 0 SW_SHOWNORMAL
  CreateShortcut "$DESKTOP\Widget Library.lnk" "$INSTDIR\Widget Library.exe" "" "$INSTDIR\Widget Library.exe" 0 SW_SHOWNORMAL
  WinShell::SetLnkAUMI "$SMPROGRAMS\Widget Library\Widget Library.lnk" "${APP_ID}"
  WinShell::SetLnkAUMI "$DESKTOP\Widget Library.lnk" "${APP_ID}"
  WriteRegStr HKCU "Software\WindowsWidget" "InstallPath" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WindowsWidget" "DisplayName" "Widget Library"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WindowsWidget" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WindowsWidget" "Publisher" "Ubuntu Widget contributors"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WindowsWidget" "DisplayIcon" "$INSTDIR\Widget Library.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WindowsWidget" "UninstallString" '$\"$INSTDIR\Uninstall Widget Library.exe$\"'
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WindowsWidget" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WindowsWidget" "NoRepair" 1
SectionEnd

Function un.onInit
  SetShellVarContext current
  SetRegView 64
  checkRunning:
    FindWindow $0 "" "Widget Library"
    ${If} $0 != 0
      MessageBox MB_RETRYCANCEL|MB_ICONEXCLAMATION "Exit Widget Library using its tray menu, then retry." IDRETRY checkRunning
      Abort
    ${EndIf}
FunctionEnd

Section "Uninstall"
  Delete "$INSTDIR\resources\elevate.exe"
  !include "${PROJECT_DIR}/dist/uninstall-files.nsh"
  Delete "$INSTDIR\Uninstall Widget Library.exe"
  RMDir "$INSTDIR"
  Delete "$DESKTOP\Widget Library.lnk"
  Delete "$SMPROGRAMS\Widget Library\Widget Library.lnk"
  RMDir "$SMPROGRAMS\Widget Library"
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "WindowsWidget"
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "Widget Library"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WindowsWidget"
  WinShell::UninstAppUserModelId "${APP_ID}"
  DeleteRegKey HKCU "Software\WindowsWidget"
  ; Preserve %APPDATA%\windows-widget and any unrelated destination files.
SectionEnd
