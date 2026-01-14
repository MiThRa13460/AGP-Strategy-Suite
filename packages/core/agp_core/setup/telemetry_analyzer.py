"""
Telemetry Analyzer - Statistical analysis of telemetry data.

Performs corner detection, behavior analysis, and performance metrics
calculation from raw telemetry data.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import math
import logging

from agp_core.setup.telemetry_models import (
    TelemetryPoint,
    LapData,
    SessionData,
    CornerAnalysis,
    CornerType,
    CornerDirection,
    CornerPhase,
    BehaviorStatistics,
)

logger = logging.getLogger(__name__)


@dataclass
class CornerDefinition:
    """Definition of a corner on the track."""
    corner_id: int
    name: str
    start_distance: float
    apex_distance: float
    end_distance: float
    direction: CornerDirection
    corner_type: CornerType


class TelemetryAnalyzer:
    """
    Analyzes telemetry data to extract behavior patterns and performance metrics.

    This analyzer performs:
    1. Corner detection and classification
    2. Understeer/oversteer detection
    3. Traction analysis
    4. Braking efficiency analysis
    5. Statistical behavior profiling
    """

    # Thresholds for detection
    UNDERSTEER_SLIP_THRESHOLD = 8.0      # Degrees - front slip > rear slip
    OVERSTEER_SLIP_THRESHOLD = 8.0       # Degrees - rear slip > front slip
    TRACTION_SLIP_RATIO_THRESHOLD = 0.15  # Wheel slip ratio for traction loss
    BRAKE_LOCK_THRESHOLD = -0.20         # Slip ratio for lock detection

    # Corner detection thresholds
    CORNER_STEERING_THRESHOLD = 15.0     # Degrees
    CORNER_LATERAL_G_THRESHOLD = 0.3     # G
    MIN_CORNER_DURATION = 0.5            # Seconds

    # Speed classifications (km/h)
    SLOW_CORNER_SPEED = 80
    MEDIUM_CORNER_SPEED = 140
    FAST_CORNER_SPEED = 200

    def __init__(self):
        self.track_corners: list[CornerDefinition] = []

    def analyze_session(self, session: SessionData) -> BehaviorStatistics:
        """
        Analyze complete session and return behavior statistics.

        Args:
            session: Complete session data with laps

        Returns:
            BehaviorStatistics with aggregated analysis
        """
        logger.info(f"Analyzing session: {session.session_id}")

        # First, detect corners if not already defined
        if not self.track_corners and session.valid_laps:
            self._detect_track_corners(session.best_valid_lap)

        # Analyze each lap
        all_corner_analyses: list[CornerAnalysis] = []

        for lap in session.valid_laps:
            # Detect phases for each point
            self._detect_corner_phases(lap)

            # Analyze corners
            corners = self._analyze_lap_corners(lap)
            lap.corners = corners
            all_corner_analyses.extend(corners)

            # Calculate lap behavior percentages
            self._calculate_lap_behavior(lap)

        # Aggregate statistics
        stats = self._calculate_behavior_statistics(session, all_corner_analyses)

        return stats

    def analyze_lap(self, lap: LapData) -> list[CornerAnalysis]:
        """Analyze a single lap and return corner analyses."""
        # Detect phases
        self._detect_corner_phases(lap)

        # Analyze corners
        corners = self._analyze_lap_corners(lap)
        lap.corners = corners

        # Calculate behavior
        self._calculate_lap_behavior(lap)

        return corners

    def _detect_track_corners(self, reference_lap: LapData | None) -> None:
        """Detect corners from a reference lap."""
        if not reference_lap or not reference_lap.data_points:
            return

        corners: list[CornerDefinition] = []
        in_corner = False
        corner_start_idx = 0
        corner_id = 1

        points = reference_lap.data_points

        for i, point in enumerate(points):
            is_turning = (
                abs(point.steering) > self.CORNER_STEERING_THRESHOLD or
                abs(point.g_lat) > self.CORNER_LATERAL_G_THRESHOLD
            )

            if is_turning and not in_corner:
                # Corner entry
                in_corner = True
                corner_start_idx = i

            elif not is_turning and in_corner:
                # Corner exit
                in_corner = False

                # Only count if long enough
                duration = points[i].timestamp - points[corner_start_idx].timestamp
                if duration >= self.MIN_CORNER_DURATION:
                    # Find apex (minimum speed point)
                    corner_points = points[corner_start_idx:i]
                    apex_idx = min(
                        range(len(corner_points)),
                        key=lambda x: corner_points[x].speed
                    )

                    # Determine direction
                    avg_steering = sum(p.steering for p in corner_points) / len(corner_points)
                    direction = CornerDirection.LEFT if avg_steering < 0 else CornerDirection.RIGHT

                    # Determine type
                    min_speed = corner_points[apex_idx].speed
                    corner_type = self._classify_corner_speed(min_speed)

                    corner = CornerDefinition(
                        corner_id=corner_id,
                        name=f"Turn {corner_id}",
                        start_distance=points[corner_start_idx].distance,
                        apex_distance=corner_points[apex_idx].distance,
                        end_distance=points[i].distance,
                        direction=direction,
                        corner_type=corner_type,
                    )
                    corners.append(corner)
                    corner_id += 1

        self.track_corners = corners
        logger.info(f"Detected {len(corners)} corners on track")

    def _classify_corner_speed(self, speed: float) -> CornerType:
        """Classify corner type based on minimum speed."""
        if speed < self.SLOW_CORNER_SPEED:
            return CornerType.SLOW
        elif speed < self.MEDIUM_CORNER_SPEED:
            return CornerType.MEDIUM
        elif speed < self.FAST_CORNER_SPEED:
            return CornerType.FAST
        else:
            return CornerType.VERY_FAST

    def _detect_corner_phases(self, lap: LapData) -> None:
        """Detect and assign corner phase to each telemetry point."""
        if not lap.data_points:
            return

        for i, point in enumerate(lap.data_points):
            point.corner_phase = self._determine_phase(point, lap.data_points, i)

    def _determine_phase(
        self,
        point: TelemetryPoint,
        all_points: list[TelemetryPoint],
        idx: int
    ) -> CornerPhase:
        """Determine the driving phase for a single point."""

        # Simple phase detection based on inputs and G-forces
        throttle = point.throttle
        brake = point.brake
        steering = abs(point.steering)
        g_lat = abs(point.g_lat)
        g_long = point.g_long  # Negative = braking, positive = acceleration

        # Heavy braking
        if brake > 50 and g_long < -0.5:
            return CornerPhase.BRAKE_ZONE

        # Trail braking (moderate brake with steering)
        if brake > 10 and brake <= 50 and steering > 10:
            return CornerPhase.TRAIL_BRAKE

        # Turn-in (high steering rate, transitioning)
        if steering > 20 and throttle < 30 and brake < 30:
            if idx > 0:
                prev_steering = abs(all_points[idx-1].steering)
                if steering - prev_steering > 2:  # Increasing steering
                    return CornerPhase.TURN_IN

        # Apex/Mid-corner (high lateral G, low longitudinal input)
        if g_lat > 0.8 and throttle < 50 and brake < 10:
            return CornerPhase.APEX

        # Mid-corner (moderate lateral G)
        if g_lat > 0.5 and steering > 15:
            return CornerPhase.MID_CORNER

        # Corner exit (increasing throttle with steering)
        if throttle > 30 and steering > 10 and g_long > 0:
            return CornerPhase.EXIT

        # Full acceleration
        if throttle > 80 and steering < 10:
            return CornerPhase.ACCELERATION

        # Approach (light braking or coasting before corner)
        if brake > 0 and brake < 50 and steering < 10:
            return CornerPhase.APPROACH

        return CornerPhase.APPROACH

    def _analyze_lap_corners(self, lap: LapData) -> list[CornerAnalysis]:
        """Analyze all corners in a lap."""
        if not self.track_corners or not lap.data_points:
            return []

        corners: list[CornerAnalysis] = []

        for corner_def in self.track_corners:
            # Get points for this corner
            corner_points = [
                p for p in lap.data_points
                if corner_def.start_distance <= p.distance <= corner_def.end_distance
            ]

            if not corner_points:
                continue

            analysis = self._analyze_single_corner(corner_def, corner_points)
            corners.append(analysis)

        return corners

    def _analyze_single_corner(
        self,
        corner_def: CornerDefinition,
        points: list[TelemetryPoint]
    ) -> CornerAnalysis:
        """Analyze a single corner passage."""

        # Speed analysis
        speeds = [p.speed for p in points]
        entry_speed = speeds[0] if speeds else 0
        exit_speed = speeds[-1] if speeds else 0
        min_speed = min(speeds) if speeds else 0
        apex_idx = speeds.index(min_speed) if speeds else 0
        apex_speed = points[apex_idx].speed if points else 0

        # Braking analysis
        brake_points = [p for p in points if p.brake > 10]
        brake_point_distance = brake_points[0].distance if brake_points else corner_def.start_distance
        brake_pressure_max = max(p.brake for p in points) if points else 0

        brake_duration = 0.0
        trail_brake_duration = 0.0
        if brake_points:
            brake_start = brake_points[0].timestamp
            brake_end = brake_points[-1].timestamp
            brake_duration = brake_end - brake_start

            # Trail brake = braking while steering
            trail_points = [p for p in brake_points if abs(p.steering) > 15]
            if trail_points:
                trail_brake_duration = trail_points[-1].timestamp - trail_points[0].timestamp

        # Behavior detection
        understeer_detected, understeer_severity, understeer_phase = self._detect_understeer(points)
        oversteer_detected, oversteer_severity, oversteer_phase = self._detect_oversteer(points)
        traction_loss, traction_severity = self._detect_traction_loss(points)

        # Tire temps
        front_temps = [(p.tire_temp_fl + p.tire_temp_fr) / 2 for p in points if p.tire_temp_fl > 0]
        rear_temps = [(p.tire_temp_rl + p.tire_temp_rr) / 2 for p in points if p.tire_temp_rl > 0]

        # Slip angles
        front_slip = [max(abs(p.slip_angle_fl), abs(p.slip_angle_fr)) for p in points]
        rear_slip = [max(abs(p.slip_angle_rl), abs(p.slip_angle_rr)) for p in points]

        # G-forces
        lat_gs = [abs(p.g_lat) for p in points]
        long_gs = [p.g_long for p in points]

        # Time through corner
        time_through = points[-1].timestamp - points[0].timestamp if points else 0

        return CornerAnalysis(
            corner_id=corner_def.corner_id,
            corner_name=corner_def.name,
            corner_type=corner_def.corner_type,
            direction=corner_def.direction,
            start_distance=corner_def.start_distance,
            apex_distance=corner_def.apex_distance,
            end_distance=corner_def.end_distance,
            entry_speed=entry_speed,
            min_speed=min_speed,
            apex_speed=apex_speed,
            exit_speed=exit_speed,
            brake_point_distance=brake_point_distance,
            brake_pressure_max=brake_pressure_max,
            brake_duration=brake_duration,
            trail_brake_duration=trail_brake_duration,
            understeer_detected=understeer_detected,
            understeer_severity=understeer_severity,
            understeer_phase=understeer_phase,
            oversteer_detected=oversteer_detected,
            oversteer_severity=oversteer_severity,
            oversteer_phase=oversteer_phase,
            traction_loss_detected=traction_loss,
            traction_loss_severity=traction_severity,
            tire_temp_front_avg=sum(front_temps) / len(front_temps) if front_temps else 0,
            tire_temp_rear_avg=sum(rear_temps) / len(rear_temps) if rear_temps else 0,
            slip_angle_front_max=max(front_slip) if front_slip else 0,
            slip_angle_rear_max=max(rear_slip) if rear_slip else 0,
            time_through_corner=time_through,
            max_lat_g=max(lat_gs) if lat_gs else 0,
            max_brake_g=abs(min(long_gs)) if long_gs else 0,
            max_accel_g=max(long_gs) if long_gs else 0,
        )

    def _detect_understeer(
        self,
        points: list[TelemetryPoint]
    ) -> tuple[bool, float, CornerPhase | None]:
        """
        Detect understeer in corner.

        Understeer indicators:
        - Front slip angle > rear slip angle
        - Increasing steering with no corresponding lateral G increase
        - Steering saturation
        """
        if not points:
            return False, 0.0, None

        understeer_count = 0
        max_severity = 0.0
        worst_phase = None

        for point in points:
            front_slip = (abs(point.slip_angle_fl) + abs(point.slip_angle_fr)) / 2
            rear_slip = (abs(point.slip_angle_rl) + abs(point.slip_angle_rr)) / 2

            slip_diff = front_slip - rear_slip

            # Understeer when front slips more than rear
            if slip_diff > self.UNDERSTEER_SLIP_THRESHOLD:
                understeer_count += 1
                severity = min(100, (slip_diff - self.UNDERSTEER_SLIP_THRESHOLD) * 10)
                if severity > max_severity:
                    max_severity = severity
                    worst_phase = point.corner_phase

        # Also check for steering saturation (high steering, low lateral G)
        for point in points:
            if abs(point.steering) > 60 and abs(point.g_lat) < 1.0:
                expected_g = abs(point.steering) / 60  # Rough expectation
                if abs(point.g_lat) < expected_g * 0.7:
                    understeer_count += 1
                    severity = (1 - abs(point.g_lat) / expected_g) * 50
                    if severity > max_severity:
                        max_severity = severity
                        worst_phase = point.corner_phase

        detected = understeer_count > len(points) * 0.1  # >10% of points
        return detected, max_severity, worst_phase

    def _detect_oversteer(
        self,
        points: list[TelemetryPoint]
    ) -> tuple[bool, float, CornerPhase | None]:
        """
        Detect oversteer in corner.

        Oversteer indicators:
        - Rear slip angle > front slip angle
        - Counter-steering (steering opposite to corner direction)
        - Rapid yaw rate changes
        """
        if not points:
            return False, 0.0, None

        oversteer_count = 0
        max_severity = 0.0
        worst_phase = None

        for i, point in enumerate(points):
            front_slip = (abs(point.slip_angle_fl) + abs(point.slip_angle_fr)) / 2
            rear_slip = (abs(point.slip_angle_rl) + abs(point.slip_angle_rr)) / 2

            slip_diff = rear_slip - front_slip

            # Oversteer when rear slips more than front
            if slip_diff > self.OVERSTEER_SLIP_THRESHOLD:
                oversteer_count += 1
                severity = min(100, (slip_diff - self.OVERSTEER_SLIP_THRESHOLD) * 10)
                if severity > max_severity:
                    max_severity = severity
                    worst_phase = point.corner_phase

        # Check for counter-steering
        for i in range(1, len(points)):
            prev = points[i-1]
            curr = points[i]

            # Sign change in steering while still cornering
            if prev.steering * curr.steering < 0 and abs(curr.g_lat) > 0.5:
                oversteer_count += 1
                severity = min(100, abs(curr.steering - prev.steering))
                if severity > max_severity:
                    max_severity = severity
                    worst_phase = curr.corner_phase

        detected = oversteer_count > len(points) * 0.05  # >5% of points
        return detected, max_severity, worst_phase

    def _detect_traction_loss(
        self,
        points: list[TelemetryPoint]
    ) -> tuple[bool, float]:
        """
        Detect traction loss (wheelspin) on corner exit.

        Indicators:
        - High slip ratio on rear wheels
        - Throttle > 50% with rear slip ratio spike
        """
        if not points:
            return False, 0.0

        traction_loss_count = 0
        max_severity = 0.0

        for point in points:
            if point.throttle > 50:
                rear_slip_ratio = max(
                    abs(point.slip_ratio_rl),
                    abs(point.slip_ratio_rr)
                )

                if rear_slip_ratio > self.TRACTION_SLIP_RATIO_THRESHOLD:
                    traction_loss_count += 1
                    severity = min(100, rear_slip_ratio * 200)
                    max_severity = max(max_severity, severity)

        detected = traction_loss_count > 3  # At least 3 samples
        return detected, max_severity

    def _calculate_lap_behavior(self, lap: LapData) -> None:
        """Calculate behavior percentages for a lap."""
        if not lap.data_points:
            return

        total_points = len(lap.data_points)
        understeer_points = 0
        oversteer_points = 0
        traction_loss_points = 0
        brake_lock_points = 0

        for point in lap.data_points:
            front_slip = (abs(point.slip_angle_fl) + abs(point.slip_angle_fr)) / 2
            rear_slip = (abs(point.slip_angle_rl) + abs(point.slip_angle_rr)) / 2

            # Understeer
            if front_slip - rear_slip > self.UNDERSTEER_SLIP_THRESHOLD:
                understeer_points += 1

            # Oversteer
            if rear_slip - front_slip > self.OVERSTEER_SLIP_THRESHOLD:
                oversteer_points += 1

            # Traction loss
            if point.throttle > 50:
                rear_slip_ratio = max(abs(point.slip_ratio_rl), abs(point.slip_ratio_rr))
                if rear_slip_ratio > self.TRACTION_SLIP_RATIO_THRESHOLD:
                    traction_loss_points += 1

            # Brake lock
            if point.brake > 30:
                front_slip_ratio = min(point.slip_ratio_fl, point.slip_ratio_fr)
                if front_slip_ratio < self.BRAKE_LOCK_THRESHOLD:
                    brake_lock_points += 1

        lap.understeer_percentage = (understeer_points / total_points) * 100
        lap.oversteer_percentage = (oversteer_points / total_points) * 100
        lap.traction_loss_percentage = (traction_loss_points / total_points) * 100
        lap.brake_lock_percentage = (brake_lock_points / total_points) * 100

    def _calculate_behavior_statistics(
        self,
        session: SessionData,
        corners: list[CornerAnalysis]
    ) -> BehaviorStatistics:
        """Calculate aggregate behavior statistics."""
        stats = BehaviorStatistics()

        if not corners:
            return stats

        # Overall tendencies
        understeer_severities = [c.understeer_severity for c in corners if c.understeer_detected]
        oversteer_severities = [c.oversteer_severity for c in corners if c.oversteer_detected]

        stats.understeer_tendency = sum(understeer_severities) / len(understeer_severities) if understeer_severities else 0
        stats.oversteer_tendency = sum(oversteer_severities) / len(oversteer_severities) if oversteer_severities else 0

        # Balance score: 0 = understeer, 50 = neutral, 100 = oversteer
        if stats.understeer_tendency + stats.oversteer_tendency > 0:
            stats.balance_score = 50 + (stats.oversteer_tendency - stats.understeer_tendency) / 2
            stats.balance_score = max(0, min(100, stats.balance_score))

        # By corner phase
        entry_corners = [c for c in corners if c.understeer_phase == CornerPhase.TURN_IN or c.oversteer_phase == CornerPhase.TURN_IN]
        mid_corners = [c for c in corners if c.understeer_phase in [CornerPhase.APEX, CornerPhase.MID_CORNER] or c.oversteer_phase in [CornerPhase.APEX, CornerPhase.MID_CORNER]]
        exit_corners = [c for c in corners if c.understeer_phase == CornerPhase.EXIT or c.oversteer_phase == CornerPhase.EXIT]

        stats.entry_balance = self._calculate_phase_balance(entry_corners)
        stats.mid_corner_balance = self._calculate_phase_balance(mid_corners)
        stats.exit_balance = self._calculate_phase_balance(exit_corners)

        # By corner type
        slow_corners = [c for c in corners if c.corner_type == CornerType.SLOW]
        medium_corners = [c for c in corners if c.corner_type == CornerType.MEDIUM]
        fast_corners = [c for c in corners if c.corner_type in [CornerType.FAST, CornerType.VERY_FAST]]

        stats.slow_corner_balance = self._calculate_type_balance(slow_corners)
        stats.medium_corner_balance = self._calculate_type_balance(medium_corners)
        stats.fast_corner_balance = self._calculate_type_balance(fast_corners)

        # Traction
        traction_severities = [c.traction_loss_severity for c in corners if c.traction_loss_detected]
        stats.traction_on_throttle = sum(traction_severities) / len(traction_severities) if traction_severities else 0

        # Tire stress
        front_temps = [c.tire_temp_front_avg for c in corners if c.tire_temp_front_avg > 0]
        rear_temps = [c.tire_temp_rear_avg for c in corners if c.tire_temp_rear_avg > 0]

        if front_temps and rear_temps:
            avg_front = sum(front_temps) / len(front_temps)
            avg_rear = sum(rear_temps) / len(rear_temps)
            # Higher temp = more stress. Normalize to 0-100
            stats.front_tire_stress = min(100, max(0, (avg_front - 70) * 2))
            stats.rear_tire_stress = min(100, max(0, (avg_rear - 70) * 2))
            stats.tire_balance = 50 + (stats.rear_tire_stress - stats.front_tire_stress) / 2

        # Consistency
        if session.valid_laps:
            lap_times = [lap.lap_time for lap in session.valid_laps]
            if len(lap_times) > 1:
                mean_time = sum(lap_times) / len(lap_times)
                variance = sum((t - mean_time) ** 2 for t in lap_times) / len(lap_times)
                std_dev = math.sqrt(variance)
                # Lower std dev = more consistent
                stats.consistency = max(0, 100 - std_dev * 10)

        stats.sample_size = len(corners)

        return stats

    def _calculate_phase_balance(self, corners: list[CornerAnalysis]) -> float:
        """Calculate balance for a corner phase."""
        if not corners:
            return 50.0

        understeer_sum = sum(c.understeer_severity for c in corners)
        oversteer_sum = sum(c.oversteer_severity for c in corners)

        if understeer_sum + oversteer_sum == 0:
            return 50.0

        return 50 + (oversteer_sum - understeer_sum) / (len(corners) * 2)

    def _calculate_type_balance(self, corners: list[CornerAnalysis]) -> float:
        """Calculate balance for a corner type."""
        return self._calculate_phase_balance(corners)
