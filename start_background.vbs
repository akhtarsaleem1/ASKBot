Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "d:\Software\ASKBot"
' Run python hidden in the background (0 = hide window)
' We use python.exe -m askbot.main to ensure proper module resolution
WshShell.Run "python.exe -m askbot.main", 0, False
