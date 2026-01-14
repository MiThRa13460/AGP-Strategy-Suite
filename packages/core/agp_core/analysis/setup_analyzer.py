"""
Setup Analyzer - Intelligent Setup Recommendations
Correlates telemetry data with setup values
Detects conflicts and provides holistic recommendations
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
from collections import deque
import json
import math
import time


class CornerPhase(Enum):
    STRAIGHT = "straight"
    BRAKING = "braking"
    ENTRY = "entry"
    MID = "mid"
    EXIT = "exit"
    ACCELERATION = "acceleration"


class Problem(Enum):
    UNDERSTEER_ENTRY = "understeer_entry"
    UNDERSTEER_MID = "understeer_mid"
    UNDERSTEER_EXIT = "understeer_exit"
    OVERSTEER_ENTRY = "oversteer_entry"
    OVERSTEER_MID = "oversteer_mid"
    OVERSTEER_EXIT = "oversteer_exit"
    WHEELSPIN = "wheelspin"
    WHEEL_LOCK = "wheel_lock"
    INSTABILITY_HIGH_SPEED = "instability_high_speed"
    TIRE_OVERHEAT_FRONT = "tire_overheat_front"
    TIRE_OVERHEAT_REAR = "tire_overheat_rear"
    TIRE_COLD_FRONT = "tire_cold_front"
    TIRE_COLD_REAR = "tire_cold_rear"
    BRAKE_OVERHEAT_FRONT = "brake_overheat_front"
    BRAKE_OVERHEAT_REAR = "brake_overheat_rear"
    EXCESSIVE_ROLL = "excessive_roll"
    BOTTOMING = "bottoming"
    POOR_TRACTION = "poor_traction"


@dataclass
class SetupParameter:
    """Definition of a setup parameter with effects"""
    name: str
    display_name: str
    unit: str
    category: str
    # Effects on problems: negative = helps, positive = hurts
    effects: Dict[Problem, float] = field(default_factory=dict)
    # Interactions with other parameters
    interactions: Dict[str, float] = field(default_factory=dict)


@dataclass
class Sample:
    """Single telemetry sample"""
    timestamp: float
    phase: CornerPhase
    speed: float
    throttle: float
    brake: float
    steering: float
    g_lat: float
    g_long: float

    # Tires
    tire_temp: List[float]  # FL, FR, RL, RR
    tire_temp_inner: List[float]
    tire_temp_outer: List[float]
    tire_pressure: List[float]
    tire_wear: List[float]
    grip: List[float]
    tire_load: List[float]
    slip_ratio: List[float]

    # Brakes
    brake_temp: List[float]

    # Suspension
    ride_height: List[float]
    susp_deflection: List[float]

    # Aero
    front_downforce: float
    rear_downforce: float
    rake: float

    # Geometry
    camber: List[float]
    toe: List[float]


@dataclass
class LapAnalysis:
    """Analysis results for one lap"""
    lap_number: int
    lap_time: float
    sample_count: int

    # Behavior by phase
    behavior: Dict[CornerPhase, Dict[str, float]]

    # Problems detected
    problems: Dict[Problem, float]  # Problem -> severity (0-1)

    # Tire stats
    tire_temps_avg: List[float]
    tire_temps_max: List[float]
    tire_pressure_avg: List[float]
    tire_wear_start: List[float]
    tire_wear_end: List[float]
    tire_balance: List[float]  # inner-outer for each

    # Brake stats
    brake_temps_max: List[float]

    # Suspension stats
    avg_rake: float
    max_roll_front: float
    max_roll_rear: float
    bottoming_events: int

    # Traction
    wheelspin_pct: float
    lockup_pct: float
    avg_rear_slip: float

    # Stability
    stability_score: float
    high_speed_corrections: float


@dataclass
class Recommendation:
    """Setup recommendation"""
    parameter: str
    direction: str  # "increase" or "decrease"
    value: Optional[str]  # Suggested value or range
    reason: str
    priority: int  # 1-10
    addresses: List[Problem]
    side_effects: List[str]
    confidence: float  # 0-1


class SetupAnalyzer:
    """
    Intelligent setup analyzer that correlates telemetry with setup
    and provides holistic recommendations
    """

    def __init__(self):
        # Sample buffer
        self.samples: deque = deque(maxlen=5000)
        self.current_lap_samples: List[Sample] = []
        self.current_lap = 0

        # Lap history
        self.lap_analyses: List[LapAnalysis] = []

        # Current setup (loaded from file)
        self.current_setup: Dict[str, Any] = {}

        # Vehicle info
        self.vehicle_name = ""
        self.vehicle_category = "GT3"  # GT3, LMP2, LMH, etc.

        # Define all parameters and their effects
        self._init_parameters()

        # Optimal ranges by category
        self._init_optimal_ranges()

    def _init_parameters(self):
        """Initialize parameter definitions with effects"""
        self.parameters: Dict[str, SetupParameter] = {
            # === SPRINGS ===
            "front_spring": SetupParameter(
                name="front_spring", display_name="Ressort Avant", unit="N/mm",
                category="suspension",
                effects={
                    Problem.UNDERSTEER_ENTRY: -0.25,
                    Problem.UNDERSTEER_MID: -0.15,
                    Problem.OVERSTEER_EXIT: 0.15,
                    Problem.TIRE_OVERHEAT_FRONT: 0.1,
                    Problem.INSTABILITY_HIGH_SPEED: -0.1,
                }
            ),
            "rear_spring": SetupParameter(
                name="rear_spring", display_name="Ressort Arriere", unit="N/mm",
                category="suspension",
                effects={
                    Problem.UNDERSTEER_ENTRY: 0.15,
                    Problem.OVERSTEER_EXIT: -0.3,
                    Problem.POOR_TRACTION: 0.15,
                    Problem.TIRE_OVERHEAT_REAR: 0.1,
                }
            ),

            # === BUMP (COMPRESSION) ===
            "front_slow_bump": SetupParameter(
                name="front_slow_bump", display_name="Bump Lent AV", unit="clicks",
                category="dampers",
                effects={
                    Problem.UNDERSTEER_ENTRY: -0.2,
                    Problem.UNDERSTEER_MID: -0.1,
                    Problem.INSTABILITY_HIGH_SPEED: -0.1,
                }
            ),
            "front_fast_bump": SetupParameter(
                name="front_fast_bump", display_name="Bump Rapide AV", unit="clicks",
                category="dampers",
                effects={
                    Problem.BOTTOMING: -0.2,
                }
            ),
            "rear_slow_bump": SetupParameter(
                name="rear_slow_bump", display_name="Bump Lent AR", unit="clicks",
                category="dampers",
                effects={
                    Problem.OVERSTEER_EXIT: -0.15,
                    Problem.POOR_TRACTION: 0.12,
                    Problem.WHEELSPIN: 0.1,
                }
            ),
            "rear_fast_bump": SetupParameter(
                name="rear_fast_bump", display_name="Bump Rapide AR", unit="clicks",
                category="dampers",
                effects={
                    Problem.BOTTOMING: -0.15,
                    Problem.POOR_TRACTION: 0.08,
                }
            ),

            # === REBOUND ===
            "front_slow_rebound": SetupParameter(
                name="front_slow_rebound", display_name="Detente Lente AV", unit="clicks",
                category="dampers",
                effects={
                    Problem.UNDERSTEER_ENTRY: 0.18,
                    Problem.INSTABILITY_HIGH_SPEED: -0.15,
                }
            ),
            "front_fast_rebound": SetupParameter(
                name="front_fast_rebound", display_name="Detente Rapide AV", unit="clicks",
                category="dampers",
                effects={
                    Problem.INSTABILITY_HIGH_SPEED: -0.1,
                }
            ),
            "rear_slow_rebound": SetupParameter(
                name="rear_slow_rebound", display_name="Detente Lente AR", unit="clicks",
                category="dampers",
                effects={
                    Problem.OVERSTEER_ENTRY: -0.2,
                    Problem.OVERSTEER_EXIT: 0.12,
                    Problem.POOR_TRACTION: -0.08,
                }
            ),
            "rear_fast_rebound": SetupParameter(
                name="rear_fast_rebound", display_name="Detente Rapide AR", unit="clicks",
                category="dampers",
                effects={
                    Problem.INSTABILITY_HIGH_SPEED: -0.08,
                }
            ),

            # === ANTI-ROLL BARS ===
            "front_arb": SetupParameter(
                name="front_arb", display_name="Barre Anti-Roulis AV", unit="N/mm",
                category="suspension",
                effects={
                    Problem.UNDERSTEER_ENTRY: -0.3,
                    Problem.UNDERSTEER_MID: -0.35,
                    Problem.OVERSTEER_EXIT: 0.2,
                    Problem.EXCESSIVE_ROLL: -0.3,
                    Problem.TIRE_OVERHEAT_FRONT: 0.08,
                }
            ),
            "rear_arb": SetupParameter(
                name="rear_arb", display_name="Barre Anti-Roulis AR", unit="N/mm",
                category="suspension",
                effects={
                    Problem.UNDERSTEER_ENTRY: 0.2,
                    Problem.UNDERSTEER_MID: 0.25,
                    Problem.OVERSTEER_EXIT: -0.35,
                    Problem.OVERSTEER_ENTRY: -0.15,
                    Problem.EXCESSIVE_ROLL: -0.25,
                    Problem.POOR_TRACTION: 0.12,
                }
            ),

            # === GEOMETRY - CAMBER ===
            "front_camber": SetupParameter(
                name="front_camber", display_name="Carrossage AV", unit="deg",
                category="geometry",
                effects={
                    Problem.UNDERSTEER_MID: -0.25,
                    Problem.TIRE_OVERHEAT_FRONT: 0.15,
                }
            ),
            "rear_camber": SetupParameter(
                name="rear_camber", display_name="Carrossage AR", unit="deg",
                category="geometry",
                effects={
                    Problem.OVERSTEER_MID: -0.2,
                    Problem.TIRE_OVERHEAT_REAR: 0.15,
                    Problem.POOR_TRACTION: 0.08,
                }
            ),

            # === GEOMETRY - TOE ===
            "front_toe": SetupParameter(
                name="front_toe", display_name="Pincement AV", unit="deg",
                category="geometry",
                effects={
                    Problem.UNDERSTEER_ENTRY: 0.15,  # toe-in increases understeer
                    Problem.INSTABILITY_HIGH_SPEED: -0.2,
                    Problem.TIRE_OVERHEAT_FRONT: 0.1,
                }
            ),
            "rear_toe": SetupParameter(
                name="rear_toe", display_name="Pincement AR", unit="deg",
                category="geometry",
                effects={
                    Problem.OVERSTEER_EXIT: -0.25,  # toe-in stabilizes rear
                    Problem.INSTABILITY_HIGH_SPEED: -0.3,
                    Problem.POOR_TRACTION: -0.1,
                    Problem.TIRE_OVERHEAT_REAR: 0.1,
                }
            ),

            # === AERO ===
            "front_wing": SetupParameter(
                name="front_wing", display_name="Aileron AV", unit="deg",
                category="aero",
                effects={
                    Problem.UNDERSTEER_MID: -0.2,
                    Problem.UNDERSTEER_ENTRY: -0.15,
                }
            ),
            "rear_wing": SetupParameter(
                name="rear_wing", display_name="Aileron AR", unit="deg",
                category="aero",
                effects={
                    Problem.OVERSTEER_MID: -0.3,
                    Problem.OVERSTEER_EXIT: -0.2,
                    Problem.INSTABILITY_HIGH_SPEED: -0.35,
                    Problem.POOR_TRACTION: -0.2,
                }
            ),

            # === RIDE HEIGHT ===
            "front_ride_height": SetupParameter(
                name="front_ride_height", display_name="Hauteur Caisse AV", unit="mm",
                category="aero",
                effects={
                    Problem.UNDERSTEER_MID: 0.1,  # higher = less downforce
                    Problem.BOTTOMING: -0.3,
                }
            ),
            "rear_ride_height": SetupParameter(
                name="rear_ride_height", display_name="Hauteur Caisse AR", unit="mm",
                category="aero",
                effects={
                    Problem.OVERSTEER_MID: 0.1,
                    Problem.BOTTOMING: -0.25,
                    Problem.POOR_TRACTION: 0.08,
                }
            ),

            # === DIFFERENTIAL ===
            "diff_power": SetupParameter(
                name="diff_power", display_name="Diff Puissance", unit="%",
                category="differential",
                effects={
                    Problem.POOR_TRACTION: -0.25,
                    Problem.WHEELSPIN: -0.15,
                    Problem.OVERSTEER_EXIT: 0.3,
                }
            ),
            "diff_coast": SetupParameter(
                name="diff_coast", display_name="Diff Deceleration", unit="%",
                category="differential",
                effects={
                    Problem.OVERSTEER_ENTRY: 0.25,
                    Problem.INSTABILITY_HIGH_SPEED: 0.1,
                }
            ),
            "diff_preload": SetupParameter(
                name="diff_preload", display_name="Precharge Diff", unit="Nm",
                category="differential",
                effects={
                    Problem.POOR_TRACTION: -0.1,
                    Problem.OVERSTEER_EXIT: 0.08,
                }
            ),

            # === BRAKES ===
            "brake_bias": SetupParameter(
                name="brake_bias", display_name="Repartition Freinage", unit="%",
                category="brakes",
                effects={
                    Problem.OVERSTEER_ENTRY: -0.35,  # more front = less rear lockup
                    Problem.UNDERSTEER_ENTRY: 0.25,
                    Problem.WHEEL_LOCK: -0.2,
                    Problem.BRAKE_OVERHEAT_FRONT: 0.15,
                    Problem.BRAKE_OVERHEAT_REAR: -0.15,
                }
            ),

            # === TIRE PRESSURE ===
            "front_pressure": SetupParameter(
                name="front_pressure", display_name="Pression AV", unit="kPa",
                category="tires",
                effects={
                    Problem.UNDERSTEER_MID: 0.12,  # higher = less grip
                    Problem.TIRE_OVERHEAT_FRONT: -0.15,
                    Problem.TIRE_COLD_FRONT: 0.2,
                }
            ),
            "rear_pressure": SetupParameter(
                name="rear_pressure", display_name="Pression AR", unit="kPa",
                category="tires",
                effects={
                    Problem.OVERSTEER_MID: 0.08,
                    Problem.POOR_TRACTION: 0.1,
                    Problem.TIRE_OVERHEAT_REAR: -0.12,
                    Problem.TIRE_COLD_REAR: 0.18,
                }
            ),
        }

    def _init_optimal_ranges(self):
        """Initialize optimal ranges by vehicle category"""
        self.optimal_ranges = {
            "GT3": {
                "tire_temp": (75, 95, 85),  # min, max, optimal
                "tire_pressure": (170, 190, 180),
                "brake_temp": (300, 600, 450),
                "brake_temp_max": 700,
                "engine_temp": (82, 105, 92),
            },
            "LMP2": {
                "tire_temp": (80, 95, 87),
                "tire_pressure": (165, 180, 172),
                "brake_temp": (350, 650, 500),
                "brake_temp_max": 750,
                "engine_temp": (88, 105, 95),
            },
            "LMH": {
                "tire_temp": (82, 98, 90),
                "tire_pressure": (160, 178, 168),
                "brake_temp": (380, 680, 530),
                "brake_temp_max": 780,
                "engine_temp": (90, 108, 98),
            },
        }

    def load_setup(self, setup_path: str) -> bool:
        """Load current setup from JSON file"""
        try:
            with open(setup_path, 'r') as f:
                self.current_setup = json.load(f)
            return True
        except Exception as e:
            print(f"Error loading setup: {e}")
            return False

    def add_sample(self, telemetry_data, scoring_data=None):
        """Add a telemetry sample for analysis"""
        if not telemetry_data:
            return

        # Detect corner phase
        phase = self._classify_phase(telemetry_data)

        # Calculate slip ratios
        slip_ratios = self._calculate_slip_ratios(telemetry_data)

        sample = Sample(
            timestamp=time.time(),
            phase=phase,
            speed=telemetry_data.speed_kmh,
            throttle=telemetry_data.throttle,
            brake=telemetry_data.brake,
            steering=abs(telemetry_data.steering),
            g_lat=telemetry_data.g_lat,
            g_long=telemetry_data.g_long,

            tire_temp=[
                telemetry_data.tire_temp_fl,
                telemetry_data.tire_temp_fr,
                telemetry_data.tire_temp_rl,
                telemetry_data.tire_temp_rr
            ],
            tire_temp_inner=[
                telemetry_data.wheels[0].temp_inner,
                telemetry_data.wheels[1].temp_inner,
                telemetry_data.wheels[2].temp_inner,
                telemetry_data.wheels[3].temp_inner
            ],
            tire_temp_outer=[
                telemetry_data.wheels[0].temp_outer,
                telemetry_data.wheels[1].temp_outer,
                telemetry_data.wheels[2].temp_outer,
                telemetry_data.wheels[3].temp_outer
            ],
            tire_pressure=[
                telemetry_data.tire_pressure_fl,
                telemetry_data.tire_pressure_fr,
                telemetry_data.tire_pressure_rl,
                telemetry_data.tire_pressure_rr
            ],
            tire_wear=[
                telemetry_data.tire_wear_fl,
                telemetry_data.tire_wear_fr,
                telemetry_data.tire_wear_rl,
                telemetry_data.tire_wear_rr
            ],
            grip=[
                telemetry_data.grip_fl,
                telemetry_data.grip_fr,
                telemetry_data.grip_rl,
                telemetry_data.grip_rr
            ],
            tire_load=[
                telemetry_data.wheels[0].tire_load,
                telemetry_data.wheels[1].tire_load,
                telemetry_data.wheels[2].tire_load,
                telemetry_data.wheels[3].tire_load
            ],
            slip_ratio=slip_ratios,

            brake_temp=[
                telemetry_data.brake_temp_fl,
                telemetry_data.brake_temp_fr,
                telemetry_data.brake_temp_rl,
                telemetry_data.brake_temp_rr
            ],

            ride_height=[
                telemetry_data.wheels[0].ride_height,
                telemetry_data.wheels[1].ride_height,
                telemetry_data.wheels[2].ride_height,
                telemetry_data.wheels[3].ride_height
            ],
            susp_deflection=[
                telemetry_data.wheels[0].suspension_deflection,
                telemetry_data.wheels[1].suspension_deflection,
                telemetry_data.wheels[2].suspension_deflection,
                telemetry_data.wheels[3].suspension_deflection
            ],

            front_downforce=telemetry_data.front_downforce,
            rear_downforce=telemetry_data.rear_downforce,
            rake=telemetry_data.rake,

            camber=[
                telemetry_data.wheels[0].camber,
                telemetry_data.wheels[1].camber,
                telemetry_data.wheels[2].camber,
                telemetry_data.wheels[3].camber
            ],
            toe=[
                telemetry_data.wheels[0].toe,
                telemetry_data.wheels[1].toe,
                telemetry_data.wheels[2].toe,
                telemetry_data.wheels[3].toe
            ]
        )

        # Add to buffers
        self.samples.append(sample)
        self.current_lap_samples.append(sample)

        # Detect new lap
        if telemetry_data.lap_number != self.current_lap:
            if self.current_lap > 0 and len(self.current_lap_samples) > 100:
                self._analyze_lap()
            self.current_lap = telemetry_data.lap_number
            self.current_lap_samples = []

        # Update vehicle info
        self.vehicle_name = telemetry_data.vehicle_name
        self._detect_vehicle_category(telemetry_data)

    def _classify_phase(self, data) -> CornerPhase:
        """Classify current corner phase"""
        brake = data.brake
        throttle = data.throttle
        steering = abs(data.steering)
        speed = data.speed_kmh

        if brake > 0.8 and steering < 0.05:
            return CornerPhase.BRAKING
        elif brake > 0.15 and steering > 0.03:
            return CornerPhase.ENTRY
        elif throttle > 0.7 and steering > 0.03:
            return CornerPhase.EXIT
        elif throttle > 0.9 and steering < 0.03:
            return CornerPhase.ACCELERATION
        elif steering > 0.08:
            return CornerPhase.MID
        else:
            return CornerPhase.STRAIGHT

    def _calculate_slip_ratios(self, data) -> List[float]:
        """Calculate slip ratio for each wheel"""
        slip_ratios = []
        speed = data.speed

        for i, wheel in enumerate(data.wheels):
            if speed > 1:
                wheel_speed = abs(wheel.rotation) * 0.325  # estimated radius
                slip = (wheel_speed / speed) - 1
                slip_ratios.append(slip)
            else:
                slip_ratios.append(0)

        return slip_ratios

    def _detect_vehicle_category(self, data):
        """Detect vehicle category from telemetry"""
        if data.speed_kmh > 0:
            if data.front_downforce + data.rear_downforce > 15000:
                self.vehicle_category = "LMH"
            elif data.front_downforce + data.rear_downforce > 8000:
                self.vehicle_category = "LMP2"
            else:
                self.vehicle_category = "GT3"

    def _analyze_lap(self):
        """Analyze completed lap"""
        samples = self.current_lap_samples
        if len(samples) < 100:
            return

        # Behavior by phase
        behavior = self._analyze_behavior(samples)

        # Detect problems
        problems = self._detect_problems(samples, behavior)

        # Calculate stats
        analysis = LapAnalysis(
            lap_number=self.current_lap,
            lap_time=0,  # Would come from scoring
            sample_count=len(samples),
            behavior=behavior,
            problems=problems,
            tire_temps_avg=self._calc_avg([s.tire_temp for s in samples]),
            tire_temps_max=self._calc_max([s.tire_temp for s in samples]),
            tire_pressure_avg=self._calc_avg([s.tire_pressure for s in samples]),
            tire_wear_start=samples[0].tire_wear,
            tire_wear_end=samples[-1].tire_wear,
            tire_balance=self._calc_tire_balance(samples),
            brake_temps_max=self._calc_max([s.brake_temp for s in samples]),
            avg_rake=sum(s.rake for s in samples) / len(samples),
            max_roll_front=max(abs(s.ride_height[0] - s.ride_height[1]) for s in samples),
            max_roll_rear=max(abs(s.ride_height[2] - s.ride_height[3]) for s in samples),
            bottoming_events=sum(1 for s in samples if min(s.ride_height) < 5),
            wheelspin_pct=self._calc_wheelspin_pct(samples),
            lockup_pct=self._calc_lockup_pct(samples),
            avg_rear_slip=self._calc_avg_rear_slip(samples),
            stability_score=self._calc_stability_score(samples),
            high_speed_corrections=self._calc_high_speed_corrections(samples)
        )

        self.lap_analyses.append(analysis)
        if len(self.lap_analyses) > 20:
            self.lap_analyses.pop(0)

    def _analyze_behavior(self, samples) -> Dict[CornerPhase, Dict[str, float]]:
        """Analyze behavior for each corner phase"""
        behavior = {}

        for phase in [CornerPhase.ENTRY, CornerPhase.MID, CornerPhase.EXIT]:
            phase_samples = [s for s in samples if s.phase == phase]

            if len(phase_samples) < 10:
                behavior[phase] = {"understeer": 0, "oversteer": 0, "neutral": 1}
                continue

            under = 0
            over = 0
            neutral = 0

            for s in phase_samples:
                front_grip = (s.grip[0] + s.grip[1]) / 2
                rear_grip = (s.grip[2] + s.grip[3]) / 2
                front_slip = (abs(s.slip_ratio[0]) + abs(s.slip_ratio[1])) / 2
                rear_slip = (abs(s.slip_ratio[2]) + abs(s.slip_ratio[3])) / 2

                if front_grip < rear_grip - 0.03 or front_slip > rear_slip + 0.015:
                    under += 1
                elif rear_grip < front_grip - 0.03 or rear_slip > front_slip + 0.015:
                    over += 1
                else:
                    neutral += 1

            total = len(phase_samples)
            behavior[phase] = {
                "understeer": under / total,
                "oversteer": over / total,
                "neutral": neutral / total
            }

        return behavior

    def _detect_problems(self, samples, behavior) -> Dict[Problem, float]:
        """Detect problems and their severity"""
        problems = {}
        ranges = self.optimal_ranges.get(self.vehicle_category, self.optimal_ranges["GT3"])

        # Behavior problems
        if behavior.get(CornerPhase.ENTRY, {}).get("understeer", 0) > 0.35:
            problems[Problem.UNDERSTEER_ENTRY] = behavior[CornerPhase.ENTRY]["understeer"]

        if behavior.get(CornerPhase.MID, {}).get("understeer", 0) > 0.4:
            problems[Problem.UNDERSTEER_MID] = behavior[CornerPhase.MID]["understeer"]

        if behavior.get(CornerPhase.EXIT, {}).get("understeer", 0) > 0.35:
            problems[Problem.UNDERSTEER_EXIT] = behavior[CornerPhase.EXIT]["understeer"]

        if behavior.get(CornerPhase.ENTRY, {}).get("oversteer", 0) > 0.3:
            problems[Problem.OVERSTEER_ENTRY] = behavior[CornerPhase.ENTRY]["oversteer"]

        if behavior.get(CornerPhase.MID, {}).get("oversteer", 0) > 0.35:
            problems[Problem.OVERSTEER_MID] = behavior[CornerPhase.MID]["oversteer"]

        if behavior.get(CornerPhase.EXIT, {}).get("oversteer", 0) > 0.3:
            problems[Problem.OVERSTEER_EXIT] = behavior[CornerPhase.EXIT]["oversteer"]

        # Tire temps
        front_temp = sum(s.tire_temp[0] + s.tire_temp[1] for s in samples) / (len(samples) * 2)
        rear_temp = sum(s.tire_temp[2] + s.tire_temp[3] for s in samples) / (len(samples) * 2)

        if front_temp > ranges["tire_temp"][1]:
            problems[Problem.TIRE_OVERHEAT_FRONT] = min(1, (front_temp - ranges["tire_temp"][1]) / 10)
        if front_temp < ranges["tire_temp"][0]:
            problems[Problem.TIRE_COLD_FRONT] = min(1, (ranges["tire_temp"][0] - front_temp) / 10)
        if rear_temp > ranges["tire_temp"][1]:
            problems[Problem.TIRE_OVERHEAT_REAR] = min(1, (rear_temp - ranges["tire_temp"][1]) / 10)
        if rear_temp < ranges["tire_temp"][0]:
            problems[Problem.TIRE_COLD_REAR] = min(1, (ranges["tire_temp"][0] - rear_temp) / 10)

        # Brake temps
        front_brake_max = max(max(s.brake_temp[0], s.brake_temp[1]) for s in samples)
        rear_brake_max = max(max(s.brake_temp[2], s.brake_temp[3]) for s in samples)

        if front_brake_max > ranges["brake_temp_max"]:
            problems[Problem.BRAKE_OVERHEAT_FRONT] = min(1, (front_brake_max - ranges["brake_temp_max"]) / 100)
        if rear_brake_max > ranges["brake_temp_max"]:
            problems[Problem.BRAKE_OVERHEAT_REAR] = min(1, (rear_brake_max - ranges["brake_temp_max"]) / 100)

        # Traction
        wheelspin = self._calc_wheelspin_pct(samples)
        if wheelspin > 0.1:
            problems[Problem.WHEELSPIN] = min(1, wheelspin * 2)
            problems[Problem.POOR_TRACTION] = min(1, wheelspin * 1.5)

        # Lockup
        lockup = self._calc_lockup_pct(samples)
        if lockup > 0.1:
            problems[Problem.WHEEL_LOCK] = min(1, lockup * 2)

        # Stability
        stability = self._calc_stability_score(samples)
        if stability < 0.7:
            problems[Problem.INSTABILITY_HIGH_SPEED] = 1 - stability

        # Roll
        max_roll = max(
            max(abs(s.ride_height[0] - s.ride_height[1]) for s in samples),
            max(abs(s.ride_height[2] - s.ride_height[3]) for s in samples)
        )
        if max_roll > 12:
            problems[Problem.EXCESSIVE_ROLL] = min(1, (max_roll - 12) / 10)

        # Bottoming
        bottoming = sum(1 for s in samples if min(s.ride_height) < 5) / len(samples)
        if bottoming > 0.05:
            problems[Problem.BOTTOMING] = min(1, bottoming * 5)

        return problems

    def _calc_avg(self, data_list) -> List[float]:
        """Calculate average for list of 4-element arrays"""
        if not data_list:
            return [0, 0, 0, 0]
        return [sum(d[i] for d in data_list) / len(data_list) for i in range(4)]

    def _calc_max(self, data_list) -> List[float]:
        """Calculate max for list of 4-element arrays"""
        if not data_list:
            return [0, 0, 0, 0]
        return [max(d[i] for d in data_list) for i in range(4)]

    def _calc_tire_balance(self, samples) -> List[float]:
        """Calculate inner-outer temperature balance"""
        if not samples:
            return [0, 0, 0, 0]
        last = samples[-1]
        return [
            last.tire_temp_inner[i] - last.tire_temp_outer[i]
            for i in range(4)
        ]

    def _calc_wheelspin_pct(self, samples) -> float:
        """Calculate percentage of exit samples with wheelspin"""
        exit_samples = [s for s in samples if s.phase == CornerPhase.EXIT]
        if not exit_samples:
            return 0
        spin_count = sum(1 for s in exit_samples
                        if (abs(s.slip_ratio[2]) + abs(s.slip_ratio[3])) / 2 > 0.08)
        return spin_count / len(exit_samples)

    def _calc_lockup_pct(self, samples) -> float:
        """Calculate percentage of braking samples with wheel lock"""
        brake_samples = [s for s in samples if s.phase in [CornerPhase.BRAKING, CornerPhase.ENTRY]]
        if not brake_samples:
            return 0
        lock_count = sum(1 for s in brake_samples
                        if min(s.slip_ratio) < -0.1)
        return lock_count / len(brake_samples)

    def _calc_avg_rear_slip(self, samples) -> float:
        """Calculate average rear slip ratio during acceleration"""
        exit_samples = [s for s in samples if s.phase == CornerPhase.EXIT]
        if not exit_samples:
            return 0
        slips = [(abs(s.slip_ratio[2]) + abs(s.slip_ratio[3])) / 2 for s in exit_samples]
        return sum(slips) / len(slips)

    def _calc_stability_score(self, samples) -> float:
        """Calculate high speed stability score"""
        high_speed = [s for s in samples if s.phase == CornerPhase.STRAIGHT and s.speed > 180]
        if len(high_speed) < 20:
            return 1.0
        corrections = sum(s.steering for s in high_speed) / len(high_speed)
        return max(0, 1 - corrections * 8)

    def _calc_high_speed_corrections(self, samples) -> float:
        """Calculate steering corrections at high speed"""
        high_speed = [s for s in samples if s.phase == CornerPhase.STRAIGHT and s.speed > 180]
        if not high_speed:
            return 0
        return sum(s.steering for s in high_speed) / len(high_speed)

    def generate_recommendations(self) -> List[Recommendation]:
        """Generate intelligent setup recommendations"""
        if not self.lap_analyses:
            return []

        # Use most recent lap analysis
        analysis = self.lap_analyses[-1]
        recommendations = []
        applied_effects = {}  # Track cumulative effects

        # Sort problems by severity
        sorted_problems = sorted(
            analysis.problems.items(),
            key=lambda x: x[1],
            reverse=True
        )

        for problem, severity in sorted_problems[:5]:  # Top 5 problems
            if severity < 0.2:
                continue

            # Find best parameters to address this problem
            solutions = self._find_solutions(problem, applied_effects)

            for param_name, score, direction in solutions[:2]:
                param = self.parameters.get(param_name)
                if not param:
                    continue

                # Check for conflicts
                side_effects = self._check_side_effects(param, direction, analysis)

                # Calculate confidence
                confidence = min(1, score * severity)

                # Get current value if available
                current_value = self._get_setup_value(param_name)
                suggested_value = self._suggest_value(param_name, direction, current_value)

                rec = Recommendation(
                    parameter=param.display_name,
                    direction=direction,
                    value=suggested_value,
                    reason=self._format_reason(problem, severity, param),
                    priority=int(severity * 10),
                    addresses=[problem],
                    side_effects=side_effects,
                    confidence=confidence
                )

                recommendations.append(rec)

                # Track effects
                for eff_problem, eff_value in param.effects.items():
                    mult = 1 if direction == "increase" else -1
                    applied_effects[eff_problem] = applied_effects.get(eff_problem, 0) + eff_value * mult

        # Sort by priority and remove duplicates
        seen = set()
        unique_recs = []
        for rec in sorted(recommendations, key=lambda x: x.priority, reverse=True):
            if rec.parameter not in seen:
                seen.add(rec.parameter)
                unique_recs.append(rec)

        return unique_recs[:5]  # Limit to 5 recommendations

    def _find_solutions(self, problem: Problem, applied_effects: Dict) -> List[Tuple[str, float, str]]:
        """Find parameters that help with a problem"""
        solutions = []

        for name, param in self.parameters.items():
            effect = param.effects.get(problem, 0)

            if effect == 0:
                continue

            # Negative effect means the parameter helps when increased
            if effect < 0:
                direction = "increase"
                score = abs(effect)
            else:
                direction = "decrease"
                score = abs(effect)

            # Penalize for conflicts with already applied effects
            for eff_problem, eff_value in param.effects.items():
                if eff_problem in applied_effects:
                    if (eff_value > 0 and applied_effects[eff_problem] < 0) or \
                       (eff_value < 0 and applied_effects[eff_problem] > 0):
                        score *= 0.5  # Conflict penalty

            if score > 0.1:
                solutions.append((name, score, direction))

        return sorted(solutions, key=lambda x: x[1], reverse=True)

    def _check_side_effects(self, param: SetupParameter, direction: str, analysis: LapAnalysis) -> List[str]:
        """Check for potential side effects"""
        side_effects = []
        mult = 1 if direction == "increase" else -1

        for problem, effect in param.effects.items():
            actual_effect = effect * mult

            # Positive effect means it makes the problem worse
            if actual_effect > 0.1:
                # Check if this problem already exists
                if problem in analysis.problems and analysis.problems[problem] > 0.3:
                    side_effects.append(f"Peut aggraver: {problem.value}")

        return side_effects

    def _get_setup_value(self, param_name: str) -> Optional[float]:
        """Get current value from loaded setup"""
        # Map param names to setup file keys
        # This depends on the setup file format
        return self.current_setup.get(param_name)

    def _suggest_value(self, param_name: str, direction: str, current: Optional[float]) -> str:
        """Suggest a new value based on direction"""
        if current is None:
            if direction == "increase":
                return "+1-2 clicks/points"
            else:
                return "-1-2 clicks/points"

        # Provide specific suggestion based on parameter type
        adjustments = {
            "front_spring": 5000,  # N/m
            "rear_spring": 5000,
            "front_arb": 5000,
            "rear_arb": 5000,
            "front_pressure": 3,  # kPa
            "rear_pressure": 3,
            "brake_bias": 1,  # %
            "front_camber": 0.2,  # deg
            "rear_camber": 0.2,
            "front_toe": 0.02,
            "rear_toe": 0.02,
            "front_wing": 1,
            "rear_wing": 1,
            "diff_power": 5,  # %
            "diff_coast": 5,
        }

        adj = adjustments.get(param_name, 1)
        if direction == "decrease":
            adj = -adj

        new_val = current + adj
        return f"{current} → {new_val}"

    def _format_reason(self, problem: Problem, severity: float, param: SetupParameter) -> str:
        """Format reason for recommendation"""
        problem_names = {
            Problem.UNDERSTEER_ENTRY: "sous-virage en entree",
            Problem.UNDERSTEER_MID: "sous-virage mi-virage",
            Problem.UNDERSTEER_EXIT: "sous-virage en sortie",
            Problem.OVERSTEER_ENTRY: "survirage en entree",
            Problem.OVERSTEER_MID: "survirage mi-virage",
            Problem.OVERSTEER_EXIT: "survirage en sortie",
            Problem.WHEELSPIN: "patinage",
            Problem.WHEEL_LOCK: "blocage roues",
            Problem.INSTABILITY_HIGH_SPEED: "instabilite haute vitesse",
            Problem.TIRE_OVERHEAT_FRONT: "surchauffe pneus avant",
            Problem.TIRE_OVERHEAT_REAR: "surchauffe pneus arriere",
            Problem.TIRE_COLD_FRONT: "pneus avant froids",
            Problem.TIRE_COLD_REAR: "pneus arriere froids",
            Problem.BRAKE_OVERHEAT_FRONT: "surchauffe freins avant",
            Problem.BRAKE_OVERHEAT_REAR: "surchauffe freins arriere",
            Problem.EXCESSIVE_ROLL: "roulis excessif",
            Problem.BOTTOMING: "talonnage",
            Problem.POOR_TRACTION: "manque de traction",
        }

        return f"Corrige {problem_names.get(problem, problem.value)} ({severity*100:.0f}%)"

    def get_summary(self) -> Dict[str, Any]:
        """Get current analysis summary"""
        if not self.lap_analyses:
            return {
                "status": "collecting",
                "message": "En attente de donnees...",
                "samples": len(self.samples)
            }

        analysis = self.lap_analyses[-1]

        # Calculate understeer/oversteer percentages
        understeer_sum = 0
        oversteer_sum = 0

        for phase in [CornerPhase.ENTRY, CornerPhase.MID, CornerPhase.EXIT]:
            if phase in analysis.behavior:
                understeer_sum += analysis.behavior[phase].get("understeer", 0)
                oversteer_sum += analysis.behavior[phase].get("oversteer", 0)

        understeer_pct = (understeer_sum / 3) * 100
        oversteer_pct = (oversteer_sum / 3) * 100

        return {
            "status": "ready",
            "lap_number": analysis.lap_number,
            "samples": analysis.sample_count,
            "vehicle": self.vehicle_name,
            "category": self.vehicle_category,
            "problems": {p.value: s for p, s in analysis.problems.items()},
            "understeer_pct": understeer_pct,
            "oversteer_pct": oversteer_pct,
            "traction_loss_pct": analysis.wheelspin_pct * 100,
            "tire_temps": {
                "FL": analysis.tire_temps_avg[0],
                "FR": analysis.tire_temps_avg[1],
                "RL": analysis.tire_temps_avg[2],
                "RR": analysis.tire_temps_avg[3]
            },
            "tire_temps_max": {
                "FL": analysis.tire_temps_max[0],
                "FR": analysis.tire_temps_max[1],
                "RL": analysis.tire_temps_max[2],
                "RR": analysis.tire_temps_max[3]
            },
            "brake_temps_max": {
                "FL": analysis.brake_temps_max[0],
                "FR": analysis.brake_temps_max[1],
                "RL": analysis.brake_temps_max[2],
                "RR": analysis.brake_temps_max[3]
            },
            "tire_pressure_avg": {
                "FL": analysis.tire_pressure_avg[0],
                "FR": analysis.tire_pressure_avg[1],
                "RL": analysis.tire_pressure_avg[2],
                "RR": analysis.tire_pressure_avg[3]
            },
            "tire_wear": {
                "FL": analysis.tire_wear_end[0] * 100,
                "FR": analysis.tire_wear_end[1] * 100,
                "RL": analysis.tire_wear_end[2] * 100,
                "RR": analysis.tire_wear_end[3] * 100
            },
            "stability_score": analysis.stability_score,
            "wheelspin_pct": analysis.wheelspin_pct,
            "lockup_pct": analysis.lockup_pct,
            "avg_rake": analysis.avg_rake,
            "bottoming_events": analysis.bottoming_events,
            "behavior": {
                phase.value: data for phase, data in analysis.behavior.items()
            }
        }
