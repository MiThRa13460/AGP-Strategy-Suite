"""
rFactor 2 Shared Memory Reader - Complete Implementation
Reads ALL shared memory maps: Telemetry, Scoring, Extended, ForceFeedback
Based on rF2 Shared Memory Plugin structures
"""

import ctypes
import mmap
import struct
from ctypes import wintypes
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import time

# Windows API
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

OpenFileMappingW = kernel32.OpenFileMappingW
OpenFileMappingW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
OpenFileMappingW.restype = wintypes.HANDLE

MapViewOfFile = kernel32.MapViewOfFile
MapViewOfFile.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, ctypes.c_size_t]
MapViewOfFile.restype = ctypes.c_void_p

UnmapViewOfFile = kernel32.UnmapViewOfFile
UnmapViewOfFile.argtypes = [ctypes.c_void_p]
UnmapViewOfFile.restype = wintypes.BOOL

CloseHandle = kernel32.CloseHandle
CloseHandle.argtypes = [wintypes.HANDLE]
CloseHandle.restype = wintypes.BOOL

FILE_MAP_READ = 0x0004
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

# Shared Memory Names
RF2_TELEMETRY_NAME = "$rFactor2SMMP_Telemetry$"
RF2_SCORING_NAME = "$rFactor2SMMP_Scoring$"
RF2_EXTENDED_NAME = "$rFactor2SMMP_Extended$"
RF2_FORCE_FEEDBACK_NAME = "$rFactor2SMMP_ForceFeedback$"

# Constants
MAX_MAPPED_VEHICLES = 128
MAX_MAPPED_IDS = 512


# ============= STRUCTURE DEFINITIONS =============

class rF2Vec3(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("x", ctypes.c_double),
        ("y", ctypes.c_double),
        ("z", ctypes.c_double)
    ]


class rF2Wheel(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("mSuspensionDeflection", ctypes.c_double),
        ("mRideHeight", ctypes.c_double),
        ("mSuspForce", ctypes.c_double),
        ("mBrakeTemp", ctypes.c_double),
        ("mBrakePressure", ctypes.c_double),
        ("mRotation", ctypes.c_double),
        ("mLateralPatchVel", ctypes.c_double),
        ("mLongitudinalPatchVel", ctypes.c_double),
        ("mLateralGroundVel", ctypes.c_double),
        ("mLongitudinalGroundVel", ctypes.c_double),
        ("mCamber", ctypes.c_double),
        ("mLateralForce", ctypes.c_double),
        ("mLongitudinalForce", ctypes.c_double),
        ("mTireLoad", ctypes.c_double),
        ("mGripFract", ctypes.c_double),
        ("mPressure", ctypes.c_double),
        ("mTemperature", ctypes.c_double * 3),  # inner/middle/outer
        ("mWear", ctypes.c_double),
        ("mTerrainName", ctypes.c_char * 16),
        ("mSurfaceType", ctypes.c_ubyte),
        ("mFlat", ctypes.c_ubyte),
        ("mDetached", ctypes.c_ubyte),
        ("mStaticUndeflectedRadius", ctypes.c_ubyte),
        ("mVerticalTireDeflection", ctypes.c_double),
        ("mWheelYLocation", ctypes.c_double),
        ("mToe", ctypes.c_double),
        ("mTireCarcassTemperature", ctypes.c_double),
        ("mTireInnerLayerTemperature", ctypes.c_double * 3),
        ("mExpansion", ctypes.c_ubyte * 20)
    ]


