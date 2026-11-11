# Basilisk fix: outer-planet SPICE identifiers vs. barycenter-only kernels

| | |
|---|---|
| Upstream issue | TODO: link |
| Upstream PR | link (open) |
| Affected files | `src/Basilisk/utilities/simIncludeGravBody.py` (`BODY_DATA`, `createBody`, `createSaturn/Uranus/Neptune`); `examples/scenarioOrbitMultiBody.py` |
| Tested against | TODO: Basilisk version / commit |

## Problem
`gravBodyFactory` stores each body under its `identifier` (the `BODY_DATA` key), and
`createSpiceInterface` passes those identifiers to the SPICE module as the planet names
to look up. The default kernel set (`de430.bsp`, `naif0012.tls`, `de-403-masses.tpc`,
`pck00010.tpc`) only provides ephemerides up to the planetary **barycenters** for the
outer planets.

Jupiter and Mars were already registered as `"jupiter barycenter"` / `"mars barycenter"`,
but Saturn, Uranus and Neptune were not: their `planetName` already ended in
`"... barycenter_planet_data"`, while their `identifier` stayed `"saturn"`, `"uranus"`,
`"neptune"`. SPICE therefore resolved those to the planet-centre IDs (699, 799, 899), which
are not in the loaded kernels. Observed symptom: SPICE missing ephemeris data error code.



## How it was found
`scenarioOrbitMultiBody.py` with all outer planets enabled for the New Horizons case, while
studying how much the far planets perturb the trajectory.

## Fix
Identifiers (and dictionary keys, `createBody` look-up, `createSaturn/Uranus/Neptune`, and
the example's `createBodies(...)` call) renamed to `"saturn barycenter"`,
`"uranus barycenter"`, `"neptune barycenter"`, matching the existing Jupiter/Mars convention.
TODO: state whether the old names are kept as deprecated aliases.

## Reproduce
`python reproduce_bug.py` reports FAIL for the three planets before the fix, OK after.

## Apply
From a Basilisk checkout: `git am /path/to/0001-<name>.patch`
