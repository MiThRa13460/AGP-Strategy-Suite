"""
CSV Parser for telemetry data.

Supports multiple formats:
- MoTeC CSV export
- rFactor 2 native telemetry
- ACC MoTeC format
- Generic CSV with auto-detection
"""

from __future__ import annotations
import csv
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterator
from datetime import datetime
import logging

from agp_core.setup.telemetry_models import (
    TelemetryPoint,
    LapData,
    SessionData,
)

logger = logging.getLogger(__name__)


class CSVFormat(Enum):
    """Supported CSV formats."""
    MOTEC = "motec"
    RF2 = "rf2"
    ACC = "acc"
    IRACING = "iracing"
    GENERIC = "generic"
    AUTO = "auto"


@dataclass
class ColumnMapping:
    """Mapping of CSV columns to telemetry fields."""

    # Time/Distance
    time: str | None = None
    distance: str | None = None
    lap: str | None = None

    # Vehicle
    speed: str | None = None
    rpm: str | None = None
    gear: str | None = None

    # Inputs
    throttle: str | None = None
    brake: str | None = None
    steering: str | None = None
    clutch: str | None = None

    # Forces
    g_lat: str | None = None
    g_long: str | None = None

    # Tires - Temps
    tire_temp_fl: str | None = None
    tire_temp_fr: str | None = None
    tire_temp_rl: str | None = None
    tire_temp_rr: str | None = None

    # Tires - Pressure
    tire_pressure_fl: str | None = None
    tire_pressure_fr: str | None = None
    tire_pressure_rl: str | None = None
    tire_pressure_rr: str | None = None

    # Tires - Wear
    tire_wear_fl: str | None = None
    tire_wear_fr: str | None = None
    tire_wear_rl: str | None = None
    tire_wear_rr: str | None = None

    # Slip angles
    slip_angle_fl: str | None = None
    slip_angle_fr: str | None = None
    slip_angle_rl: str | None = None
    slip_angle_rr: str | None = None

    # Slip ratios
    slip_ratio_fl: str | None = None
    slip_ratio_fr: str | None = None
    slip_ratio_rl: str | None = None
    slip_ratio_rr: str | None = None

    # Suspension
    ride_height_fl: str | None = None
    ride_height_fr: str | None = None
    ride_height_rl: str | None = None
    ride_height_rr: str | None = None

    susp_travel_fl: str | None = None
    susp_travel_fr: str | None = None
    susp_travel_rl: str | None = None
    susp_travel_rr: str | None = None

    # Brakes
    brake_temp_fl: str | None = None
    brake_temp_fr: str | None = None
    brake_temp_rl: str | None = None
    brake_temp_rr: str | None = None

    # Other
    fuel: str | None = None


# Predefined mappings for known formats
MOTEC_MAPPING = ColumnMapping(
    time="Time",
    distance="Distance",
    lap="Lap",
    speed="Ground Speed",
    rpm="Engine RPM",
    gear="Gear",
    throttle="Throttle Pos",
    brake="Brake Pos",
    steering="Steered Angle",
    clutch="Clutch Pos",
    g_lat="G Force Lat",
    g_long="G Force Long",
    tire_temp_fl="Tyre Temp FL",
    tire_temp_fr="Tyre Temp FR",
    tire_temp_rl="Tyre Temp RL",
    tire_temp_rr="Tyre Temp RR",
    tire_pressure_fl="Tyre Press FL",
    tire_pressure_fr="Tyre Press FR",
    tire_pressure_rl="Tyre Press RL",
    tire_pressure_rr="Tyre Press RR",
    slip_angle_fl="Slip Angle FL",
    slip_angle_fr="Slip Angle FR",
    slip_angle_rl="Slip Angle RL",
    slip_angle_rr="Slip Angle RR",
    susp_travel_fl="Susp Travel FL",
    susp_travel_fr="Susp Travel FR",
    susp_travel_rl="Susp Travel RL",
    susp_travel_rr="Susp Travel RR",
    fuel="Fuel Level",
)