class rF2VehicleTelemetry(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("mID", ctypes.c_int),
        ("mDeltaTime", ctypes.c_double),
        ("mElapsedTime", ctypes.c_double),
        ("mLapNumber", ctypes.c_int),
        ("mLapStartET", ctypes.c_double),
        ("mVehicleName", ctypes.c_char * 64),
        ("mTrackName", ctypes.c_char * 64),
        ("mPos", rF2Vec3),
        ("mLocalVel", rF2Vec3),
        ("mLocalAccel", rF2Vec3),
        ("mOri", rF2Vec3 * 3),
        ("mLocalRot", rF2Vec3),
        ("mLocalRotAccel", rF2Vec3),
        ("mGear", ctypes.c_int),
        ("mEngineRPM", ctypes.c_double),
        ("mEngineWaterTemp", ctypes.c_double),
        ("mEngineOilTemp", ctypes.c_double),
        ("mClutchRPM", ctypes.c_double),
        ("mUnfilteredThrottle", ctypes.c_double),
        ("mUnfilteredBrake", ctypes.c_double),
        ("mUnfilteredSteering", ctypes.c_double),
        ("mUnfilteredClutch", ctypes.c_double),
        ("mFilteredThrottle", ctypes.c_double),
        ("mFilteredBrake", ctypes.c_double),
        ("mFilteredSteering", ctypes.c_double),
        ("mFilteredClutch", ctypes.c_double),
        ("mSteeringShaftTorque", ctypes.c_double),
        ("mFront3rdDeflection", ctypes.c_double),
        ("mRear3rdDeflection", ctypes.c_double),
        ("mFrontWingHeight", ctypes.c_double),
        ("mFrontRideHeight", ctypes.c_double),
        ("mRearRideHeight", ctypes.c_double),
        ("mDrag", ctypes.c_double),
        ("mFrontDownforce", ctypes.c_double),
        ("mRearDownforce", ctypes.c_double),
        ("mFuel", ctypes.c_double),
        ("mEngineMaxRPM", ctypes.c_double),
        ("mScheduledStops", ctypes.c_ubyte),
        ("mOverheating", ctypes.c_ubyte),
        ("mDetached", ctypes.c_ubyte),
        ("mHeadlights", ctypes.c_ubyte),
        ("mDentSeverity", ctypes.c_ubyte * 8),
        ("mLastImpactET", ctypes.c_double),
        ("mLastImpactMagnitude", ctypes.c_double),
        ("mLastImpactPos", rF2Vec3),
        ("mEngineTorque", ctypes.c_double),
        ("mCurrentSector", ctypes.c_int),
        ("mSpeedLimiter", ctypes.c_ubyte),
        ("mMaxGears", ctypes.c_ubyte),
        ("mFrontTireCompoundIndex", ctypes.c_ubyte),
        ("mRearTireCompoundIndex", ctypes.c_ubyte),
        ("mFuelCapacity", ctypes.c_double),
        ("mFrontFlapActivated", ctypes.c_ubyte),
        ("mRearFlapActivated", ctypes.c_ubyte),
        ("mRearFlapLegalStatus", ctypes.c_ubyte),
        ("mIgnitionStarter", ctypes.c_ubyte),
        ("mFrontTireCompoundName", ctypes.c_char * 18),
        ("mRearTireCompoundName", ctypes.c_char * 18),
        ("mSpeedLimiterAvailable", ctypes.c_ubyte),
        ("mAntiStallActivated", ctypes.c_ubyte),
        ("mUnused", ctypes.c_ubyte * 2),
        ("mVisualSteeringWheelRange", ctypes.c_float),
        ("mRearBrakeBias", ctypes.c_double),
        ("mTurboBoostPressure", ctypes.c_double),
        ("mPhysicsToGraphicsOffset", ctypes.c_float * 3),
        ("mPhysicalSteeringWheelRange", ctypes.c_float),
        ("mExpansion", ctypes.c_ubyte * 152),
        ("mWheels", rF2Wheel * 4)
    ]


class rF2Telemetry(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("mVersionUpdateBegin", ctypes.c_int),
        ("mVersionUpdateEnd", ctypes.c_int),
        ("mBytesUpdatedHint", ctypes.c_int),
        ("mNumVehicles", ctypes.c_int),
        ("mVehicles", rF2VehicleTelemetry * MAX_MAPPED_VEHICLES)
    ]


# Scoring structures
class rF2VehicleScoring(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("mID", ctypes.c_int),
        ("mDriverName", ctypes.c_char * 32),
        ("mVehicleName", ctypes.c_char * 64),
        ("mTotalLaps", ctypes.c_short),
        ("mSector", ctypes.c_byte),
        ("mFinishStatus", ctypes.c_byte),
        ("mLapDist", ctypes.c_double),
        ("mPathLateral", ctypes.c_double),
        ("mTrackEdge", ctypes.c_double),
        ("mBestSector1", ctypes.c_double),
        ("mBestSector2", ctypes.c_double),
        ("mBestLapTime", ctypes.c_double),
        ("mLastSector1", ctypes.c_double),
        ("mLastSector2", ctypes.c_double),
        ("mLastLapTime", ctypes.c_double),
        ("mCurSector1", ctypes.c_double),
        ("mCurSector2", ctypes.c_double),
        ("mNumPitstops", ctypes.c_short),
        ("mNumPenalties", ctypes.c_short),
        ("mIsPlayer", ctypes.c_ubyte),
        ("mControl", ctypes.c_byte),
        ("mInPits", ctypes.c_ubyte),
        ("mPlace", ctypes.c_ubyte),
        ("mVehicleClass", ctypes.c_char * 32),
        ("mTimeBehindNext", ctypes.c_double),
        ("mLapsBehindNext", ctypes.c_int),
        ("mTimeBehindLeader", ctypes.c_double),
        ("mLapsBehindLeader", ctypes.c_int),
        ("mLapStartET", ctypes.c_double),
        ("mPos", rF2Vec3),
        ("mLocalVel", rF2Vec3),
        ("mLocalAccel", rF2Vec3),
        ("mOri", rF2Vec3 * 3),
        ("mLocalRot", rF2Vec3),
        ("mLocalRotAccel", rF2Vec3),
        ("mSpeed", ctypes.c_double),
        ("mHeadlights", ctypes.c_ubyte),
        ("mPitState", ctypes.c_ubyte),
        ("mServerScored", ctypes.c_ubyte),
        ("mIndividualPhase", ctypes.c_ubyte),
        ("mQualification", ctypes.c_int),
        ("mTimeIntoLap", ctypes.c_double),
        ("mEstimatedLapTime", ctypes.c_double),
        ("mPitGroup", ctypes.c_char * 24),
        ("mFlag", ctypes.c_ubyte),
        ("mUnderYellow", ctypes.c_ubyte),
        ("mCountLapFlag", ctypes.c_ubyte),
        ("mInGarageStall", ctypes.c_ubyte),
        ("mUpgradePack", ctypes.c_char * 16),
        ("mPitLapDist", ctypes.c_float),
        ("mBestLapSector1", ctypes.c_double),
        ("mBestLapSector2", ctypes.c_double),
        ("mExpansion", ctypes.c_ubyte * 48)
    ]


