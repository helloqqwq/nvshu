; ============================================
; 女书输入法 NSIS 安装程序
; ============================================

!define PRODUCT_NAME "女书输入法"
!define PRODUCT_NAME_EN "NushuIME"
!define PRODUCT_VERSION "2.0.0"
!define PRODUCT_PUBLISHER "NushuIME Project"
!define PRODUCT_EXE "NushuIME.exe"
!define PRODUCT_ICON "icon.ico"

; 安装程序设置
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "dist\${PRODUCT_NAME_EN}_Setup_${PRODUCT_VERSION}.exe"
InstallDir "$PROGRAMFILES\${PRODUCT_NAME_EN}"
InstallDirRegKey HKLM "Software\${PRODUCT_NAME_EN}" "InstallDir"
RequestExecutionLevel admin
SetCompressor /SOLID lzma

; 界面设置
!include "MUI2.nsh"
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; 页面
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "license.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "SimpChinese"

; ============================================
; 安装区段
; ============================================
Section "!主程序" SEC_MAIN
  SectionIn RO
  SetOutPath "$INSTDIR"
  
  ; 停止运行中的程序
  nsExec::ExecToLog 'taskkill /f /im "${PRODUCT_EXE}" 2>nul'
  Sleep 500
  
  ; 复制主程序
  File "dist\${PRODUCT_EXE}"
  
  ; 复制字体文件
  CreateDirectory "$INSTDIR\fonts"
  SetOutPath "$INSTDIR\fonts"
  File "fonts\*.*"
  
  ; 写入注册表
  WriteRegStr HKLM "Software\${PRODUCT_NAME_EN}" "InstallDir" "$INSTDIR"
  WriteRegStr HKLM "Software\${PRODUCT_NAME_EN}" "Version" "${PRODUCT_VERSION}"
  
  ; 创建卸载程序
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME_EN}" \
    "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME_EN}" \
    "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME_EN}" \
    "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME_EN}" \
    "Publisher" "${PRODUCT_PUBLISHER}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME_EN}" \
    "DisplayIcon" '"$INSTDIR\${PRODUCT_EXE}"'
SectionEnd

Section "安装女书字体" SEC_FONT
  ; 安装字体到系统
  SetOutPath "$FONTSDIR"
  File "fonts\NotoTraditionalNushu-Regular.ttf"
  
  ; 注册字体
  WriteRegStr HKLM "SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts" \
    "Noto Traditional Nushu (TrueType)" "NotoTraditionalNushu-Regular.ttf"
  
  ; 通知系统字体变更
  System::Call 'GDI32::AddFontResourceW(w "$FONTSDIR\NotoTraditionalNushu-Regular.ttf")i'
  SendMessage ${HWND_BROADCAST} ${WM_FONTCHANGE} 0 0
SectionEnd

Section "创建快捷方式" SEC_SHORTCUTS
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "$INSTDIR\${PRODUCT_EXE}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\卸载.lnk" "$INSTDIR\Uninstall.exe"
  CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\${PRODUCT_EXE}"
SectionEnd

Section "开机自启动" SEC_AUTOSTART
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" \
    "${PRODUCT_NAME_EN}" '"$INSTDIR\${PRODUCT_EXE}"'
SectionEnd

; ============================================
; 区段描述
; ============================================
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_MAIN} "女书输入法主程序（必选）"
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_FONT} "安装女书字体到系统，使所有应用都能正确显示女书字符"
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_SHORTCUTS} "创建桌面和开始菜单快捷方式"
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_AUTOSTART} "开机自动启动女书输入法"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; ============================================
; 卸载区段
; ============================================
Section "Uninstall"
  ; 停止运行中的程序
  nsExec::ExecToLog 'taskkill /f /im "${PRODUCT_EXE}" 2>nul'
  Sleep 500
  
  ; 删除自启动
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "${PRODUCT_NAME_EN}"
  
  ; 删除快捷方式
  Delete "$DESKTOP\${PRODUCT_NAME}.lnk"
  RMDir /r "$SMPROGRAMS\${PRODUCT_NAME}"
  
  ; 删除主程序和字体
  Delete "$INSTDIR\${PRODUCT_EXE}"
  RMDir /r "$INSTDIR\fonts"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
  
  ; 删除注册表
  DeleteRegKey HKLM "Software\${PRODUCT_NAME_EN}"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME_EN}"
  
  ; 询问是否删除系统字体
  MessageBox MB_YESNO "是否同时卸载女书字体？" IDYES RemoveFont IDNO SkipFont
  
  RemoveFont:
    Delete "$FONTSDIR\NotoTraditionalNushu-Regular.ttf"
    DeleteRegValue HKLM "SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts" \
      "Noto Traditional Nushu (TrueType)"
    SendMessage ${HWND_BROADCAST} ${WM_FONTCHANGE} 0 0
  
  SkipFont:
SectionEnd
