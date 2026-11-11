# Zerua High-Precision Orbit Propagation module (HPOP)

The Zerua HPOP module is a high-fidelity numerical integration framework built on top of Basilisk. It is designed to propagate Earth-orbiting satellites with precision perturbations, including high-degree spherical harmonics, atmospheric drag, and third-body gravitational influences.

The module reads a user-provided satellite TLE or raw state vector and uses Basilisk's advanced simulation engine to propagate the orbit, using the NRLMSIS atmosphere density model for drag simulation and GGM03S Earth harmonics to accurately depict our planet's gravitational influence.

The code has been developed in an internship program for a BSc Physics thesis at Euskal Herriko Unibertsitatea (EHU) at ZeruaTech.

## Installation & Requirements

This module requires the Basilisk simulation framework.

1.  **Dependencies**:
    * `numpy`, `matplotlib`, `scipy`
    * `PyYAML` (for config parsing)
    * `skyfield` (for TLE and time-scale management)
    * `Basilisk` (ensure your `PYTHONPATH` is configured to point to your Basilisk build, follow the BSK install guide)
  
2. **Setup**: 
   Install the necessary packages via `pip`. In the case of Basilisk, check their [main page](https://avslab.github.io/basilisk/index.html) for more installation details.

## Usage

### Quick Start
You can run a propagation with minimal parameters or use a full configuration file:

```python
from hpop import HPOP_prop

# Quick run for 1 hour with basic perturbations
tle = "YOUR_TLE_STRING_HERE" 
# CAREFUL WITH FORMATTING !! Example TLE format (avoid tabulation, test TLE in the script for reference):            SAT-25544                                                                         1 25544U 98067A   25336.09225230  .00009217  00000-0  17381-3 0  9994             2 25544  51.6314 195.1903 0003639 193.8265 166.2625 15.49237019541206
pos, vel, time, _, _ = HPOP_prop(tle, bodies=3, drag=True, simTime=1.0)

```

### Advanced Configuration (config.yaml)
For research, use a configuration file to ensure reproducibility, for example:

```yaml
propagation:
  sim_time: 72.0
  integrator: "rkf45"
  abs_tolerance: 1e-12

forces:
  geopotential:
    degree: 100
  drag:
    enabled: true
    atmosphere_model: "MSIS"
```

For more `config` file examples and most useful use-cases, check the `configs/` folder. To run using a config file:

```python
# HPOP_prop automatically validates and applies defaults from config.yaml in case of missing parametres.
pos, vel, _, _, _ = HPOP_prop(tle, config_path="config.yaml")
```

## Citation
If you use this module in your research, please cite the Zerua framework, underlying Basilisk source and the accompanying dissertation piece it was developed for:

**Development of a High-Precision Orbit Propagation (HPOP) model for Zerua / Desarrollo de un modelo de Propagación de Órbitas de Alta Precisión (POAP) para Zerua** - *Xabier Gallastegui*


Depending on your specific integration, you may also want to cite the Basilisk Astrodynamics Software documentation.