class rF2Scoring(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("mVersionUpdateBegin", ctypes.c_int),
        ("mVersionUpdateEnd", ctypes.c_int),
        ("mBytesUpdatedHint", ctypes.c_int),
        ("mTrackName", ctypes.c_char * 64),
        ("mSession", ctypes.c_int),
        ("mCurrentET", ctypes.c_double),
        ("mEndET", ctypes.c_double),
        ("mMaxLaps", ctypes.c_int),
        ("mLapDist", ctypes.c_double),
        ("mNumVehicles", ctypes.c_int),
        ("mGamePhase", ctypes.c_ubyte),
        ("mYellowFlagState", ctypes.c_byte),
        ("mSectorFlag", ctypes.c_byte * 3),
        ("mStartLight", ctypes.c_ubyte),
        ("mNumRedLights", ctypes.c_ubyte),
        ("mInRealtime", ctypes.c_ubyte),
        ("mPlayerName", ctypes.c_char * 32),
        ("mPlrFileName", ctypes.c_char * 64),
        ("mDarkCloud", ctypes.c_double),
        ("mRaining", ctypes.c_double),
        ("mAmbientTemp", ctypes.c_double),
        ("mTrackTemp", ctypes.c_double),
        ("mWind", rF2Vec3),
        ("mMinPathWetness", ctypes.c_double),
        ("mMaxPathWetness", ctypes.c_double),
        ("mGameMode", ctypes.c_ubyte),
        ("mIsPasswordProtected", ctypes.c_ubyte),
        ("mServerPort", ctypes.c_ushort),
        ("mServerPublicIP", ctypes.c_uint),
        ("mMaxPlayers", ctypes.c_int),
        ("mServerName", ctypes.c_char * 32),
        ("mStartET", ctypes.c_double),
        ("mAvgPathWetness", ctypes.c_double),
        ("mExpansion", ctypes.c_ubyte * 200),
        ("mVehicles", rF2VehicleScoring * MAX_MAPPED_VEHICLES)
    ]


# Extended data structures
class rF2TrackedDamage(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("mMaxImpactMagnitude", ctypes.c_double),
        ("mAccumulatedImpactMagnitude", ctypes.c_double)
    ]


class rF2PhysicsOptions(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("mTractionControl", ctypes.c_ubyte),
        ("mAntiLockBrakes", ctypes.c_ubyte),
        ("mStabilityControl", ctypes.c_ubyte),
        ("mAutoShift", ctypes.c_ubyte),
        ("mAutoClutch", ctypes.c_ubyte),
        ("mInvulnerable", ctypes.c_ubyte),
        ("mOppositeLock", ctypes.c_ubyte),
        ("mSteeringHelp", ctypes.c_ubyte),
        ("mBrakingHelp", ctypes.c_ubyte),
        ("mSpinRecovery", ctypes.c_ubyte),
        ("mAutoPit", ctypes.c_ubyte),
        ("mAutoLift", ctypes.c_ubyte),
        ("mAutoBlip", ctypes.c_ubyte),
        ("mFuelMult", ctypes.c_ubyte),
        ("mTireMult", ctypes.c_ubyte),
        ("mMechFail", ctypes.c_ubyte),
        ("mAllowPitcrewPush", ctypes.c_ubyte),
        ("mRepeatShifts", ctypes.c_ubyte),
        ("mHoldClutch", ctypes.c_ubyte),
        ("mAutoReverse", ctypes.c_ubyte),
        ("mAlternateNeutral", ctypes.c_ubyte),
        ("mAIControl", ctypes.c_ubyte),
        ("mUnused1", ctypes.c_ubyte),
        ("mUnused2", ctypes.c_ubyte),
        ("mManualShiftOverrideTime", ctypes.c_float),
        ("mAutoShiftOverrideTime", ctypes.c_float),
        ("mSpeedSensitiveSteering", ctypes.c_float),
        ("mSteerRatioSpeed", ctypes.c_float)
    ]


