; 该脚本使用 HM VNISEdit 脚本编辑器向导产生

; 安装程序初始定义常量
!define PRODUCT_NAME "NovalIDE"
!define PRODUCT_VERSION "1.2.2"
!define PRODUCT_PUBLISHER "wukan"
!define PRODUCT_WEB_SITE "http://www.genetalks.com"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\NovalIDE.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"
!define PRODUCT_PROJECT_FILE_EXTENSION ".nov"
!define PRODUCT_PROJECT_FILE "Noval.ProjectFile"
!define PRODUCT_PROJECT_FILE_DESCRIPTION "NovalIDE Project File"
!define PRODUCT_PROJECT_FILE_ICON_KEY "${PRODUCT_PROJECT_FILE}\DefaultIcon"
!define PRODUCT_PROJECT_FILE_OPEN_KEY "${PRODUCT_PROJECT_FILE}\shell\open\command"

SetCompressor lzma

; ------ MUI 现代界面定义 (1.67 版本以上兼容) ------
!include "MUI.nsh"

; MUI 预定义常量
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; 欢迎页面
!insertmacro MUI_PAGE_WELCOME
; 许可协议页面
!insertmacro MUI_PAGE_LICENSE "license.txt"
; 安装目录选择页面
!insertmacro MUI_PAGE_DIRECTORY
; 安装过程页面
!insertmacro MUI_PAGE_INSTFILES
; 安装完成页面
!define MUI_FINISHPAGE_RUN "$INSTDIR\NovalIDE.exe"
!insertmacro MUI_PAGE_FINISH

; 安装卸载过程页面
!insertmacro MUI_UNPAGE_INSTFILES

; 安装界面包含的语言设置
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "SimpChinese"

