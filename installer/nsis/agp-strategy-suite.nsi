; AGP Strategy Suite - NSIS Installer Script
; ==========================================

!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"

; --------------------------------
; General Configuration
; --------------------------------

!define PRODUCT_NAME "AGP Strategy Suite"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "AGP"
!define PRODUCT_WEB_SITE "https://github.com/agp/agp-strategy-suite"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\AGPStrategySuite.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

; Installer attributes
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "..\..\dist\AGPStrategySuite-${PRODUCT_VERSION}-Setup.exe"
InstallDir "$PROGRAMFILES\AGP Strategy Suite"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show
RequestExecutionLevel admin

; --------------------------------
; Modern UI Configuration
; --------------------------------

!define MUI_ABORTWARNING
!define MUI_ICON "..\..\apps\desktop\src-tauri\icons\icon.ico"
!define MUI_UNICON "..\..\apps\desktop\src-tauri\icons\icon.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP "welcome.bmp"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "header.bmp"

; Welcome page
!insertmacro MUI_PAGE_WELCOME

; License page
!insertmacro MUI_PAGE_LICENSE "..\..\LICENSE"

; Components page
!insertmacro MUI_PAGE_COMPONENTS

; Directory page
!insertmacro MUI_PAGE_DIRECTORY

; SimHub plugin directory
Var SimHubPath
Page custom SimHubPageCreate SimHubPageLeave

; Install page
!insertmacro MUI_PAGE_INSTFILES

; Finish page
!define MUI_FINISHPAGE_RUN "$INSTDIR\AGPStrategySuite.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Launch AGP Strategy Suite"
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\README.md"
!define MUI_FINISHPAGE_SHOWREADME_TEXT "View README"
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Language
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "French"

; --------------------------------
; Custom SimHub Page
; --------------------------------

Function SimHubPageCreate
    !insertmacro MUI_HEADER_TEXT "SimHub Integration" "Select SimHub installation directory for plugin"

    nsDialogs::Create 1018
    Pop $0

    ${NSD_CreateLabel} 0 0 100% 24u "If you have SimHub installed, the AGP Strategy plugin will be installed automatically.$\n$\nLeave empty to skip plugin installation."
    Pop $0

    ${NSD_CreateLabel} 0 40u 100% 12u "SimHub Directory:"
    Pop $0

    ${NSD_CreateDirRequest} 0 54u 240u 12u "$SimHubPath"
    Pop $1

    ${NSD_CreateBrowseButton} 250u 54u 50u 12u "Browse..."
    Pop $2
    ${NSD_OnClick} $2 SimHubBrowse

    ; Try to auto-detect SimHub
    ${If} $SimHubPath == ""
        ReadRegStr $SimHubPath HKLM "Software\SimHub" "InstallDir"
        ${If} $SimHubPath == ""
            StrCpy $SimHubPath "$PROGRAMFILES\SimHub"
            ${IfNot} ${FileExists} "$SimHubPath\SimHubWPF.exe"
                StrCpy $SimHubPath "$PROGRAMFILES (x86)\SimHub"
                ${IfNot} ${FileExists} "$SimHubPath\SimHubWPF.exe"
                    StrCpy $SimHubPath ""
                ${EndIf}
            ${EndIf}
        ${EndIf}
        ${NSD_SetText} $1 $SimHubPath
    ${EndIf}

    nsDialogs::Show
FunctionEnd

Function SimHubBrowse
    nsDialogs::SelectFolderDialog "Select SimHub Directory" $SimHubPath
    Pop $0
    ${If} $0 != "error"
        StrCpy $SimHubPath $0
        ${NSD_SetText} $1 $SimHubPath
    ${EndIf}
FunctionEnd

Function SimHubPageLeave
    ${NSD_GetText} $1 $SimHubPath
FunctionEnd

; --------------------------------
; Installer Sections
; --------------------------------

Section "AGP Strategy Suite (Required)" SEC_MAIN
    SectionIn RO

    SetOutPath "$INSTDIR"

    ; Main application files (Tauri build output)
    File /r "..\..\apps\desktop\src-tauri\target\release\AGPStrategySuite.exe"
    File /r "..\..\apps\desktop\src-tauri\target\release\*.dll"

    ; Resources
    SetOutPath "$INSTDIR\resources"
    File /r "..\..\apps\desktop\src-tauri\target\release\resources\*.*"

    ; Python backend
    SetOutPath "$INSTDIR\backend"
    File /r "..\..\dist\backend\*.*"

    ; Documentation
    SetOutPath "$INSTDIR"
    File "..\..\README.md"
    File "..\..\LICENSE"

    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
    CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\AGP Strategy Suite.lnk" "$INSTDIR\AGPStrategySuite.exe"
    CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk" "$INSTDIR\uninst.exe"
    CreateShortCut "$DESKTOP\AGP Strategy Suite.lnk" "$INSTDIR\AGPStrategySuite.exe"

    ; Registry entries
    WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\AGPStrategySuite.exe"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\AGPStrategySuite.exe"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"

    ; Calculate installed size
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "EstimatedSize" "$0"
SectionEnd