class rF2Extended(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("mVersionUpdateBegin", ctypes.c_int),
        ("mVersionUpdateEnd", ctypes.c_int),
        ("mVersion", ctypes.c_char * 8),
        ("mIs64bit", ctypes.c_ubyte),
        ("mPhysics", rF2PhysicsOptions),
        ("mTrackedDamages", rF2TrackedDamage * MAX_MAPPED_IDS),
        ("mInRealtimeFC", ctypes.c_ubyte),
        ("mMultimediaThreadStarted", ctypes.c_ubyte),
        ("mSimulationThreadStarted", ctypes.c_ubyte),
        ("mSessionStarted", ctypes.c_ubyte),
        ("mTicksSessionStarted", ctypes.c_longlong),
        ("mTicksSessionEnded", ctypes.c_longlong),
        ("mSessionTransitionCapture", ctypes.c_double * 6),
        ("mDisplayedMessageUpdateCapture", ctypes.c_char * 128),
        ("mDirectMemoryAccessEnabled", ctypes.c_ubyte),
        ("mUnsubscribedBuffersMask", ctypes.c_int),
        ("mExpansion", ctypes.c_ubyte * 4000)
    ]


class rF2ForceFeedback(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("mVersionUpdateBegin", ctypes.c_int),
        ("mVersionUpdateEnd", ctypes.c_int),
        ("mForceValue", ctypes.c_double)
    ]


# ============= DATA CLASSES FOR CLEAN OUTPUT =============

@dataclass
class WheelData:
    suspension_deflection: float = 0.0
    ride_height: float = 0.0
    susp_force: float = 0.0
    brake_temp: float = 0.0
    brake_pressure: float = 0.0
    rotation: float = 0.0
    camber: float = 0.0
    lateral_force: float = 0.0
    longitudinal_force: float = 0.0
    tire_load: float = 0.0
    grip: float = 0.0
    pressure: float = 0.0
    temp_inner: float = 0.0
    temp_middle: float = 0.0
    temp_outer: float = 0.0
    temp_avg: float = 0.0
    wear: float = 0.0
    toe: float = 0.0
    carcass_temp: float = 0.0
    flat: bool = False
    surface_type: int = 0


@dataclass
class TelemetryData:
    # Identity
    vehicle_name: str = ""
    track_name: str = ""
    driver_id: int = 0

    # Position
    pos_x: float = 0.0
    pos_y: float = 0.0
    pos_z: float = 0.0

    # Speed & Motion
    speed: float = 0.0
    speed_kmh: float = 0.0
    local_vel_x: float = 0.0
    local_vel_y: float = 0.0
    local_vel_z: float = 0.0

    # Acceleration
    g_long: float = 0.0
    g_lat: float = 0.0
    g_vert: float = 0.0

    # Engine
    rpm: float = 0.0
    rpm_max: float = 0.0
    gear: int = 0
    max_gears: int = 0
    engine_torque: float = 0.0
    water_temp: float = 0.0
    oil_temp: float = 0.0
    overheating: bool = False
    turbo_boost: float = 0.0

    # Inputs
    throttle: float = 0.0
    brake: float = 0.0
    steering: float = 0.0
    clutch: float = 0.0
    steering_torque: float = 0.0

    # Fuel
    fuel: float = 0.0
    fuel_capacity: float = 0.0
    fuel_pct: float = 0.0

    # Lap
    lap_number: int = 0
    current_sector: int = 0
    lap_start_et: float = 0.0
    elapsed_time: float = 0.0

    # Aero & Chassis
    front_ride_height: float = 0.0
    rear_ride_height: float = 0.0
    rake: float = 0.0
    front_downforce: float = 0.0
    rear_downforce: float = 0.0
    drag: float = 0.0
    front_wing_height: float = 0.0
    rear_brake_bias: float = 0.0

    # Compounds
    front_tire_compound: str = ""
    rear_tire_compound: str = ""

    # Wheels
    wheels: List[WheelData] = field(default_factory=lambda: [WheelData() for _ in range(4)])

    # Aggregated tire data
    tire_temp_fl: float = 0.0
    tire_temp_fr: float = 0.0
    tire_temp_rl: float = 0.0
    tire_temp_rr: float = 0.0

    tire_pressure_fl: float = 0.0
    tire_pressure_fr: float = 0.0
    tire_pressure_rl: float = 0.0
    tire_pressure_rr: float = 0.0

    tire_wear_fl: float = 0.0
    tire_wear_fr: float = 0.0
    tire_wear_rl: float = 0.0
    tire_wear_rr: float = 0.0

    brake_temp_fl: float = 0.0
    brake_temp_fr: float = 0.0
    brake_temp_rl: float = 0.0
    brake_temp_rr: float = 0.0

    grip_fl: float = 0.0
    grip_fr: float = 0.0
    grip_rl: float = 0.0
    grip_rr: float = 0.0

    # Damage
    last_impact_magnitude: float = 0.0


@dataclass
class ScoringData:
    # Session
    track_name: str = ""
    session_type: int = 0
    current_time: float = 0.0
    end_time: float = 0.0
    max_laps: int = 0
    lap_distance: float = 0.0
    num_vehicles: int = 0
    game_phase: int = 0
    in_realtime: bool = False

    # Weather
    ambient_temp: float = 0.0
    track_temp: float = 0.0
    raining: float = 0.0
    dark_cloud: float = 0.0
    wind_x: float = 0.0
    wind_y: float = 0.0
    wind_z: float = 0.0
    min_path_wetness: float = 0.0
    max_path_wetness: float = 0.0
    avg_path_wetness: float = 0.0

    # Flags
    yellow_flag_state: int = 0
    sector_flags: List[int] = field(default_factory=lambda: [0, 0, 0])
    start_light: int = 0

    # Player
    player_name: str = ""


