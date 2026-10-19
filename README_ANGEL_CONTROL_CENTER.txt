LOCALAI-ANGEL CONTROL CENTER - BUTTON LAUNCH FIX

Why the buttons failed:
The prior version passed a BAT path to cmd.exe /k with fragile quoting. CMD interpreted the quote characters as part of the command instead of running the BAT.

Fix:
The UI now uses Windows os.startfile() to launch each BAT through its registered command processor. It also finds the project folder next to the EXE by checking for the three expected BAT files.

Install/rebuild:
1. Extract these files into D:\GitHub\LocalAI-Angel.
2. Keep INSTALL_ANGEL_V1.0.0.bat, START_ANGEL.bat, STOP_ANGEL.bat, and the Compose YAML files in that folder.
3. Run BUILD_ANGEL_CONTROL_CENTER_EXE.bat.
4. Copy dist\AngelControlCenter.exe into the repository root, beside the three BAT files.
5. Run that EXE and test Stop, Start, and Install/Repair.

This ZIP contains source and a build script, not a precompiled EXE.
