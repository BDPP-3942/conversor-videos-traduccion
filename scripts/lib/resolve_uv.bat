@echo off

rem Resolve the uv executable used by project wrappers.
rem The project-managed copy takes precedence over PATH for reproducibility.
set "UV_BIN="
if exist "%~dp0..\..\tools\uv\uv.exe" set "UV_BIN=%~dp0..\..\tools\uv\uv.exe"
if defined UV_BIN exit /b 0

for /f "delims=" %%U in ('where uv.exe 2^>nul') do if not defined UV_BIN set "UV_BIN=%%U"
if defined UV_BIN exit /b 0

exit /b 1
