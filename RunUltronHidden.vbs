' ============================================================================
' RunUltronHidden.vbs  —  U.L.T.R.O.N. Smart Toggle Launcher
' Bind this to a keyboard shortcut (e.g. Ctrl+Alt+J).
' First invocation  → starts Ollama + boot → ultron_ui.py
' Second invocation → terminates ultron_ui.py (and ultron_boot.py if still running)
' ============================================================================
Option Explicit

Dim oShell, oFSO, sDir
Set oShell = CreateObject("WScript.Shell")
Set oFSO   = CreateObject("Scripting.FileSystemObject")

' Derive the folder this .vbs lives in so all paths are absolute.
' When triggered by a keyboard shortcut the CWD is unreliable.
sDir = oFSO.GetParentFolderName(WScript.ScriptFullName)

If IsUltronRunning() Then
    CloseUltron
Else
    LaunchUltron
End If

' ─────────────────────────────────────────────────────── IsUltronRunning ────

Function IsUltronRunning()
    ' Uses WMI process enumeration only — no AppActivate side-effect
    ' (AppActivate would steal window focus every time the shortcut is pressed).
    Dim oWMI, oProcs, oProc
    IsUltronRunning = False

    On Error Resume Next
    Set oWMI   = GetObject("winmgmts:\\.\root\cimv2")
    Set oProcs = oWMI.ExecQuery( _
        "SELECT * FROM Win32_Process " & _
        "WHERE Name='python.exe' OR Name='pythonw.exe'")

    For Each oProc In oProcs
        If InStr(LCase(oProc.CommandLine), "ultron_main.py") > 0 Then
            IsUltronRunning = True
            Exit Function
        End If
    Next
    On Error GoTo 0
End Function

' ────────────────────────────────────────────────────────── LaunchUltron ────

Sub LaunchUltron()
    Dim sBat, sPython, sBoot

    sBat = sDir & "\Start_Ultron.bat"

    ' --- Strategy A: run the full bat (starts Ollama + boot) ----------
    ' Verify the bat exists before trying it.
    If oFSO.FileExists(sBat) Then
        ' Window style 0 = hidden console; the boot screen still appears.
        ' bWaitOnReturn = False so the VBS exits immediately.
        oShell.CurrentDirectory = sDir
        oShell.Run "cmd /c """ & sBat & """", 0, False
        Exit Sub
    End If

    ' --- Strategy B: bat not found — try to run ultron_boot.py directly ------
    ' This path should never be needed but acts as a safety net.
    sPython    = FindPythonExe()
    sBoot = sDir & "\ultron_boot.py"

    if sPython <> "" And oFSO.FileExists(sBoot) Then
        oShell.Run """" & sPython & """ """ & sBoot & """", 0, False
    Else
        MsgBox "U.L.T.R.O.N.: Could not locate Start_Ultron.bat or ultron_boot.py in:" & _
               vbCrLf & sDir, vbExclamation, "U.L.T.R.O.N. Launcher"
    End If
End Sub

' ─────────────────────────────────────────────────────────── CloseUltron ────

Sub CloseUltron()
    Dim oWMI, oProcs, oProc, sCmdLine

    On Error Resume Next
    Set oWMI   = GetObject("winmgmts:\\.\root\cimv2")
    Set oProcs = oWMI.ExecQuery( _
        "SELECT * FROM Win32_Process " & _
        "WHERE Name='python.exe' OR Name='pythonw.exe'")

    ' Terminate any python process running ultron_main.py OR ultron_boot.py
    For Each oProc In oProcs
        sCmdLine = LCase(oProc.CommandLine)
        If InStr(sCmdLine, "ultron_main.py") > 0 Or InStr(sCmdLine, "ultron_boot.py") > 0 Then
            oProc.Terminate
        End If
    Next
    On Error GoTo 0

    ' Give the OS 400 ms to clean up before we try AppActivate
    WScript.Sleep 400

    ' Belt-and-suspenders: send Alt+F4 if the window is still registered
    If oShell.AppActivate("U.L.T.R.O.N. | PERSONAL ASSISTANT") Then
        WScript.Sleep 150
        oShell.SendKeys "%{F4}"
    End If
    ' Also close the boot screen if it is somehow still open
    If oShell.AppActivate("U.L.T.R.O.N.  —  NEURAL BOOT SEQUENCE") Then
        WScript.Sleep 100
        oShell.SendKeys "%{F4}"
    End If
End Sub

' ─────────────────────────────────────────────────────────── FindPythonExe ──

Function FindPythonExe()
    Dim sLocal, sSysRoot, i
    Dim aVersions(5)
    aVersions(0) = "313"
    aVersions(1) = "312"
    aVersions(2) = "311"
    aVersions(3) = "310"
    aVersions(4) = "39"
    aVersions(5) = "38"

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
