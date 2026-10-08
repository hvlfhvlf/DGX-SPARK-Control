import runpy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
runpy.run_module('spark_control.setup', run_name='__main__')
