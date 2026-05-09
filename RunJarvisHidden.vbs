' ============================================================================
' RunJarvisHidden.vbs  —  J.A.R.V.I.S. Smart Toggle Launcher
' Bind this to a keyboard shortcut (e.g. Ctrl+Alt+J).
' First invocation  → starts Ollama + countdown → jarvis.py
' Second invocation → terminates jarvis.py (and countdown.py if still running)
' ============================================================================
Option Explicit

Dim oShell, oFSO, sDir
Set oShell = CreateObject("WScript.Shell")
Set oFSO   = CreateObject("Scripting.FileSystemObject")

' Derive the folder this .vbs lives in so all paths are absolute.
' When triggered by a keyboard shortcut the CWD is unreliable.
sDir = oFSO.GetParentFolderName(WScript.ScriptFullName)

If IsJarvisRunning() Then
    CloseJarvis
Else
    LaunchJarvis
End If

' ─────────────────────────────────────────────────────── IsJarvisRunning ────

Function IsJarvisRunning()
    ' Uses WMI process enumeration only — no AppActivate side-effect
    ' (AppActivate would steal window focus every time the shortcut is pressed).
    Dim oWMI, oProcs, oProc
    IsJarvisRunning = False

    On Error Resume Next
    Set oWMI   = GetObject("winmgmts:\\.\root\cimv2")
    Set oProcs = oWMI.ExecQuery( _
        "SELECT * FROM Win32_Process " & _
        "WHERE Name='python.exe' OR Name='pythonw.exe'")

    For Each oProc In oProcs
        If InStr(LCase(oProc.CommandLine), "jarvis.py") > 0 Then
            IsJarvisRunning = True
            Exit Function
        End If
    Next
    On Error GoTo 0
End Function

' ────────────────────────────────────────────────────────── LaunchJarvis ────

Sub LaunchJarvis()
    Dim sBat, sPython, sCountdown

    sBat = sDir & "\Start_Jarvis.bat"

    ' --- Strategy A: run the full bat (starts Ollama + countdown) ----------
    ' Verify the bat exists before trying it.
    If oFSO.FileExists(sBat) Then
        ' Window style 0 = hidden console; the countdown CTk window still appears.
        ' bWaitOnReturn = False so the VBS exits immediately.
        oShell.CurrentDirectory = sDir
        oShell.Run "cmd /c """ & sBat & """", 0, False
        Exit Sub
    End If

    ' --- Strategy B: bat not found — try to run countdown.py directly ------
    ' This path should never be needed but acts as a safety net.
    sPython    = FindPythonExe()
    sCountdown = sDir & "\countdown.py"

    If sPython <> "" And oFSO.FileExists(sCountdown) Then
        oShell.Run """" & sPython & """ """ & sCountdown & """", 0, False
    Else
        MsgBox "J.A.R.V.I.S.: Could not locate Start_Jarvis.bat or countdown.py in:" & _
               vbCrLf & sDir, vbExclamation, "J.A.R.V.I.S. Launcher"
    End If
End Sub

' ─────────────────────────────────────────────────────────── CloseJarvis ────

Sub CloseJarvis()
    Dim oWMI, oProcs, oProc, sCmdLine

    On Error Resume Next
    Set oWMI   = GetObject("winmgmts:\\.\root\cimv2")
    Set oProcs = oWMI.ExecQuery( _
        "SELECT * FROM Win32_Process " & _
        "WHERE Name='python.exe' OR Name='pythonw.exe'")

    ' Terminate any python process running jarvis.py OR countdown.py
    For Each oProc In oProcs
        sCmdLine = LCase(oProc.CommandLine)
        If InStr(sCmdLine, "jarvis.py") > 0 Or InStr(sCmdLine, "countdown.py") > 0 Then
            oProc.Terminate
        End If
    Next
    On Error GoTo 0

    ' Give the OS 400 ms to clean up before we try AppActivate
    WScript.Sleep 400

    ' Belt-and-suspenders: send Alt+F4 if the window is still registered
    If oShell.AppActivate("J.A.R.V.I.S. | PERSONAL ASSISTANT") Then
        WScript.Sleep 150
        oShell.SendKeys "%{F4}"
    End If
    ' Also close the boot screen if it is somehow still open
    If oShell.AppActivate("J.A.R.V.I.S.  -  NEURAL BOOT SEQUENCE") Or _
       oShell.AppActivate("J.A.R.V.I.S. - NEURAL BOOT SEQUENCE") Then
        WScript.Sleep 100
        oShell.SendKeys "%{F4}"
    End If
End Sub

' ─────────────────────────────────────────────────────────── FindPythonExe ──

Function FindPythonExe()
    '
    ' Returns the full path to a Python executable, or "" if none found.
    ' Checks in priority order:
    '   1. py.exe launcher at %SystemRoot%  (C:\Windows\py.exe)
    '   2. User-local installs  (%LOCALAPPDATA%\Programs\Python\...)
    '   3. System-wide installs (C:\PythonXYZ\  and  C:\Program Files\PythonXYZ\)
    '   4. Microsoft Store alias (%LOCALAPPDATA%\Microsoft\WindowsApps\)
    '
    Dim sLocal, sSysRoot, i
    Dim aVersions(8)
    aVersions(0) = "313"
    aVersions(1) = "312"
    aVersions(2) = "311"
    aVersions(3) = "310"
    aVersions(4) = "39"
    aVersions(5) = "38"
    aVersions(6) = "313"
    aVersions(7) = "312"
    aVersions(8) = "311"

    FindPythonExe = ""

    ' 1. py.exe launcher
    sSysRoot = oShell.ExpandEnvironmentStrings("%SystemRoot%") & "\py.exe"
    If oFSO.FileExists(sSysRoot) Then
        FindPythonExe = sSysRoot
        Exit Function
    End If

    ' 2. User-local installs
    sLocal = oShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\"
    For i = 0 To 5
        Dim sCandidate
        sCandidate = sLocal & "Python" & aVersions(i) & "\python.exe"
        If oFSO.FileExists(sCandidate) Then
            FindPythonExe = sCandidate
            Exit Function
        End If
    Next

    ' 3. System-wide installs
    For i = 0 To 5
        Dim sCandSys1, sCandSys2
        sCandSys1 = "C:\Python" & aVersions(i) & "\python.exe"
        sCandSys2 = "C:\Program Files\Python" & aVersions(i) & "\python.exe"
        If oFSO.FileExists(sCandSys1) Then
            FindPythonExe = sCandSys1
            Exit Function
        End If
        If oFSO.FileExists(sCandSys2) Then
            FindPythonExe = sCandSys2
            Exit Function
        End If
    Next

    ' 4. Microsoft Store Python
    Dim sStore
    sStore = oShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & _
             "\Microsoft\WindowsApps\python.exe"
    If oFSO.FileExists(sStore) Then
        FindPythonExe = sStore
        Exit Function
    End If
End Function