; 安装预释放文件
!insertmacro MUI_RESERVEFILE_INSTALLOPTIONS
; ------ MUI 现代界面定义结束 ------

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "NovalIDE_Setup_${PRODUCT_VERSION}.exe"
InstallDir "$PROGRAMFILES\NovalIDE"
InstallDirRegKey HKLM "${PRODUCT_UNINST_KEY}" "UninstallString"
ShowInstDetails show
ShowUnInstDetails show

Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer
  CreateDirectory "$SMPROGRAMS\NovalIDE"
  CreateShortCut "$SMPROGRAMS\NovalIDE\NovalIDE.lnk" "$INSTDIR\NovalIDE.exe"
  CreateShortCut "$DESKTOP\NovalIDE.lnk" "$INSTDIR\NovalIDE.exe"
  File "dist\${PRODUCT_NAME}\win32process.pyd"
  File "dist\${PRODUCT_NAME}\win32pipe.pyd"
  File "dist\${PRODUCT_NAME}\win32gui.pyd"
  File "dist\${PRODUCT_NAME}\win32file.pyd"
  File "dist\${PRODUCT_NAME}\win32evtlog.pyd"
  File "dist\${PRODUCT_NAME}\win32event.pyd"
  File "dist\${PRODUCT_NAME}\win32api.pyd"
  File "dist\${PRODUCT_NAME}\version.txt"
  File "dist\${PRODUCT_NAME}\template.xml"
  File "dist\${PRODUCT_NAME}\unicodedata.pyd"

  File "dist\${PRODUCT_NAME}\tcl86t.dll"
  File "dist\${PRODUCT_NAME}\tk86t.dll"
  File "dist\${PRODUCT_NAME}\select.pyd"
  File "dist\${PRODUCT_NAME}\pywintypes36.dll"
  File "dist\${PRODUCT_NAME}\pythoncom36.dll"
  File "dist\${PRODUCT_NAME}\python36.dll"
  File "dist\${PRODUCT_NAME}\pyexpat.pyd"
  File "dist\${PRODUCT_NAME}\_sqlite3.pyd"
  File "dist\${PRODUCT_NAME}\sqlite3.dll"
  File "dist\${PRODUCT_NAME}\NovalIDE.exe"
  File "dist\${PRODUCT_NAME}\NovalIDE.exe.manifest"
  File "dist\${PRODUCT_NAME}\MSVCP140.dll"
  File "dist\${PRODUCT_NAME}\base_library.zip"
  File "dist\${PRODUCT_NAME}\_bz2.pyd"
  File "dist\${PRODUCT_NAME}\sip.pyd"
  File "dist\${PRODUCT_NAME}\API-MS-Win-Core-SysInfo-L1-1-0.dll"
  File "dist\${PRODUCT_NAME}\API-MS-Win-Core-Synch-L1-1-0.dll"
  File "dist\${PRODUCT_NAME}\API-MS-Win-Core-String-L1-1-0.dll"
  File "dist\${PRODUCT_NAME}\API-MS-Win-Core-Profile-L1-1-0.dll"
  File "dist\${PRODUCT_NAME}\API-MS-Win-Core-ProcessThreads-L1-1-0.dll"
  File "dist\${PRODUCT_NAME}\API-MS-Win-Core-ProcessEnvironment-L1-1-0.dll"
  File "dist\${PRODUCT_NAME}\API-MS-Win-Core-Memory-L1-1-0.dll"
  File "dist\${PRODUCT_NAME}\API-MS-Win-Core-Localization-L1-2-0.dll"
  File "dist\${PRODUCT_NAME}\API-MS-Win-Core-LibraryLoader-L1-1-0.dll"
  File "dist\${PRODUCT_NAME}\API-MS-Win-Core-Interlocked-L1-1-0.dll"
  File "dist\${PRODUCT_NAME}\API-MS-Win-Core-Handle-L1-1-0.dll"
  File "dist\${PRODUCT_NAME}\API-MS-Win-Core-ErrorHandling-L1-1-0.dll"
  File "dist\${PRODUCT_NAME}\API-MS-Win-Core-Debug-L1-1-0.dll"
  File "dist\${PRODUCT_NAME}\_win32sysloader.pyd"
  File "dist\${PRODUCT_NAME}\_tkinter.pyd"
  File "dist\${PRODUCT_NAME}\_ssl.pyd"
  File "dist\${PRODUCT_NAME}\_socket.pyd"
  File "dist\${PRODUCT_NAME}\_hashlib.pyd"
  File "dist\${PRODUCT_NAME}\_ctypes.pyd"
  File "dist\${PRODUCT_NAME}\_multiprocessing.pyd"
  File "dist\${PRODUCT_NAME}\noval.ico"

  SetOutPath "$INSTDIR\noval"
  File /r "dist\${PRODUCT_NAME}\noval\*.*"

  SetOutPath "$INSTDIR\tcl"
  File /r "dist\${PRODUCT_NAME}\tcl\*.*"

  SetOutPath "$INSTDIR\tk"
  File /r "dist\${PRODUCT_NAME}\tk\*.*"

  SetOutPath "$INSTDIR\psutil"
  File /r "dist\${PRODUCT_NAME}\psutil\_psutil_windows.cp36-win32.pyd"

  SetOutPath "$INSTDIR\locale"
  File /r "dist\${PRODUCT_NAME}\locale\*.*"

  SetOutPath "$INSTDIR\lib2to3"
  File /r "dist\${PRODUCT_NAME}\lib2to3\*.*"

  SetOutPath "$INSTDIR\certifi"
  File /r "dist\${PRODUCT_NAME}\certifi\*.*"

  SetOutPath "$INSTDIR\PIL"
  File /r "dist\${PRODUCT_NAME}\PIL\*.*"

  SetOutPath "$INSTDIR\tkdnd"
  File /r "dist\${PRODUCT_NAME}\tkdnd\*.*"

  SetOutPath "$INSTDIR\win32com\shell"
  File /r "dist\${PRODUCT_NAME}\win32com\shell\*.*"

SectionEnd

Section -AdditionalIcons
  WriteIniStr "$INSTDIR\${PRODUCT_NAME}.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
  CreateShortCut "$SMPROGRAMS\NovalIDE\Website.lnk" "$INSTDIR\${PRODUCT_NAME}.url"
  CreateShortCut "$SMPROGRAMS\NovalIDE\Uninstall.lnk" "$INSTDIR\uninst.exe"
SectionEnd

Section -Post
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKCR "${PRODUCT_PROJECT_FILE_EXTENSION}" "" "${PRODUCT_PROJECT_FILE}"
  WriteRegStr HKCR "${PRODUCT_PROJECT_FILE}" "" "${PRODUCT_PROJECT_FILE_DESCRIPTION}"
  WriteRegStr HKCR "${PRODUCT_PROJECT_FILE_ICON_KEY}" "" "$INSTDIR\noval\bmp_source\project.ico"
  WriteRegStr HKCR "${PRODUCT_PROJECT_FILE_OPEN_KEY}" "" "$INSTDIR\NovalIDE.exe $\"%1$\""
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\NovalIDE.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\NovalIDE.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
SectionEnd

/******************************
 *  以下是安装程序的卸载部分  *
 ******************************/

