Unicode true
!include "MUI2.nsh"
!include "x64.nsh"

!define PRODUCT "Rotación de cuentas"
!define VERSION "1.0.0"
!define EXE "RotacionDeCuentas.exe"
!define UNINSTALL_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\RotacionDeCuentas"

Name "${PRODUCT}"
OutFile "${OUTPUT}"
InstallDir "$LOCALAPPDATA\Programs\RotacionDeCuentas"
RequestExecutionLevel user
SetCompressor /SOLID lzma
Icon "Trading.ico"
UninstallIcon "Trading.ico"
VIProductVersion "1.0.0.0"
VIAddVersionKey /LANG=1034 "ProductName" "${PRODUCT}"
VIAddVersionKey /LANG=1034 "FileDescription" "Instalador de ${PRODUCT}"
VIAddVersionKey /LANG=1034 "FileVersion" "${VERSION}"
VIAddVersionKey /LANG=1034 "LegalCopyright" "Rotación de cuentas"

!define MUI_FINISHPAGE_RUN "$INSTDIR\${EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "Abrir Rotación de cuentas"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "Spanish"

Function .onInit
    ${IfNot} ${RunningX64}
        MessageBox MB_OK|MB_ICONSTOP "Este instalador requiere Windows de 64 bits."
        Abort
    ${EndIf}
    SetShellVarContext current
    SetRegView 64
FunctionEnd

Section
    SetOutPath "$INSTDIR"
    File /r "${PAYLOAD}\*"
    WriteUninstaller "$INSTDIR\Desinstalar.exe"
    CreateDirectory "$SMPROGRAMS\${PRODUCT}"
    CreateShortcut "$SMPROGRAMS\${PRODUCT}\${PRODUCT}.lnk" "$INSTDIR\${EXE}"
    CreateShortcut "$DESKTOP\${PRODUCT} (instalada).lnk" "$INSTDIR\${EXE}"
    WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayName" "${PRODUCT}"
    WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayVersion" "${VERSION}"
    WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayIcon" "$INSTDIR\${EXE}"
    WriteRegStr HKCU "${UNINSTALL_KEY}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKCU "${UNINSTALL_KEY}" "UninstallString" '"$INSTDIR\Desinstalar.exe"'
    WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoModify" 1
    WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoRepair" 1
SectionEnd

Section "Uninstall"
    SetShellVarContext current
    SetRegView 64
    Delete "$DESKTOP\${PRODUCT} (instalada).lnk"
    Delete "$SMPROGRAMS\${PRODUCT}\${PRODUCT}.lnk"
    RMDir "$SMPROGRAMS\${PRODUCT}"
    Delete "$INSTDIR\${EXE}"
    RMDir /r "$INSTDIR\_internal"
    Delete "$INSTDIR\Desinstalar.exe"
    RMDir "$INSTDIR"
    DeleteRegKey HKCU "${UNINSTALL_KEY}"
SectionEnd
