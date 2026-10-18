"""Expose exploration through the investigator application's navigation."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).resolve().parents[1] / 'visual_evidence.py'), run_name='__main__')
