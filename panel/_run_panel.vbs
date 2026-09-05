' _run_panel.vbs - self-locating headless launcher for the Still-Life panel server.
' Pairs with scheduled task "StillLifePanelServer".
' IMPORTANT: keep this file pure ASCII (no Chinese comments) and CRLF line endings.
'   wscript on a GBK (Chinese-locale) Windows cannot reliably parse UTF-8 scripts
'   that contain non-ASCII characters -> VBScript compile error 800A0400.
' Resolution order for pythonw:
'   1) env var STILL_LIFE_PYTHONW (explicit override)
'   2) Doubao sandbox runtime: %LOCALAPPDATA%\Doubao\User Data\sandbox_runtime\bases\<hash>\python\pythonw.exe
'      (newest base wins; survives sandbox hash changes)
'   3) pythonw.exe on PATH
' Skill dir = the folder this script lives in (...still-life-illustrator\panel).
Option Explicit
Dim fso, shell, panelDir, scriptDir, pyw, basesDir, baseDir, subF, envPy, bestDate

Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

' 1. panel dir = this script's folder
scriptDir = WScript.ScriptFullName
panelDir = fso.GetParentFolderName(scriptDir)

' 2a. explicit env override
pyw = ""
envPy = shell.ExpandEnvironmentStrings("%STILL_LIFE_PYTHONW%")
If envPy <> "%STILL_LIFE_PYTHONW%" And envPy <> "" Then
    If fso.FileExists(envPy) Then pyw = envPy
End If

' 2b. Doubao sandbox runtime (any base, newest wins)
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

' 2c. fallback: pythonw on PATH
If pyw = "" Then pyw = "pythonw.exe"

shell.CurrentDirectory = panelDir
shell.Run """" & pyw & """ """ & panelDir & "\start_panel.py"" --no-browser", 0, False