@dataclass
class VehicleScoringData:
    driver_id: int = 0
    driver_name: str = ""
    vehicle_name: str = ""
    vehicle_class: str = ""

    # Position
    place: int = 0
    total_laps: int = 0
    current_sector: int = 0
    lap_dist: float = 0.0

    # Times
    best_lap_time: float = 0.0
    last_lap_time: float = 0.0
    best_sector1: float = 0.0
    best_sector2: float = 0.0
    last_sector1: float = 0.0
    last_sector2: float = 0.0
    cur_sector1: float = 0.0
    cur_sector2: float = 0.0
    time_into_lap: float = 0.0
    estimated_lap_time: float = 0.0

    # Gaps
    time_behind_next: float = 0.0
    laps_behind_next: int = 0
    time_behind_leader: float = 0.0
    laps_behind_leader: int = 0

    # Status
    is_player: bool = False
    in_pits: bool = False
    pit_state: int = 0
    num_pitstops: int = 0
    num_penalties: int = 0
    finish_status: int = 0
    flag: int = 0
    under_yellow: bool = False

    # Speed
    speed: float = 0.0


@dataclass
class ExtendedData:
    # Physics options
    traction_control: int = 0
    abs: int = 0
    stability_control: int = 0
    auto_shift: int = 0
    fuel_mult: int = 0
    tire_mult: int = 0

    # Session
    in_realtime: bool = False
    session_started: bool = False


# ============= MAIN READER CLASS =============

