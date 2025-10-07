@echo off
setlocal

set "PROJECT_DIR=%~dp0..\"

if exist "%PROJECT_DIR%data\samples\load_samples.py" (
    cd /d "%PROJECT_DIR%backend"
    call venv\Scripts\activate
    python "%PROJECT_DIR%data\samples\load_samples.py"
    echo Sample data loaded
) else (
    echo Sample data script not found
)

endlocal
