NOTEBOOK = 'workshop.ipynb'
EXECUTED = 'workshop-executed.ipynb'
"""Run every notebook cell in a fresh kernel from this repository."""
from pathlib import Path
import asyncio
import sys
import nbformat
from nbclient import NotebookClient

root = Path(__file__).resolve().parent
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
source = root / NOTEBOOK
notebook = nbformat.read(source, as_version=4)
NotebookClient(notebook, timeout=600, kernel_name="python3",
               resources={"metadata": {"path": str(root)}}).execute()
nbformat.write(notebook, root / EXECUTED)
