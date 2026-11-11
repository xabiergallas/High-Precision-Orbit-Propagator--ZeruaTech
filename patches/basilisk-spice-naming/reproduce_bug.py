"""Minimal reproduction: SPICE planet identifiers vs. barycenter-only kernels.

Creates the outer-planet gravity bodies through simIncludeGravBody, lets the
SpiceInterface evaluate them at one epoch and checks that every body received
a non-zero, finite position from SPICE.

Expected on unpatched Basilisk: "saturn", "uranus", "neptune" FAIL
    (SPICE is asked for the planet-centre IDs 699/799/899, which the default
    de430.bsp does not contain; only the barycenters 6/7/8 are there).
Expected with the fix: all bodies OK.

NOTE: written against the scenarioOrbitMultiBody.py API; adjust the body list
to whatever your Basilisk version accepts.  [TODO: paste observed output]
"""
import sys
import numpy as np
from Basilisk.utilities import SimulationBaseClass, macros, simIncludeGravBody

BODIES = ["sun", "jupiter barycenter", "saturn", "uranus", "neptune"]
# With the fix these shoould be: "saturn barycenter", "uranus barycenter", "neptune barycenter"


def main():
    scSim = SimulationBaseClass.SimBaseClass()
    proc = scSim.CreateNewProcess("proc")
    proc.addTask(scSim.CreateNewTask("task", macros.sec2nano(10.0)))

    gravFactory = simIncludeGravBody.gravBodyFactory()
    gravFactory.createBodies(*BODIES)
    spice = gravFactory.createSpiceInterface(time="2012 MAY 1 00:28:30.0")
    scSim.AddModelToTask("task", spice)

    scSim.InitializeSimulation()
    scSim.ConfigureStopTime(macros.sec2nano(10.0))
    scSim.ExecuteSimulation()

    failed = False
    for name, msg in zip(gravFactory.gravBodies, spice.planetStateOutMsgs):
        r = np.array(msg.read().PositionVector)  # m, relative to the SSB
        ok = np.all(np.isfinite(r)) and np.linalg.norm(r) > 0.0
        print(f"{name:22s} |r| = {np.linalg.norm(r):.6e} m  {'OK' if ok else 'FAIL'}")
        failed |= not ok

    gravFactory.unloadSpiceKernels()
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
