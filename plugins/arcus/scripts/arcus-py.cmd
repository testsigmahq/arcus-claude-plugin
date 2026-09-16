: << 'CMDBLOCK'
@echo off
REM Cross-platform polyglot launcher: resolve a Python 3.9+ interpreter and run
REM the script named by the first argument.
REM
REM cmd.exe runs the batch block below. A POSIX shell treats ":" as a no-op and
REM swallows the block as a heredoc, then runs the sh section at the bottom, so
REM one file serves whichever shell Claude Code uses. The polyglot pattern is
REM borrowed from the superpowers plugin's run-hook.cmd.
REM
REM Windows has no "python3" on PATH: the python.org installer ships python.exe
REM and the py launcher, and the name "python3" is normally a Microsoft Store
REM app-execution alias that opens the Store and exits non-zero. So probe each
REM candidate by actually running it, preferring "py -3", which the official
REM installer always registers.
REM
REM Labels rather than parenthesised blocks throughout: %ERRORLEVEL% inside a
REM block is expanded when the block is parsed, not when it runs.
REM
REM Usage: arcus-py.cmd <script.py> [args...]

setlocal
if "%~1"=="" goto :no_script
set "SCRIPT=%~1"
shift

py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>nul
if not errorlevel 1 goto :use_py

python -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>nul
if not errorlevel 1 goto :use_python

python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>nul
if not errorlevel 1 goto :use_python3

REM Nothing usable. Exit 0 so a missing interpreter disables capture instead of
REM breaking the session.
echo arcus: no Python 3.9+ found (tried py -3, python, python3). Capture is disabled. 1>&2
exit /b 0

:use_py
py -3 "%SCRIPT%" %1 %2 %3 %4 %5 %6 %7 %8 %9
exit /b %ERRORLEVEL%

:use_python
python "%SCRIPT%" %1 %2 %3 %4 %5 %6 %7 %8 %9
exit /b %ERRORLEVEL%

:use_python3
python3 "%SCRIPT%" %1 %2 %3 %4 %5 %6 %7 %8 %9
exit /b %ERRORLEVEL%

:no_script
echo arcus-py: missing script path 1>&2
exit /b 1
CMDBLOCK

# --- POSIX shells (macOS, Linux, Git Bash) ---------------------------------
# Probe each candidate by running it rather than trusting `command -v`: on
# Windows the name "python3" can resolve to a Microsoft Store alias that answers
# `command -v` but is not an interpreter.
for candidate in python3 python py; do
  command -v "$candidate" >/dev/null 2>&1 || continue
  "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1 || continue
  exec "$candidate" "$@"
done

echo "arcus: no Python 3.9+ found (tried python3, python, py). Capture is disabled." >&2
exit 0
