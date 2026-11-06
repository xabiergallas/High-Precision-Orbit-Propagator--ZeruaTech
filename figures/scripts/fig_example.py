"""Example figure script: propagate the ISS for 1 h."""
from pathlib import Path
from hpop import HPOP_prop

ROOT = Path(__file__).resolve().parents[2]
tle = (ROOT / "data/tle/ISS_example.txt").read_text()
pos, vel, t, drag, dens = HPOP_prop(tle, drag=True, simTime=1.0, show_plots=False)
print(f"Propagated {len(t)} steps")
# TODO: build the actual figure and save to ROOT / "manuscript/figures/"
