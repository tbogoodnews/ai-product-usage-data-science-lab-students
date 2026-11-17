# AI product analytics workshop

## Download data before setup

A fresh clone does not contain the ignored CSVs. Download `ai-product-usage-data-science-lab-students-v0.1.0.zip` from this private repository's `v0.1.0` release in a browser signed in with access, or use authenticated GitHub CLI from the repository root:

```powershell
gh release download v0.1.0 --repo tbogoodnews/ai-product-usage-data-science-lab-students --pattern ai-product-usage-data-science-lab-students-v0.1.0.zip
$expected = '02a8cb7cfe5d2deaaf3bf2600fe88522f80edbdd65c228eccc0a2a2f170aee30'
if ((Get-FileHash .\ai-product-usage-data-science-lab-students-v0.1.0.zip -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) { throw 'Checksum mismatch' }
Expand-Archive .\ai-product-usage-data-science-lab-students-v0.1.0.zip -DestinationPath .
```

The archive contains exactly 13 CSVs under `data\`, with no notebooks or configuration files. SHA-256 is checked above. The exercise notebook is in Git. GitHub access is needed only for initial download; dependency installation also needs package access. No account credentials or model calls are needed for notebook execution.

## Setup

Run `powershell -ExecutionPolicy Bypass -File .\setup.ps1` in this folder with Python 3.10+.
Initial package installation needs internet. To rerun offline from this folder:

```powershell
$python = '\\?\' + (Join-Path $PWD '.venv\Scripts\python.exe')
& $python run_notebook.py
```

The extended-length executable path avoids Windows dependency path-length limits.
Open workshop.ipynb, select the local Python environment, and complete the two TODO exercises.
The supplied CSVs are in data, relative to this repository. No other repository is needed.
The executed notebook runs setup and preserves the intentional exercise blanks.

All records are fictional accounts, not necessarily different people. Model availability,
quality and behavior are synthetic. Public price snapshots retrieved 2026-11-16 are applied
as an educational convention, not historical bills. AIC is usage, not revenue.
See schema.md and source_url fields in the price CSVs. The data and executed notebook
are present locally but Git-ignored because of their size.
