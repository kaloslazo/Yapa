"""Levanta el motor con la semana de demo sin configurar PYTHONPATH: python api/tools/servir_demo.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.argv = [sys.argv[0], "--demo", *sys.argv[1:]]

from yapa_sdd.web.__main__ import main  # noqa: E402

main()