class RF2SharedMemory:
    def __init__(self):
        self.telemetry_handle = None
        self.telemetry_view = None
        self.scoring_handle = None
        self.scoring_view = None
        self.extended_handle = None
        self.extended_view = None
        self.ffb_handle = None
        self.ffb_view = None

        self.connected = False
        self.last_error = ""

    def connect(self) -> bool:
        """Connect to all rF2 shared memory maps"""
        try:
            # Telemetry
            self.telemetry_handle = OpenFileMappingW(FILE_MAP_READ, False, RF2_TELEMETRY_NAME)
            if self.telemetry_handle:
                self.telemetry_view = MapViewOfFile(self.telemetry_handle, FILE_MAP_READ, 0, 0, 0)

            # Scoring
            self.scoring_handle = OpenFileMappingW(FILE_MAP_READ, False, RF2_SCORING_NAME)
            if self.scoring_handle:
                self.scoring_view = MapViewOfFile(self.scoring_handle, FILE_MAP_READ, 0, 0, 0)

            # Extended
            self.extended_handle = OpenFileMappingW(FILE_MAP_READ, False, RF2_EXTENDED_NAME)
            if self.extended_handle:
                self.extended_view = MapViewOfFile(self.extended_handle, FILE_MAP_READ, 0, 0, 0)

            # Force Feedback
            self.ffb_handle = OpenFileMappingW(FILE_MAP_READ, False, RF2_FORCE_FEEDBACK_NAME)
            if self.ffb_handle:
                self.ffb_view = MapViewOfFile(self.ffb_handle, FILE_MAP_READ, 0, 0, 0)

            self.connected = bool(self.telemetry_view)

            if not self.connected:
                self.last_error = "rF2 not running or Shared Memory plugin not installed"

            return self.connected

        except Exception as e:
            self.last_error = str(e)
            return False

    def disconnect(self):
        """Disconnect from all shared memory maps"""
        if self.telemetry_view:
            UnmapViewOfFile(self.telemetry_view)
        if self.telemetry_handle:
            CloseHandle(self.telemetry_handle)
        if self.scoring_view:
            UnmapViewOfFile(self.scoring_view)
        if self.scoring_handle:
            CloseHandle(self.scoring_handle)
        if self.extended_view:
            UnmapViewOfFile(self.extended_view)
        if self.extended_handle:
            CloseHandle(self.extended_handle)
        if self.ffb_view:
            UnmapViewOfFile(self.ffb_view)
        if self.ffb_handle:
            CloseHandle(self.ffb_handle)

        self.telemetry_handle = None
        self.telemetry_view = None
        self.scoring_handle = None
        self.scoring_view = None
        self.extended_handle = None
        self.extended_view = None
        self.ffb_handle = None
        self.ffb_view = None
        self.connected = False

    def _kelvin_to_celsius(self, kelvin: float) -> float:
        if kelvin < 100:
            return kelvin  # Already Celsius
        return kelvin - 273.15

    def _read_telemetry_raw(self) -> Optional[rF2Telemetry]:
        """Read raw telemetry structure"""
        if not self.telemetry_view:
            return None

        return ctypes.cast(self.telemetry_view, ctypes.POINTER(rF2Telemetry)).contents

    def _read_scoring_raw(self) -> Optional[rF2Scoring]:
        """Read raw scoring structure"""
        if not self.scoring_view:
            return None

        return ctypes.cast(self.scoring_view, ctypes.POINTER(rF2Scoring)).contents

    def _read_extended_raw(self) -> Optional[rF2Extended]:
        """Read raw extended structure"""
        if not self.extended_view:
            return None

        return ctypes.cast(self.extended_view, ctypes.POINTER(rF2Extended)).contents

    def _read_ffb_raw(self) -> Optional[rF2ForceFeedback]:
        """Read raw force feedback structure"""
        if not self.ffb_view:
            return None

        return ctypes.cast(self.ffb_view, ctypes.POINTER(rF2ForceFeedback)).contents

    def read_telemetry(self) -> Optional[TelemetryData]:
        """Read and process telemetry data for player vehicle"""
        raw = self._read_telemetry_raw()
        if not raw or raw.mNumVehicles <= 0:
            return None

        # Check version consistency
        if raw.mVersionUpdateBegin != raw.mVersionUpdateEnd:
            return None  # Data being updated

        # Find player vehicle (first one or marked as player in scoring)
        veh = raw.mVehicles[0]

        data = TelemetryData()

        # Identity
        data.vehicle_name = veh.mVehicleName.decode('utf-8', errors='ignore').strip('\x00')
        data.track_name = veh.mTrackName.decode('utf-8', errors='ignore').strip('\x00')
        data.driver_id = veh.mID

        # Position
        data.pos_x = veh.mPos.x
        data.pos_y = veh.mPos.y
        data.pos_z = veh.mPos.z

        # Speed
        data.local_vel_x = veh.mLocalVel.x
        data.local_vel_y = veh.mLocalVel.y
        data.local_vel_z = veh.mLocalVel.z
        data.speed = (veh.mLocalVel.x**2 + veh.mLocalVel.y**2 + veh.mLocalVel.z**2)**0.5
        data.speed_kmh = data.speed * 3.6

        # G-forces
        data.g_long = veh.mLocalAccel.x / 9.81
        data.g_lat = veh.mLocalAccel.z / 9.81
        data.g_vert = veh.mLocalAccel.y / 9.81

        # Engine
        data.rpm = veh.mEngineRPM
        data.rpm_max = veh.mEngineMaxRPM
        data.gear = veh.mGear
        data.max_gears = veh.mMaxGears
        data.engine_torque = veh.mEngineTorque
        data.water_temp = self._kelvin_to_celsius(veh.mEngineWaterTemp)
        data.oil_temp = self._kelvin_to_celsius(veh.mEngineOilTemp)
        data.overheating = bool(veh.mOverheating)
        data.turbo_boost = veh.mTurboBoostPressure

        # Inputs
        data.throttle = veh.mUnfilteredThrottle
        data.brake = veh.mUnfilteredBrake
        data.steering = veh.mUnfilteredSteering
        data.clutch = veh.mUnfilteredClutch
        data.steering_torque = veh.mSteeringShaftTorque

        # Fuel
        data.fuel = veh.mFuel
        data.fuel_capacity = veh.mFuelCapacity
        data.fuel_pct = (veh.mFuel / veh.mFuelCapacity * 100) if veh.mFuelCapacity > 0 else 0

        # Lap
        data.lap_number = veh.mLapNumber
        data.current_sector = veh.mCurrentSector
        data.lap_start_et = veh.mLapStartET
        data.elapsed_time = veh.mElapsedTime

        # Aero & Chassis
        data.front_ride_height = veh.mFrontRideHeight * 1000  # m to mm
        data.rear_ride_height = veh.mRearRideHeight * 1000
        data.rake = (veh.mRearRideHeight - veh.mFrontRideHeight) * 1000
        data.front_downforce = veh.mFrontDownforce
        data.rear_downforce = veh.mRearDownforce
        data.drag = veh.mDrag
        data.front_wing_height = veh.mFrontWingHeight
        data.rear_brake_bias = veh.mRearBrakeBias

        # Compounds
        data.front_tire_compound = veh.mFrontTireCompoundName.decode('utf-8', errors='ignore').strip('\x00')
        data.rear_tire_compound = veh.mRearTireCompoundName.decode('utf-8', errors='ignore').strip('\x00')

        # Damage
        data.last_impact_magnitude = veh.mLastImpactMagnitude

        # Process wheels
        for i in range(4):
            w = veh.mWheels[i]
            wd = WheelData()

            wd.suspension_deflection = w.mSuspensionDeflection
            wd.ride_height = w.mRideHeight * 1000  # m to mm
            wd.susp_force = w.mSuspForce
            wd.brake_temp = self._kelvin_to_celsius(w.mBrakeTemp)
            wd.brake_pressure = w.mBrakePressure
            wd.rotation = w.mRotation
            wd.camber = w.mCamber * 57.2958  # rad to deg
            wd.lateral_force = w.mLateralForce
            wd.longitudinal_force = w.mLongitudinalForce
            wd.tire_load = w.mTireLoad
            wd.grip = w.mGripFract
            wd.pressure = w.mPressure
            wd.temp_inner = self._kelvin_to_celsius(w.mTemperature[0])
            wd.temp_middle = self._kelvin_to_celsius(w.mTemperature[1])
            wd.temp_outer = self._kelvin_to_celsius(w.mTemperature[2])
            wd.temp_avg = (wd.temp_inner + wd.temp_middle + wd.temp_outer) / 3
            wd.wear = w.mWear
            wd.toe = w.mToe * 57.2958  # rad to deg
            wd.carcass_temp = self._kelvin_to_celsius(w.mTireCarcassTemperature)
            wd.flat = bool(w.mFlat)
            wd.surface_type = w.mSurfaceType

            data.wheels[i] = wd

        # Aggregated data for easy access
        data.tire_temp_fl = data.wheels[0].temp_avg
        data.tire_temp_fr = data.wheels[1].temp_avg
        data.tire_temp_rl = data.wheels[2].temp_avg
        data.tire_temp_rr = data.wheels[3].temp_avg

        data.tire_pressure_fl = data.wheels[0].pressure
        data.tire_pressure_fr = data.wheels[1].pressure
        data.tire_pressure_rl = data.wheels[2].pressure
        data.tire_pressure_rr = data.wheels[3].pressure

        data.tire_wear_fl = 1 - data.wheels[0].wear
        data.tire_wear_fr = 1 - data.wheels[1].wear
        data.tire_wear_rl = 1 - data.wheels[2].wear
        data.tire_wear_rr = 1 - data.wheels[3].wear

        data.brake_temp_fl = data.wheels[0].brake_temp
        data.brake_temp_fr = data.wheels[1].brake_temp
        data.brake_temp_rl = data.wheels[2].brake_temp
        data.brake_temp_rr = data.wheels[3].brake_temp

        data.grip_fl = data.wheels[0].grip
        data.grip_fr = data.wheels[1].grip
        data.grip_rl = data.wheels[2].grip
        data.grip_rr = data.wheels[3].grip

        return data

    def read_scoring(self) -> Optional[ScoringData]:
        """Read session/race scoring data"""
        raw = self._read_scoring_raw()
        if not raw:
            return None

        if raw.mVersionUpdateBegin != raw.mVersionUpdateEnd:
            return None

        data = ScoringData()

        data.track_name = raw.mTrackName.decode('utf-8', errors='ignore').strip('\x00')
        data.session_type = raw.mSession
        data.current_time = raw.mCurrentET
        data.end_time = raw.mEndET
        data.max_laps = raw.mMaxLaps
        data.lap_distance = raw.mLapDist
        data.num_vehicles = raw.mNumVehicles
        data.game_phase = raw.mGamePhase
        data.in_realtime = bool(raw.mInRealtime)

        # Weather
        data.ambient_temp = raw.mAmbientTemp
        data.track_temp = raw.mTrackTemp
        data.raining = raw.mRaining
        data.dark_cloud = raw.mDarkCloud
        data.wind_x = raw.mWind.x
        data.wind_y = raw.mWind.y
        data.wind_z = raw.mWind.z
        data.min_path_wetness = raw.mMinPathWetness
        data.max_path_wetness = raw.mMaxPathWetness
        data.avg_path_wetness = raw.mAvgPathWetness

        # Flags
        data.yellow_flag_state = raw.mYellowFlagState
        data.sector_flags = [raw.mSectorFlag[i] for i in range(3)]
        data.start_light = raw.mStartLight

        data.player_name = raw.mPlayerName.decode('utf-8', errors='ignore').strip('\x00')

        return data

    def read_vehicle_scoring(self, vehicle_index: int = 0) -> Optional[VehicleScoringData]:
        """Read scoring data for a specific vehicle"""
        raw = self._read_scoring_raw()
        if not raw or vehicle_index >= raw.mNumVehicles:
            return None

        veh = raw.mVehicles[vehicle_index]

        data = VehicleScoringData()

        data.driver_id = veh.mID
        data.driver_name = veh.mDriverName.decode('utf-8', errors='ignore').strip('\x00')
        data.vehicle_name = veh.mVehicleName.decode('utf-8', errors='ignore').strip('\x00')
        data.vehicle_class = veh.mVehicleClass.decode('utf-8', errors='ignore').strip('\x00')

        data.place = veh.mPlace
        data.total_laps = veh.mTotalLaps
        data.current_sector = veh.mSector
        data.lap_dist = veh.mLapDist

        data.best_lap_time = veh.mBestLapTime
        data.last_lap_time = veh.mLastLapTime
        data.best_sector1 = veh.mBestSector1
        data.best_sector2 = veh.mBestSector2
        data.last_sector1 = veh.mLastSector1
        data.last_sector2 = veh.mLastSector2
        data.cur_sector1 = veh.mCurSector1
        data.cur_sector2 = veh.mCurSector2
        data.time_into_lap = veh.mTimeIntoLap
        data.estimated_lap_time = veh.mEstimatedLapTime

        data.time_behind_next = veh.mTimeBehindNext
        data.laps_behind_next = veh.mLapsBehindNext
        data.time_behind_leader = veh.mTimeBehindLeader
        data.laps_behind_leader = veh.mLapsBehindLeader

        data.is_player = bool(veh.mIsPlayer)
        data.in_pits = bool(veh.mInPits)
        data.pit_state = veh.mPitState
        data.num_pitstops = veh.mNumPitstops
        data.num_penalties = veh.mNumPenalties
        data.finish_status = veh.mFinishStatus
        data.flag = veh.mFlag
        data.under_yellow = bool(veh.mUnderYellow)

        data.speed = veh.mSpeed * 3.6  # m/s to km/h

        return data

    def read_player_scoring(self) -> Optional[VehicleScoringData]:
        """Find and read scoring data for the player"""
        raw = self._read_scoring_raw()
        if not raw:
            return None

        for i in range(raw.mNumVehicles):
            veh = raw.mVehicles[i]
            if veh.mIsPlayer:
                return self.read_vehicle_scoring(i)

        return self.read_vehicle_scoring(0)  # Fallback to first vehicle

    def read_all_vehicles_scoring(self) -> List[VehicleScoringData]:
        """Read scoring data for all vehicles"""
        raw = self._read_scoring_raw()
        if not raw:
            return []

        vehicles = []
        for i in range(raw.mNumVehicles):
            veh = self.read_vehicle_scoring(i)
            if veh:
                vehicles.append(veh)

        return vehicles

    def read_extended(self) -> Optional[ExtendedData]:
        """Read extended data"""
        raw = self._read_extended_raw()
        if not raw:
            return None

        data = ExtendedData()

        data.traction_control = raw.mPhysics.mTractionControl
        data.abs = raw.mPhysics.mAntiLockBrakes
        data.stability_control = raw.mPhysics.mStabilityControl
        data.auto_shift = raw.mPhysics.mAutoShift
        data.fuel_mult = raw.mPhysics.mFuelMult
        data.tire_mult = raw.mPhysics.mTireMult

        data.in_realtime = bool(raw.mInRealtimeFC)
        data.session_started = bool(raw.mSessionStarted)

        return data

    def read_force_feedback(self) -> Optional[float]:
        """Read force feedback value"""
        raw = self._read_ffb_raw()
        if not raw:
            return None

        return raw.mForceValue

    def read_all(self) -> Dict[str, Any]:
        """Read all available data at once"""
        return {
            'telemetry': self.read_telemetry(),
            'scoring': self.read_scoring(),
            'player_scoring': self.read_player_scoring(),
            'extended': self.read_extended(),
            'force_feedback': self.read_force_feedback(),
            'timestamp': time.time()
        }