RF2_MAPPING = ColumnMapping(
    time="mTime",
    distance="mLapDist",
    lap="mLapNumber",
    speed="mLocalVel",  # Usually needs conversion
    rpm="mEngineRPM",
    gear="mGear",
    throttle="mUnfilteredThrottle",
    brake="mUnfilteredBrake",
    steering="mUnfilteredSteering",
    clutch="mUnfilteredClutch",
    g_lat="mLocalAccel_y",
    g_long="mLocalAccel_z",
    tire_temp_fl="mTireTemp_0",
    tire_temp_fr="mTireTemp_1",
    tire_temp_rl="mTireTemp_2",
    tire_temp_rr="mTireTemp_3",
    tire_pressure_fl="mTirePressure_0",
    tire_pressure_fr="mTirePressure_1",
    tire_pressure_rl="mTirePressure_2",
    tire_pressure_rr="mTirePressure_3",
    tire_wear_fl="mTireWear_0",
    tire_wear_fr="mTireWear_1",
    tire_wear_rl="mTireWear_2",
    tire_wear_rr="mTireWear_3",
    fuel="mFuel",
)

ACC_MAPPING = ColumnMapping(
    time="Lap Time",
    distance="Distance",
    lap="Lap",
    speed="Speed",
    rpm="RPM",
    gear="Gear",
    throttle="Gas",
    brake="Brake",
    steering="Steer Angle",
    g_lat="G Lat",
    g_long="G Lon",
    tire_temp_fl="Tyre Temp LF",
    tire_temp_fr="Tyre Temp RF",
    tire_temp_rl="Tyre Temp LR",
    tire_temp_rr="Tyre Temp RR",
    tire_pressure_fl="Tyre Press LF",
    tire_pressure_fr="Tyre Press RF",
    tire_pressure_rl="Tyre Press LR",
    tire_pressure_rr="Tyre Press RR",
)


