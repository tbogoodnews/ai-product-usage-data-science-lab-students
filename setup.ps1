$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
python -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Environment creation failed' }
$python = '\\?\' + (Join-Path $PSScriptRoot '.venv\Scripts\python.exe')
& $python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
& $python run_notebook.py
if ($LASTEXITCODE -ne 0) { throw 'Notebook execution failed' }
