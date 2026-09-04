' _run_panel.vbs —— 静物插画面板常驻无窗口启动器（配合计划任务 StillLifePanelServer 使用）
' 自定位设计（无硬编码用户名/Profile/沙箱hash，换机器、豆包升级沙箱后依然可用）：
'   1. 技能目录 = 本脚本所在目录（...still-life-illustrator\panel）
'   2. pythonw 解析优先级：
'      a) 环境变量 STILL_LIFE_PYTHONW 显式指定
'      b) 豆包沙箱运行时 %LOCALAPPDATA%\Doubao\User Data\sandbox_runtime\bases\<hash>\python\pythonw.exe（取最新 base）
'      c) PATH 中的 pythonw.exe
Option Explicit
Dim fso, shell, panelDir, scriptDir, pyw, basesDir, baseDir, subF, envPy, bestDate

Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

' 1. 技能 panel 目录 = 本脚本所在目录
scriptDir = WScript.ScriptFullName
panelDir = fso.GetParentFolderName(scriptDir)

' 2a. 环境变量显式指定
pyw = ""
envPy = shell.ExpandEnvironmentStrings("%STILL_LIFE_PYTHONW%")
If envPy <> "%STILL_LIFE_PYTHONW%" And envPy <> "" Then
    If fso.FileExists(envPy) Then pyw = envPy
End If

' 2b. 豆包沙箱运行时（任一 base，取日期最新的）
If pyw = "" Then
    basesDir = shell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Doubao\User Data\sandbox_runtime\bases"
    If fso.FolderExists(basesDir) Then
        bestDate = ""
        For Each baseDir In fso.GetFolder(basesDir).SubFolders
            If fso.FileExists(baseDir.Path & "\python\pythonw.exe") Then
                If bestDate = "" Or baseDir.DateLastModified > bestDate Then
                    bestDate = baseDir.DateLastModified
                    pyw = baseDir.Path & "\python\pythonw.exe"
                End If
            End If
        Next
    End If
End If

' 2c. 回退 PATH 中的 pythonw
If pyw = "" Then pyw = "pythonw.exe"

shell.CurrentDirectory = panelDir
shell.Run """" & pyw & """ """ & panelDir & "\start_panel.py"" --no-browser", 0, False