Section Uninstall
  Delete "$INSTDIR\${PRODUCT_NAME}.url"
  Delete "$INSTDIR\uninst.exe"
  Delete "$INSTDIR\_ctypes.pyd"
  Delete "$INSTDIR\_hashlib.pyd"
  Delete "$INSTDIR\_socket.pyd"
  Delete "$INSTDIR\_ssl.pyd"
  Delete "$INSTDIR\_tkinter.pyd"
  Delete "$INSTDIR\_win32sysloader.pyd"
  Delete "$INSTDIR\psutil._psutil_windows.pyd"
  Delete "$INSTDIR\wxmsw30u_webview_vc90.dll"
  Delete "$INSTDIR\API-MS-Win-Core-Debug-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-DelayLoad-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-ErrorHandling-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-Handle-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-Interlocked-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-IO-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-LibraryLoader-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-Localization-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-LocalRegistry-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-Memory-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-Misc-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-ProcessEnvironment-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-ProcessThreads-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-Profile-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-String-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-Synch-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-SysInfo-L1-1-0.dll"
  Delete "$INSTDIR\_bz2.pyd"
  Delete "$INSTDIR\base_library.zip"
  Delete "$INSTDIR\NovalIDE.exe"
  Delete "$INSTDIR\NovalIDE.exe.manifest"
  Delete "$INSTDIR\pyexpat.pyd"
  Delete "$INSTDIR\python36.dll"
  Delete "$INSTDIR\pywintypes36.dll"
  Delete "$INSTDIR\pythoncom36.dll"
  Delete "$INSTDIR\select.pyd"
  Delete "$INSTDIR\tcl86t.dll"
  Delete "$INSTDIR\tk86t.dll"
  Delete "$INSTDIR\unicodedata.pyd"
  Delete "$INSTDIR\version.txt"
  Delete "$INSTDIR\template.xml"
  Delete "$INSTDIR\_multiprocessing.pyd"
  Delete "$INSTDIR\win32api.pyd"
  Delete "$INSTDIR\win32com.shell.shell.pyd"
  Delete "$INSTDIR\win32event.pyd"
  Delete "$INSTDIR\win32evtlog.pyd"
  Delete "$INSTDIR\win32file.pyd"
  Delete "$INSTDIR\win32gui.pyd"
  Delete "$INSTDIR\win32pipe.pyd"
  Delete "$INSTDIR\win32process.pyd"
  Delete "$INSTDIR\winxpgui.pyd"
  Delete "$INSTDIR\_sqlite3.pyd"
  Delete "$INSTDIR\sqlite3.dll"
  Delete "$INSTDIR\_sqlite3.pyd"
  Delete "$INSTDIR\sqlite3.dll"
  Delete "$INSTDIR\NovalIDE.exe.log"
  Delete "$INSTDIR\noval.ico"
  Delete "$INSTDIR\sip.pyd"
  Delete "$INSTDIR\api-ms-win-core-localization-l1-2-0.dll"
  Delete "$INSTDIR\MSVCP140.dll"

  Delete "$SMPROGRAMS\NovalIDE\Uninstall.lnk"
  Delete "$SMPROGRAMS\NovalIDE\Website.lnk"
  Delete "$DESKTOP\NovalIDE.lnk"
  Delete "$SMPROGRAMS\NovalIDE\NovalIDE.lnk"

  RMDir "$SMPROGRAMS\NovalIDE"

  RMDir /r "$INSTDIR\tcl"
  RMDir /r "$INSTDIR\noval"

  RMDir /r "$INSTDIR\tk"
  RMDir /r "$INSTDIR\psutil"
  RMDir /r "$INSTDIR\locale"
  RMDir /r "$INSTDIR\lib2to3"
  RMDir /r "$INSTDIR\certifi"
  RMDir /r "$INSTDIR\PIL"
  RMDir /r "$INSTDIR\tkdnd"
  RMDir /r "$INSTDIR\win32com"

  RMDir "$INSTDIR"
  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  SetAutoClose true
SectionEnd

#-- 根据 NSIS 脚本编辑规则，所有 Function 区段必须放置在 Section 区段之后编写，以避免安装程序出现未可预知的问题。--#

Function .onInit
  IfFileExists "$INSTDIR\config.ini" 0 +2
  Goto end
  !insertmacro MUI_LANGDLL_DISPLAY
end:
FunctionEnd

Function un.onInit
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "您确实要完全移除 $(^Name) ，及其所有的组件？" IDYES +2
  Abort
FunctionEnd

Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "$(^Name) 已成功地从您的计算机移除。"
FunctionEnd

Function .onInstSuccess
  IntCmp $Language 2052 SetLangChinese
  IntCmp $Language 1033 SetLangEnglish

SetLangChinese:
  WriteINIStr "$INSTDIR\config.ini" "IDE" "Language" "46"
  Goto SetLangEnd

SetLangEnglish:
  WriteINIStr "$INSTDIR\config.ini" "IDE" "Language" "60"

SetLangEnd:
FunctionEnd