# ============= TEST =============

if __name__ == "__main__":
    reader = RF2SharedMemory()

    print("Connecting to rFactor 2...")
    if reader.connect():
        print("Connected!")

        while True:
            try:
                data = reader.read_all()

                if data['telemetry']:
                    t = data['telemetry']
                    print(f"\n--- Telemetry ---")
                    print(f"Vehicle: {t.vehicle_name}")
                    print(f"Track: {t.track_name}")
                    print(f"Speed: {t.speed_kmh:.1f} km/h")
                    print(f"RPM: {t.rpm:.0f} / {t.rpm_max:.0f}")
                    print(f"Gear: {t.gear}")
                    print(f"Fuel: {t.fuel:.1f}L ({t.fuel_pct:.1f}%)")
                    print(f"Water: {t.water_temp:.1f}°C | Oil: {t.oil_temp:.1f}°C")
                    print(f"G-Force: Long {t.g_long:.2f}g | Lat {t.g_lat:.2f}g")
                    print(f"Tires: FL {t.tire_temp_fl:.0f}°C | FR {t.tire_temp_fr:.0f}°C")
                    print(f"        RL {t.tire_temp_rl:.0f}°C | RR {t.tire_temp_rr:.0f}°C")
                    print(f"Brakes: FL {t.brake_temp_fl:.0f}°C | FR {t.brake_temp_fr:.0f}°C")
                    print(f"Ride Height: F {t.front_ride_height:.1f}mm | R {t.rear_ride_height:.1f}mm")

                if data['scoring']:
                    s = data['scoring']
                    print(f"\n--- Scoring ---")
                    print(f"Track Temp: {s.track_temp:.1f}°C | Ambient: {s.ambient_temp:.1f}°C")
                    print(f"Rain: {s.raining:.2f} | Wetness: {s.avg_path_wetness:.2f}")

                if data['player_scoring']:
                    p = data['player_scoring']
                    print(f"\n--- Player ---")
                    print(f"Position: P{p.place} | Lap {p.total_laps}")
                    print(f"Best Lap: {p.best_lap_time:.3f}s")
                    print(f"Gap to leader: {p.time_behind_leader:.3f}s")

                time.sleep(0.5)

            except KeyboardInterrupt:
                break

        reader.disconnect()
        print("\nDisconnected")
    else:
        print(f"Failed to connect: {reader.last_error}")
