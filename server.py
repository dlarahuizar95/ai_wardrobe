#!/usr/bin/env python3
"""Atajo: python3 server.py  == levantar pipeline/servidor.py con el .env cargado (y regenerar mi_closet.html)."""
import os, sys, subprocess
from pathlib import Path
RAIZ = Path(__file__).resolve().parent
for linea in (RAIZ / ".env").read_text().splitlines():
    if "=" in linea and not linea.startswith("#"):
        k, v = linea.split("=", 1); os.environ.setdefault(k.strip(), v.strip())
py = RAIZ / ".venv" / "bin" / "python"
subprocess.run([str(py), "-W", "ignore", str(RAIZ / "pipeline" / "generar_closet_total.py")], check=True)
os.execv(str(py), [str(py), "-W", "ignore", str(RAIZ / "pipeline" / "servidor.py")])
