import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from datetime import datetime
import calendar
import matplotlib.pyplot as plt
import numpy as np
# Skyfield TLE reading and TEME ---> GCRS
from skyfield.api import load, EarthSatellite

# Basilisk
from Basilisk import __path__
# simulation (atmo and drag)
from Basilisk.simulation import (
    dragDynamicEffector,
    exponentialAtmosphere,
    msisAtmosphere,
    spacecraft,
    svIntegrators
)
# Location of supporting data.
from Basilisk.topLevelModules import pyswice
# Support files
from Basilisk.utilities import (
    SimulationBaseClass, macros,
    orbitalMotion, tleHandling,
    simSetPlanetEnvironment,
    simIncludeGravBody,
    unitTestSupport
    )
from Basilisk.architecture import (astroConstants,
                                   messaging
                                   )
from Basilisk.utilities.supportDataTools.dataFetcher import get_path, DataFile

def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load HPOP configuration from YAML or JSON file.

    Args:
        config_path: Path to .yaml, .yml, or .json file

    Returns:
        Configuration dictionary
    """
    config_path = Path(config_path)

    if config_path.suffix in ('.yaml', '.yml'):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    elif config_path.suffix == '.json':
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        raise ValueError(f"Unsupported config format: {config_path.suffix}")

    return config


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and apply defaults to configuration. Defaults only apply if no configuration is provided at all or
    the file isn't properly formatted/missing elements so the simulation doesn't fail
    """
    defaults = {
        'propagation': {
            'time_step': 5.0,
            'sim_time': 12.0,
            'output_points': 2000,
            'start_date': None,
            'integrator': 'rk4',
            'rel_tolerance': 1e-4,
            'abs_tolerance': 1e-8
        },
        'spacecraft': {
            'mass': 1000.0,
        },
        'forces': {
            'geopotential': {
                'enabled': True,
                'degree': 100
            },
            'drag': {
                'enabled': False,
                'atmosphere_model': 'MSIS',
                'drag_coefficient': 2.2,
                'projected_area': 2.5,
                'f107': 100.0,
                'ap': 10.0
            },
            'third_body': {
                'enabled': True,
                'bodies': ['sun', 'moon', 'jupiter barycenter']
            } #bodies with the biggest influence as default
        },
        'deorbiting': {
            'enabled': True,
            'altitude_limit_km': 100.0
        }
    }

    merged = _merge_dicts(defaults, config)

    if merged['forces']['geopotential']['degree'] < 0:
        raise ValueError("Geopotential degree must be >= 0")

    if merged['spacecraft']['mass'] <= 0:
        raise ValueError("Spacecraft mass must be > 0")

    valid_bodies = [
        'sun', 'moon', 'mercury', 'venus', 'earth', 'mars barycenter',
        'jupiter barycenter', 'saturn',
        'neptune', 'uranus'
    ]
    for body in merged['forces']['third_body'].get('bodies', []):
        if body.lower() not in valid_bodies:
            raise ValueError(f"Unknown body: {body}. Valid: {valid_bodies}")

    return merged


