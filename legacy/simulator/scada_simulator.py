"""
Legacy simulator/scada_simulator.py shim
Delegates execution directly to services/simulator/scada_simulator.py
"""
import sys
import os

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

sim_script = os.path.join(repo_root, "services", "simulator", "scada_simulator.py")
with open(sim_script, "r", encoding="utf-8") as f:
    code = compile(f.read(), sim_script, "exec")
    exec(code, globals())