Section "SimHub Plugin" SEC_SIMHUB
    ${If} $SimHubPath != ""
    ${AndIf} ${FileExists} "$SimHubPath\SimHubWPF.exe"
        SetOutPath "$SimHubPath\Plugins"

        ; Plugin DLL and dependencies
        File "..\..\apps\simhub-plugin\AGPStrategy\bin\Release\net48\AGPStrategyPlugin.dll"
        File "..\..\apps\simhub-plugin\AGPStrategy\bin\Release\net48\Newtonsoft.Json.dll"
        File "..\..\apps\simhub-plugin\AGPStrategy\bin\Release\net48\websocket-sharp.dll"

        ; Mark plugin as installed
        WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "SimHubPluginInstalled" "1"
        WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "SimHubPath" "$SimHubPath"
    ${EndIf}
SectionEnd

Section "Desktop Shortcut" SEC_DESKTOP
    CreateShortCut "$DESKTOP\AGP Strategy Suite.lnk" "$INSTDIR\AGPStrategySuite.exe"
SectionEnd

Section "Start Menu Shortcuts" SEC_STARTMENU
    CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
    CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\AGP Strategy Suite.lnk" "$INSTDIR\AGPStrategySuite.exe"
    CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk" "$INSTDIR\uninst.exe"
SectionEnd

; --------------------------------
; Section Descriptions
; --------------------------------

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SEC_MAIN} "Core AGP Strategy Suite application with telemetry analysis, setup recommendations, and race strategy."
    !insertmacro MUI_DESCRIPTION_TEXT ${SEC_SIMHUB} "SimHub plugin for displaying AGP data in SimHub dashboards and overlays."
    !insertmacro MUI_DESCRIPTION_TEXT ${SEC_DESKTOP} "Create a desktop shortcut for quick access."
    !insertmacro MUI_DESCRIPTION_TEXT ${SEC_STARTMENU} "Create Start Menu shortcuts."
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; --------------------------------
; Uninstaller
; --------------------------------

Section Uninstall
    ; Kill running processes
    nsExec::ExecToLog 'taskkill /F /IM AGPStrategySuite.exe'
    nsExec::ExecToLog 'taskkill /F /IM python.exe'

    ; Remove SimHub plugin if installed
    ReadRegStr $0 HKLM "${PRODUCT_UNINST_KEY}" "SimHubPluginInstalled"
    ${If} $0 == "1"
        ReadRegStr $SimHubPath HKLM "${PRODUCT_UNINST_KEY}" "SimHubPath"
        ${If} ${FileExists} "$SimHubPath\Plugins\AGPStrategyPlugin.dll"
            Delete "$SimHubPath\Plugins\AGPStrategyPlugin.dll"
        ${EndIf}
    ${EndIf}

    ; Remove files
    RMDir /r "$INSTDIR\backend"
    RMDir /r "$INSTDIR\resources"
    Delete "$INSTDIR\AGPStrategySuite.exe"
    Delete "$INSTDIR\*.dll"
    Delete "$INSTDIR\README.md"
    Delete "$INSTDIR\LICENSE"
    Delete "$INSTDIR\uninst.exe"
    RMDir "$INSTDIR"

    ; Remove shortcuts
    Delete "$DESKTOP\AGP Strategy Suite.lnk"
    RMDir /r "$SMPROGRAMS\${PRODUCT_NAME}"

    ; Remove registry entries
    DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
    DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"

    SetAutoClose true
SectionEnd

; --------------------------------
; Installer Functions
; --------------------------------

Function .onInit
    ; Check for previous installation
    ReadRegStr $0 ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString"
    ${If} $0 != ""
        MessageBox MB_YESNO|MB_ICONQUESTION "A previous version of ${PRODUCT_NAME} is installed.$\n$\nDo you want to uninstall it first?" IDYES uninst_prev IDNO skip_uninst
        uninst_prev:
            ExecWait '$0 /S'
        skip_uninst:
    ${EndIf}

    ; Initialize SimHub path
    StrCpy $SimHubPath ""
FunctionEnd

Function un.onInit
    MessageBox MB_YESNO|MB_ICONQUESTION "Are you sure you want to uninstall ${PRODUCT_NAME}?" IDYES +2
    Abort
FunctionEnd