class CSVParser:
    """
    Multi-format CSV telemetry parser.

    Automatically detects CSV format and maps columns to standardized
    telemetry data structure.
    """

    def __init__(self, format_hint: CSVFormat = CSVFormat.AUTO):
        self.format_hint = format_hint
        self.detected_format: CSVFormat | None = None
        self.column_mapping: ColumnMapping | None = None
        self.headers: list[str] = []
        self.metadata: dict[str, Any] = {}

    def parse_file(self, file_path: Path | str) -> SessionData:
        """
        Parse a CSV file and return SessionData.

        Args:
            file_path: Path to the CSV file

        Returns:
            SessionData with all parsed laps and telemetry
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        logger.info(f"Parsing CSV file: {file_path}")

        # Read and analyze file
        with open(file_path, "r", encoding="utf-8-sig") as f:
            # Try to detect format from header
            content = f.read()

        # Parse metadata and headers
        lines = content.strip().split("\n")
        self._parse_metadata(lines)

        # Detect format and create mapping
        self._detect_format_and_map()

        # Parse telemetry data
        data_points = list(self._parse_data_rows(lines))

        logger.info(f"Parsed {len(data_points)} telemetry points")

        # Group into laps
        laps = self._group_into_laps(data_points)

        # Create session
        session = SessionData(
            session_id=f"{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            session_type=self._detect_session_type(file_path.stem),
            track_name=self.metadata.get("track", "Unknown"),
            car_name=self.metadata.get("car", "Unknown"),
            driver_name=self.metadata.get("driver", "Unknown"),
            source_file=file_path,
            laps=laps,
            total_laps=len(laps),
        )

        # Calculate statistics
        self._calculate_session_stats(session)

        return session

    def _parse_metadata(self, lines: list[str]) -> None:
        """Extract metadata from file header."""
        self.metadata = {}
        data_start_line = 0

        for i, line in enumerate(lines):
            # Check for metadata patterns
            if line.startswith("#") or line.startswith(";"):
                # Comment line, might contain metadata
                match = re.match(r"[#;]\s*(\w+)\s*[:=]\s*(.+)", line)
                if match:
                    self.metadata[match.group(1).lower()] = match.group(2).strip()
                continue

            # Check for MoTeC-style metadata
            if ":" in line and "," not in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower().replace(" ", "_")
                    self.metadata[key] = parts[1].strip()
                    continue

            # This is likely the header row
            if "," in line or "\t" in line:
                # Detect delimiter
                delimiter = "\t" if "\t" in line else ","
                potential_headers = [h.strip() for h in line.split(delimiter)]

                # Check if this looks like a header (contains known column names)
                known_patterns = [
                    "time", "speed", "rpm", "throttle", "brake", "gear",
                    "distance", "lap", "g_", "tire", "tyre", "temp", "press"
                ]

                header_score = sum(
                    1 for h in potential_headers
                    if any(p in h.lower() for p in known_patterns)
                )

                if header_score >= 3 or i == 0:
                    self.headers = potential_headers
                    data_start_line = i + 1
                    break

        self.metadata["data_start_line"] = data_start_line

    def _detect_format_and_map(self) -> None:
        """Detect CSV format from headers and create column mapping."""
        if self.format_hint != CSVFormat.AUTO:
            self.detected_format = self.format_hint
        else:
            # Auto-detect from headers
            headers_lower = [h.lower() for h in self.headers]
            headers_str = " ".join(headers_lower)

            if "mtime" in headers_lower or "mlap" in headers_lower:
                self.detected_format = CSVFormat.RF2
            elif "ground speed" in headers_str or "steered angle" in headers_str:
                self.detected_format = CSVFormat.MOTEC
            elif "g lat" in headers_str and "gas" in headers_lower:
                self.detected_format = CSVFormat.ACC
            else:
                self.detected_format = CSVFormat.GENERIC

        logger.info(f"Detected format: {self.detected_format.value}")

        # Get base mapping
        if self.detected_format == CSVFormat.MOTEC:
            base_mapping = MOTEC_MAPPING
        elif self.detected_format == CSVFormat.RF2:
            base_mapping = RF2_MAPPING
        elif self.detected_format == CSVFormat.ACC:
            base_mapping = ACC_MAPPING
        else:
            base_mapping = ColumnMapping()

        # Create mapping with fuzzy matching for missing columns
        self.column_mapping = self._create_fuzzy_mapping(base_mapping)

    def _create_fuzzy_mapping(self, base: ColumnMapping) -> ColumnMapping:
        """Create column mapping with fuzzy matching for unknown columns."""
        mapping = ColumnMapping()
        headers_lower = {h.lower(): h for h in self.headers}

        # Field patterns for fuzzy matching
        patterns = {
            "time": ["time", "elapsed", "timestamp", "t_"],
            "distance": ["distance", "dist", "lap_dist", "m_dist"],
            "lap": ["lap", "lap_number", "lap_num", "mlap"],
            "speed": ["speed", "velocity", "vel", "vx", "ground_speed"],
            "rpm": ["rpm", "engine_rpm", "rev", "revs"],
            "gear": ["gear", "gear_num"],
            "throttle": ["throttle", "gas", "accel", "tps"],
            "brake": ["brake", "brk", "brake_pos"],
            "steering": ["steer", "steering", "wheel"],
            "clutch": ["clutch", "cls"],
            "g_lat": ["g_lat", "lat_g", "lateral", "acc_y", "accel_y"],
            "g_long": ["g_long", "long_g", "longitudinal", "acc_z", "accel_z"],
            "fuel": ["fuel", "fuel_level", "fuel_remaining"],
        }

        # Tire patterns
        tire_positions = [
            ("fl", ["fl", "lf", "front_left", "0"]),
            ("fr", ["fr", "rf", "front_right", "1"]),
            ("rl", ["rl", "lr", "rear_left", "2"]),
            ("rr", ["rr", "rr", "rear_right", "3"]),
        ]

        tire_metrics = [
            ("tire_temp", ["temp", "temperature"]),
            ("tire_pressure", ["press", "pressure"]),
            ("tire_wear", ["wear"]),
            ("slip_angle", ["slip_angle", "slip_ang"]),
            ("slip_ratio", ["slip_ratio", "slip_rat"]),
            ("ride_height", ["ride_height", "ride_h", "suspension_pos"]),
            ("susp_travel", ["susp_travel", "suspension_travel", "damper"]),
            ("brake_temp", ["brake_temp", "disc_temp", "rotor_temp"]),
        ]

        # Map basic fields
        for field_name, field_patterns in patterns.items():
            # First check base mapping
            base_value = getattr(base, field_name, None)
            if base_value and base_value in self.headers:
                setattr(mapping, field_name, base_value)
                continue

            # Fuzzy match
            for header in self.headers:
                header_lower = header.lower()
                if any(p in header_lower for p in field_patterns):
                    setattr(mapping, field_name, header)
                    break

        # Map tire fields
        for pos_name, pos_patterns in tire_positions:
            for metric_base, metric_patterns in tire_metrics:
                field_name = f"{metric_base}_{pos_name}"

                # Check base mapping first
                base_value = getattr(base, field_name, None)
                if base_value and base_value in self.headers:
                    setattr(mapping, field_name, base_value)
                    continue

                # Fuzzy match
                for header in self.headers:
                    header_lower = header.lower()
                    has_metric = any(m in header_lower for m in metric_patterns)
                    has_position = any(p in header_lower for p in pos_patterns)

                    if has_metric and has_position:
                        setattr(mapping, field_name, header)
                        break

        return mapping

    def _parse_data_rows(self, lines: list[str]) -> Iterator[TelemetryPoint]:
        """Parse data rows into TelemetryPoint objects."""
        data_start = self.metadata.get("data_start_line", 1)
        delimiter = "\t" if "\t" in lines[data_start] else ","

        # Create header index mapping
        header_idx = {h: i for i, h in enumerate(self.headers)}

        for line_num, line in enumerate(lines[data_start:], start=data_start):
            if not line.strip():
                continue

            try:
                values = line.split(delimiter)
                point = self._create_telemetry_point(values, header_idx)
                if point:
                    yield point
            except Exception as e:
                logger.warning(f"Error parsing line {line_num}: {e}")
                continue

    def _create_telemetry_point(
        self,
        values: list[str],
        header_idx: dict[str, int]
    ) -> TelemetryPoint | None:
        """Create a TelemetryPoint from a row of values."""
        mapping = self.column_mapping
        if not mapping:
            return None

        def get_value(field_name: str, default: float = 0.0) -> float:
            col_name = getattr(mapping, field_name, None)
            if not col_name or col_name not in header_idx:
                return default
            try:
                idx = header_idx[col_name]
                if idx < len(values):
                    val = values[idx].strip()
                    if val:
                        return float(val)
            except (ValueError, IndexError):
                pass
            return default

        def get_int_value(field_name: str, default: int = 0) -> int:
            return int(get_value(field_name, default))

        try:
            return TelemetryPoint(
                timestamp=get_value("time"),
                distance=get_value("distance"),
                lap=get_int_value("lap"),
                speed=self._convert_speed(get_value("speed")),
                rpm=get_int_value("rpm"),
                gear=get_int_value("gear"),
                throttle=get_value("throttle"),
                brake=get_value("brake"),
                steering=get_value("steering"),
                clutch=get_value("clutch"),
                g_lat=get_value("g_lat"),
                g_long=get_value("g_long"),
                tire_temp_fl=get_value("tire_temp_fl"),
                tire_temp_fr=get_value("tire_temp_fr"),
                tire_temp_rl=get_value("tire_temp_rl"),
                tire_temp_rr=get_value("tire_temp_rr"),
                tire_pressure_fl=get_value("tire_pressure_fl"),
                tire_pressure_fr=get_value("tire_pressure_fr"),
                tire_pressure_rl=get_value("tire_pressure_rl"),
                tire_pressure_rr=get_value("tire_pressure_rr"),
                tire_wear_fl=get_value("tire_wear_fl", 100.0),
                tire_wear_fr=get_value("tire_wear_fr", 100.0),
                tire_wear_rl=get_value("tire_wear_rl", 100.0),
                tire_wear_rr=get_value("tire_wear_rr", 100.0),
                slip_angle_fl=get_value("slip_angle_fl"),
                slip_angle_fr=get_value("slip_angle_fr"),
                slip_angle_rl=get_value("slip_angle_rl"),
                slip_angle_rr=get_value("slip_angle_rr"),
                slip_ratio_fl=get_value("slip_ratio_fl"),
                slip_ratio_fr=get_value("slip_ratio_fr"),
                slip_ratio_rl=get_value("slip_ratio_rl"),
                slip_ratio_rr=get_value("slip_ratio_rr"),
                ride_height_fl=get_value("ride_height_fl"),
                ride_height_fr=get_value("ride_height_fr"),
                ride_height_rl=get_value("ride_height_rl"),
                ride_height_rr=get_value("ride_height_rr"),
                susp_travel_fl=get_value("susp_travel_fl"),
                susp_travel_fr=get_value("susp_travel_fr"),
                susp_travel_rl=get_value("susp_travel_rl"),
                susp_travel_rr=get_value("susp_travel_rr"),
                fuel=get_value("fuel"),
                brake_temp_fl=get_value("brake_temp_fl"),
                brake_temp_fr=get_value("brake_temp_fr"),
                brake_temp_rl=get_value("brake_temp_rl"),
                brake_temp_rr=get_value("brake_temp_rr"),
            )
        except Exception as e:
            logger.warning(f"Error creating TelemetryPoint: {e}")
            return None

    def _convert_speed(self, value: float) -> float:
        """Convert speed to km/h if necessary."""
        if self.detected_format == CSVFormat.RF2:
            # rF2 stores velocity in m/s
            return value * 3.6
        elif self.detected_format == CSVFormat.MOTEC:
            # MoTeC might be in m/s or km/h depending on config
            if value < 100 and value > 0:  # Likely m/s
                return value * 3.6
        return value

    def _group_into_laps(self, data_points: list[TelemetryPoint]) -> list[LapData]:
        """Group telemetry points into laps."""
        if not data_points:
            return []

        laps: list[LapData] = []
        current_lap_points: list[TelemetryPoint] = []
        current_lap_num = data_points[0].lap

        for point in data_points:
            if point.lap != current_lap_num and current_lap_points:
                # New lap started, save previous
                lap = self._create_lap_data(current_lap_num, current_lap_points)
                if lap:
                    laps.append(lap)
                current_lap_points = []
                current_lap_num = point.lap

            current_lap_points.append(point)

        # Don't forget last lap
        if current_lap_points:
            lap = self._create_lap_data(current_lap_num, current_lap_points)
            if lap:
                laps.append(lap)

        return laps

    def _create_lap_data(
        self,
        lap_number: int,
        points: list[TelemetryPoint]
    ) -> LapData | None:
        """Create LapData from telemetry points."""
        if not points:
            return None

        # Calculate lap time
        lap_time = points[-1].timestamp - points[0].timestamp

        # Detect outlap/inlap
        is_outlap = lap_number == 1 or points[0].speed < 50
        is_inlap = points[-1].speed < 50 and points[-1].throttle < 10

        # Calculate stats
        speeds = [p.speed for p in points]
        max_speed = max(speeds) if speeds else 0
        avg_speed = sum(speeds) / len(speeds) if speeds else 0

        # Fuel used
        fuel_start = points[0].fuel
        fuel_end = points[-1].fuel
        fuel_used = max(0, fuel_start - fuel_end)

        # Tire temps (average over lap)
        tire_temps_fl = [p.tire_temp_fl for p in points if p.tire_temp_fl > 0]
        tire_temps_fr = [p.tire_temp_fr for p in points if p.tire_temp_fr > 0]
        tire_temps_rl = [p.tire_temp_rl for p in points if p.tire_temp_rl > 0]
        tire_temps_rr = [p.tire_temp_rr for p in points if p.tire_temp_rr > 0]

        return LapData(
            lap_number=lap_number,
            lap_time=lap_time,
            is_valid=not is_outlap and not is_inlap and lap_time > 30,
            is_outlap=is_outlap,
            is_inlap=is_inlap,
            max_speed=max_speed,
            avg_speed=avg_speed,
            fuel_used=fuel_used,
            tire_wear_fl=points[-1].tire_wear_fl,
            tire_wear_fr=points[-1].tire_wear_fr,
            tire_wear_rl=points[-1].tire_wear_rl,
            tire_wear_rr=points[-1].tire_wear_rr,
            tire_temp_fl_avg=sum(tire_temps_fl) / len(tire_temps_fl) if tire_temps_fl else 0,
            tire_temp_fr_avg=sum(tire_temps_fr) / len(tire_temps_fr) if tire_temps_fr else 0,
            tire_temp_rl_avg=sum(tire_temps_rl) / len(tire_temps_rl) if tire_temps_rl else 0,
            tire_temp_rr_avg=sum(tire_temps_rr) / len(tire_temps_rr) if tire_temps_rr else 0,
            data_points=points,
        )

    def _detect_session_type(self, filename: str) -> str:
        """Detect session type from filename."""
        filename_lower = filename.lower()
        if "qual" in filename_lower or "quali" in filename_lower:
            return "qualifying"
        elif "race" in filename_lower:
            return "race"
        elif "warm" in filename_lower:
            return "warmup"
        return "practice"

    def _calculate_session_stats(self, session: SessionData) -> None:
        """Calculate aggregate session statistics."""
        valid_laps = session.valid_laps

        if not valid_laps:
            return

        lap_times = [lap.lap_time for lap in valid_laps]
        best_time = min(lap_times)
        best_lap = next(lap for lap in valid_laps if lap.lap_time == best_time)

        session.best_lap_time = best_time
        session.best_lap_number = best_lap.lap_number
        session.total_distance = sum(
            lap.max_speed * lap.lap_time / 3600  # Rough estimate in km
            for lap in valid_laps
        )