def _merge_dicts(defaults: Dict, overrides: Dict) -> Dict:
    """Recursively merge override dict into defaults dict."""
    result = defaults.copy()
    for key, value in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def HPOP_prop_from_config(
        tle_string: str,
        config: Dict[str, Any],
        show_plots: bool = False
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Propagate orbit using configuration dictionary. This is the original function from previous iterations,
    now separated for user-friendliness. This is the simulation "engine", make changes here at your own risk.

    Args:
        tle_string: TLE string (3-line format, careful with line breaks, look at the test at the end to see example)
        config: Configuration dictionary (from YAML/JSON)
        show_plots: If True, display test plots (rudimentary, just to check nothing glaringly fishy is going on)

    Returns:
        posData, velData, timeAxis, dragForce, denseData
    """

    prop_cfg = config['propagation']
    sc_cfg = config['spacecraft']
    force_cfg = config['forces']
    deorb_cfg = config['deorbiting']

    time_step = prop_cfg['time_step']
    sim_time = prop_cfg['sim_time']
    num_data_points = prop_cfg['output_points']
    start_date = prop_cfg['start_date']

    bskPath = __path__[0]

    simTaskName = "simTask"
    simProcessName = "simProcess"

    scSim = SimulationBaseClass.SimBaseClass()
    dynProcess = scSim.CreateNewProcess(simProcessName)

    simulationTimeStep = macros.sec2nano(time_step)
    dynProcess.addTask(scSim.CreateNewTask(simTaskName, simulationTimeStep))

    # Spacecraft creation
    scObject = spacecraft.Spacecraft()
    scObject.ModelTag = "bsk-Sat"
    scObject.hub.mHub = sc_cfg['mass']
    scSim.spacecraft = scObject

    # ---------- DRAG ---------- #
    drag_enabled = force_cfg['drag']['enabled']
    dragForce = None
    denseData = None

    if drag_enabled:
        drag_cfg = force_cfg['drag']

        if drag_cfg['atmosphere_model'].upper() == 'MSIS':
            atmo = msisAtmosphere.MsisAtmosphere()
            atmo.ModelTag = "MsisAtmo"
        elif drag_cfg['atmosphere_model'].upper() == 'EXPONENTIAL':
            atmo = exponentialAtmosphere.ExponentialAtmosphere()
            atmo.ModelTag = "ExpAtmo"
        else:
            raise ValueError(f"Unknown atmosphere model: {drag_cfg['atmosphere_model']}")

        ap = drag_cfg['ap']
        f107 = drag_cfg['f107']
        sw_msg = {
            "ap_24_0": ap, "ap_3_0": ap, "ap_3_-3": ap,
            "ap_3_-6": ap, "ap_3_-9": ap, "ap_3_-12": ap,
            "ap_3_-15": ap, "ap_3_-18": ap, "ap_3_-21": ap,
            "ap_3_-24": ap, "ap_3_-27": ap, "ap_3_-30": ap,
            "ap_3_-33": ap, "ap_3_-36": ap, "ap_3_-39": ap,
            "ap_3_-42": ap, "ap_3_-45": ap, "ap_3_-48": ap,
            "ap_3_-51": ap, "ap_3_-54": ap, "ap_3_-57": ap,
            "f107_1944_0": f107, "f107_24_-24": f107
        }

        swMsgList = []
        for c, val in enumerate(sw_msg.values()):
            swMsgData = messaging.SwDataMsgPayload(dataValue=val)
            swMsgList.append(messaging.SwDataMsg().write(swMsgData))
            atmo.swDataInMsgs[c].subscribeTo(swMsgList[-1])

        scSim.AddModelToTask(simTaskName, atmo)

        dragEffector = dragDynamicEffector.DragDynamicEffector()
        dragEffector.ModelTag = "DragEff"
        dragEffectorTaskName = "drag"
        dragEffector.coreParams.projectedArea = drag_cfg['projected_area']
        dragEffector.coreParams.dragCoeff = drag_cfg['drag_coefficient']
        dynProcess.addTask(scSim.CreateNewTask(dragEffectorTaskName, simulationTimeStep))
        scSim.AddModelToTask(dragEffectorTaskName, dragEffector)

        atmo.addSpacecraftToModel(scObject.scStateOutMsg)
        scObject.addDynamicEffector(dragEffector)
        dragEffector.atmoDensInMsg.subscribeTo(atmo.envOutMsgs[0])

    scSim.AddModelToTask(simTaskName, scObject, 1)

    # ---------- GRAVITY ---------- #
    gravFactory = simIncludeGravBody.gravBodyFactory()
    body_list = ["earth"]

    if force_cfg['third_body']['enabled']:
        body_list.extend(force_cfg['third_body']['bodies'])

    gravBodies = gravFactory.createBodies(body_list)
    gravBodies['earth'].isCentralBody = True

    geo_cfg = force_cfg['geopotential']

    if geo_cfg['enabled'] and geo_cfg['degree'] > 0:
        grav_path = get_path(DataFile.LocalGravData.GGM03S)
        gravBodies["earth"].useSphericalHarmonicsGravityModel(str(grav_path), geo_cfg['degree'])

    gravFactory.addBodiesTo(scObject)

    # ---------- TLE PARSING ----------
    lines = tle_string.strip().split('\n')
    satellite = EarthSatellite(lines[1], lines[2], lines[0])

    ts = load.timescale()

    tle_epoch = satellite.epoch
    year, month, day, hour, minute, second = tle_epoch.utc[:6]
    month_name = calendar.month_name[month]
    spice_time = f"{year} {month_name} {day:02d} {hour:02d}:{minute:02d}:{second:06.3f}"

    if start_date is not None:
        ttarget_dt = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S.%f')
        ttarget = ts.utc(ttarget_dt.year, ttarget_dt.month, ttarget_dt.day,
                         ttarget_dt.hour, ttarget_dt.minute, ttarget_dt.second)
        delta = (ttarget - tle_epoch) * 86400  # TimeDelta → seconds
    else:
        delta = 0.0

    timeInitString = spice_time
    spiceTimeStringFormat = '%Y %B %d %H:%M:%S.%f'
    timeInit = datetime.strptime(timeInitString, spiceTimeStringFormat)
    spiceObject = gravFactory.createSpiceInterface(time=timeInitString, epochInMsg=True)

    rN, vN = satellite.at(tle_epoch).position.m, satellite.at(tle_epoch).velocity.m_per_s

    spiceObject.zeroBase = 'Earth'
    scSim.AddModelToTask(simTaskName, spiceObject)

    scObject.hub.r_CN_NInit = rN
    scObject.hub.v_CN_NInit = vN

    simulationTime = macros.sec2nano(sim_time * 3600 + delta)

    # ---------- DATA LOGGING ----------
    samplingTime = unitTestSupport.samplingTime(
        simulationTime, simulationTimeStep, num_data_points
    )
    dataRec = scObject.scStateOutMsg.recorder(samplingTime)
    scSim.AddModelToTask(simTaskName, dataRec)

    if drag_enabled:
        dataAtmoLog = atmo.envOutMsgs[0].recorder(samplingTime)
        forceLog = dragEffector.logger("forceExternal_B", samplingTime)
        scSim.AddModelToTask(simTaskName, dataAtmoLog)
        scSim.AddModelToTask(simTaskName, forceLog)

    # ---------- DEORBITING EVENT ----------
    if deorb_cfg['enabled']:
        altitude_limit_m = 6378.137 * 1000 + deorb_cfg['altitude_limit_km'] * 1000
        scSim.createNewEvent(
            "Deorbited",
            simulationTimeStep,
            True,
            conditionFunction=lambda self, alt=altitude_limit_m: np.linalg.norm(
                self.spacecraft.scStateOutMsg.read().r_BN_N
            ) < alt,
            terminal=True,
        )

        # ---------- INTEGRATOR SELECTION ----------
    integrator_type = prop_cfg.get('integrator', 'rk4')

    if integrator_type == 'rk4':
        integratorObject = svIntegrators.svIntegratorRK4(scObject)
    elif integrator_type == 'rkf45':
        integratorObject = svIntegrators.svIntegratorRKF45(scObject)
        integratorObject.relTol = prop_cfg.get('rel_tolerance', 1e-8)
        integratorObject.absTol = prop_cfg.get('abs_tolerance', 1e-12)
    elif integrator_type == 'rkf78':
        integratorObject = svIntegrators.svIntegratorRKF78(scObject)
        integratorObject.relTol = prop_cfg.get('rel_tolerance', 1e-8)
        integratorObject.absTol = prop_cfg.get('abs_tolerance', 1e-12)
    elif integrator_type == 'rk2':
        integratorObject = svIntegrators.svIntegratorRK2(scObject)
    elif integrator_type == 'euler':
        integratorObject = svIntegrators.svIntegratorEuler(scObject)
    else:
        raise ValueError(f"Unknown integrator: {integrator_type}")

    scObject.setIntegrator(integratorObject)

    # ---------- EXECUTION ----------
    scSim.InitializeSimulation()
    scSim.ConfigureStopTime(simulationTime)
    scSim.ExecuteSimulation()

    # ---------- RETRIEVE DATA ----------
    posData = dataRec.r_BN_N
    velData = dataRec.v_BN_N
    timeAxis = dataRec.times()

    if drag_enabled:
        dragForce = forceLog.forceExternal_B
        denseData = dataAtmoLog.neutralDensity

    if show_plots:
        # ========== FIGURE 1: 2D Perifocal Plot ==========
        fig1 = plt.figure(1, figsize=(10, 8))

        oeData = orbitalMotion.rv2elem(gravBodies['earth'].mu, rN, vN)
        omega0 = oeData.omega
        b = oeData.a * np.sqrt(1 - oeData.e * oeData.e)

        fig_width = 4.75
        fig_height = (b / oeData.a) * 4.75
        fig1.set_size_inches(fig_width, fig_height)
        fig1.set_dpi(100)

        ax1 = fig1.add_subplot(111)

        x_limit = max(abs(oeData.rApoap), abs(oeData.rPeriap)) / 1000 * 1.25
        y_limit = b / 1000 * 1.25
        ax1.set_xlim(-x_limit, x_limit)
        ax1.set_ylim(-y_limit, y_limit)

        # Draw Earth
        planetColor = '#004400'
        planetRadius = gravBodies['earth'].radEquator / 1000
        earth_circle = plt.Circle((0, 0), planetRadius, color=planetColor, alpha=0.8)
        ax1.add_artist(earth_circle)

        # Calculate orbit points
        rData = []
        fData = []

        for idx in range(len(posData)):
            oe_temp = orbitalMotion.rv2elem(gravBodies['earth'].mu, posData[idx], velData[idx])
            if oe_temp is not None:
                rData.append(oe_temp.rmag)
                fData.append(oe_temp.f + oe_temp.omega - omega0)
            else:
                continue

        rData = np.array(rData)
        fData = np.array(fData)

        # Convert to Cartesian
        x_orbit = rData * np.cos(fData) / 1000
        y_orbit = rData * np.sin(fData) / 1000

        # Plot orbit
        ax1.plot(x_orbit, y_orbit, color='red', linewidth=2.0, label='Orbit')

        # Mark initial position
        oe_initial = orbitalMotion.rv2elem(gravBodies['earth'].mu, rN, vN)
        f_initial = oe_initial.f + oe_initial.omega - omega0
        x_initial = oe_initial.rmag * np.cos(f_initial) / 1000
        y_initial = oe_initial.rmag * np.sin(f_initial) / 1000
        ax1.plot(x_initial, y_initial, 'yo', markersize=10, label='Start', markeredgecolor='black')

        # Formatting
        ax1.set_xlabel('Perifocal X [km]', fontsize=12)
        ax1.set_ylabel('Perifocal Y [km]', fontsize=12)
        ax1.set_title('Orbit in Perifocal Frame', fontsize=14, pad=15)
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        ax1.set_aspect('equal')

        # Add orbit parameters
        param_text = f'a = {oeData.a / 1000:.1f} km\n' \
                     f'e = {oeData.e:.4f}\n' \
                     f'i = {np.degrees(oeData.i):.1f}°'
        ax1.annotate(param_text, xy=(0.02, 0.98), xycoords='axes fraction',
                     verticalalignment='top', fontsize=11,
                     bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='gray'))

        plt.tight_layout()

        # ========== FIGURE 2: 3D Orbit Plot ==========
        fig2 = plt.figure(2, figsize=(12, 10))
        ax2 = fig2.add_subplot(111, projection='3d')

        pos_km = posData / 1000.0
        earth_radius_km = gravBodies['earth'].radEquator / 1000.0

        # Create Earth
        u = np.linspace(0, 2 * np.pi, 40)
        v = np.linspace(0, np.pi, 40)

        x = earth_radius_km * np.outer(np.cos(u), np.sin(v))
        y = earth_radius_km * np.outer(np.sin(u), np.sin(v))
        z = earth_radius_km * np.outer(np.ones(np.size(u)), np.cos(v))

        ax2.plot_surface(x, y, z, color='#1E90FF', alpha=0.9,
                         edgecolor='darkblue', linewidth=0.5, antialiased=True)

        # Longitude/latitude grid
        for phi in np.linspace(0, 2 * np.pi, 8):
            x_line = earth_radius_km * np.sin(u) * np.cos(phi)
            y_line = earth_radius_km * np.sin(u) * np.sin(phi)
            z_line = earth_radius_km * np.cos(u)
            ax2.plot(x_line, y_line, z_line, color='navy', alpha=0.4, linewidth=0.8)

        # Plot trajectory
        if len(pos_km) > 1:
            ax2.plot(pos_km[:, 0], pos_km[:, 1], pos_km[:, 2],
                     color='red', linewidth=3.0, alpha=0.9, label='Orbit')

            ax2.scatter(pos_km[0, 0], pos_km[0, 1], pos_km[0, 2],
                        color='lime', s=150, marker='o', label='Start',
                        edgecolor='black', linewidth=1.5, zorder=5)
            ax2.scatter(pos_km[-1, 0], pos_km[-1, 1], pos_km[-1, 2],
                        color='orange', s=150, marker='s', label='End',
                        edgecolor='black', linewidth=1.5, zorder=5)

        # Coordinate axes
        axis_length = np.max(np.abs(pos_km)) * 1.2 if len(pos_km) > 0 else 50000
        ax2.quiver(0, 0, 0, axis_length, 0, 0, color='darkred',
                   arrow_length_ratio=0.1, linewidth=2)
        ax2.quiver(0, 0, 0, 0, axis_length, 0, color='darkgreen',
                   arrow_length_ratio=0.1, linewidth=2)
        ax2.quiver(0, 0, 0, 0, 0, axis_length, color='darkblue',
                   arrow_length_ratio=0.1, linewidth=2)

        ax2.text(axis_length * 1.1, 0, 0, 'X', color='darkred', fontsize=14, fontweight='bold')
        ax2.text(0, axis_length * 1.1, 0, 'Y', color='darkgreen', fontsize=14, fontweight='bold')
        ax2.text(0, 0, axis_length * 1.1, 'Z', color='darkblue', fontsize=14, fontweight='bold')

        ax2.set_xlabel('X [km]', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Y [km]', fontsize=12, fontweight='bold')
        ax2.set_zlabel('Z [km]', fontsize=12, fontweight='bold')
        ax2.set_title('3D Orbit Visualization', fontsize=16, pad=20, fontweight='bold')

        max_extent = np.max(np.abs(pos_km)) * 1.2 if len(pos_km) > 0 else 50000
        ax2.set_xlim([-max_extent, max_extent])
        ax2.set_ylim([-max_extent, max_extent])
        ax2.set_zlim([-max_extent, max_extent])

        ax2.legend(loc='upper right', bbox_to_anchor=(1.15, 0.9), fontsize=11)

        ax2.grid(True, alpha=0.4)

        ax2.view_init(elev=25, azim=45)

        plt.tight_layout()

        figureList = {
            "Perifocal frame 2D": fig1,
            "3D orbit visualization": fig2
        }

        plt.show()

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    # The output state vectors are in the Geocentric Celestial Reference Frame, NOT in the SGP4 native frame (TEME)!!!!

    # IF TEME is needed, the Skyfield library has handy conversion functions that automatically rotate the frame to the
    # desired frame

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


    return posData, velData, timeAxis, dragForce, denseData


def HPOP_prop(
        tle_string: str,
        bodies: int = 10,
        drag: bool = False,
        show_plots: bool = False,
        date: Optional[str] = None,
        timeStep: float = 5.0,
        simTime: float = 12.0,
        config_path: Optional[str] = None
) -> Tuple:
    """
    Main HPOP propagation function.

    If config_path is provided, YAML/JSON configuration takes precedence
    over individual parameters.

    Args:
        tle_string: TLE in 3-line format, check test function at the end for proper formatting example
        bodies: Number of third bodies (1-10). Overridden by config if provided.
        drag: Enable atmospheric drag. Overridden by config if provided.
        show_plots: test plots for verification, shows 2D and 3D orbit
        date: Start date override (for other-than-epoch start dates)
        timeStep: Integration step in seconds
        simTime: Simulation duration in hours
        config_path: Path to YAML/JSON configuration file

    Returns:
        posData, velData, timeAxis, dragForce, denseData
    """

    if config_path is not None:
        config = load_config(config_path)
        config = validate_config(config)
        return HPOP_prop_from_config(tle_string, config, show_plots)
    else:
        body_list = [
            "earth", "sun", "moon", "jupiter barycenter",
            "venus", "mars barycenter", "mercury",
            "saturn", "neptune", "uranus"
        ]
        bodies = max(1, min(bodies, 10))

        config = {
            'propagation': {
                'time_step': timeStep,
                'sim_time': simTime,
                'output_points': 2000,
                'start_date': date,
                'integrator': 'rkf45',
                'rel_tolerance': 1e-8,
                'abs_tolerance': 1e-12
            },
            'spacecraft': {
                'mass': 1000.0,
            },
            'forces': {
                'geopotential': {
                    'enabled': True,
                    'degree': 100
                },
                'drag': {
                    'enabled': drag,
                    'atmosphere_model': 'MSIS',
                    'drag_coefficient': 2.2,
                    'projected_area': 2.5,
                    'f107': 100.0,
                    'ap': 10.0
                },
                'third_body': {
                    'enabled': bodies > 1,
                    'bodies': body_list[1:bodies] if bodies > 1 else []
                }
            },
            'deorbiting': {
                'enabled': True,
                'altitude_limit_km': 100.0
            }
        }
        # Full hpop by default, for simpler cases use config or feed parameters
        config = validate_config(config)
        return HPOP_prop_from_config(tle_string, config, show_plots)

def _test():
    tle_string = """SAT-25544
1 25544U 98067A   25336.09225230  .00009217  00000-0  17381-3 0  9994
2 25544  51.6314 195.1903 0003639 193.8265 166.2625 15.49237019541206"""  # ISS TLE

    posData, velData, timeAxis, dragForce, denseData = (
        HPOP_prop(tle_string,drag=True,show_plots=True,date="2025-12-03 02:12:50.599", timeStep=5., simTime=1))



if __name__ == '__main__':
    _test()