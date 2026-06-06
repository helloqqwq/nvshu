; ============================================
; NushuIME NSIS Installer
; ============================================

!define PRODUCT_NAME "NushuIME"
!define PRODUCT_NAME_EN "NushuIME"
!define PRODUCT_VERSION "2.0.0"
!define PRODUCT_PUBLISHER "helloqqwq"
!define PRODUCT_EXE "NushuIME.exe"

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "dist\${PRODUCT_NAME_EN}_Setup_${PRODUCT_VERSION}.exe"
InstallDir "$PROGRAMFILES\${PRODUCT_NAME_EN}"
InstallDirRegKey HKLM "Software\${PRODUCT_NAME_EN}" "InstallDir"
RequestExecutionLevel admin
SetCompressor /SOLID lzma

!include "MUI2.nsh"
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

Section "!Main Program" SEC_MAIN
  SectionIn RO
  SetOutPath "$INSTDIR"

  nsExec::ExecToLog 'taskkill /f /im "${PRODUCT_EXE}" 2>nul'
  Sleep 500

  File "dist\${PRODUCT_EXE}"

  CreateDirectory "$INSTDIR\fonts"
  SetOutPath "$INSTDIR\fonts"
  File "fonts\*.*"

  WriteRegStr HKLM "Software\${PRODUCT_NAME_EN}" "InstallDir" "$INSTDIR"
  WriteRegStr HKLM "Software\${PRODUCT_NAME_EN}" "Version" "${PRODUCT_VERSION}"

  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME_EN}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME_EN}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME_EN}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME_EN}" "Publisher" "${PRODUCT_PUBLISHER}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME_EN}" "DisplayIcon" '"$INSTDIR\${PRODUCT_EXE}"'
SectionEnd

Section "Install Nushu Font" SEC_FONT
  SetOutPath "$FONTSDIR"
  File "fonts\NotoTraditionalNushu-Regular.ttf"

  WriteRegStr HKLM "SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts" "Noto Traditional Nushu (TrueType)" "NotoTraditionalNushu-Regular.ttf"

  System::Call 'GDI32::AddFontResourceW(w "$FONTSDIR\NotoTraditionalNushu-Regular.ttf")i'
  SendMessage ${HWND_BROADCAST} ${WM_FONTCHANGE} 0 0
SectionEnd

Section "Create Shortcuts" SEC_SHORTCUTS
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "$INSTDIR\${PRODUCT_EXE}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
  CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\${PRODUCT_EXE}"
SectionEnd

Section "Auto Start" SEC_AUTOSTART
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "${PRODUCT_NAME_EN}" '"$INSTDIR\${PRODUCT_EXE}"'
SectionEnd

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_MAIN} "NushuIME main program (required)"
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_FONT} "Install Nushu font to system so all apps can display Nushu characters"
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_SHORTCUTS} "Create desktop and start menu shortcuts"
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_AUTOSTART} "Auto start NushuIME on boot"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

Section "Uninstall"
  nsExec::ExecToLog 'taskkill /f /im "${PRODUCT_EXE}" 2>nul'
  Sleep 500

  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "${PRODUCT_NAME_EN}"

  Delete "$DESKTOP\${PRODUCT_NAME}.lnk"
  RMDir /r "$SMPROGRAMS\${PRODUCT_NAME}"

  Delete "$INSTDIR\${PRODUCT_EXE}"
  RMDir /r "$INSTDIR\fonts"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"

  DeleteRegKey HKLM "Software\${PRODUCT_NAME_EN}"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME_EN}"

  MessageBox MB_YESNO "Also uninstall Nushu font from system?" IDYES RemoveFont IDNO SkipFont

  RemoveFont:
    Delete "$FONTSDIR\NotoTraditionalNushu-Regular.ttf"
    DeleteRegValue HKLM "SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts" "Noto Traditional Nushu (TrueType)"
    SendMessage ${HWND_BROADCAST} ${WM_FONTCHANGE} 0 0

  SkipFont:
SectionEnd
