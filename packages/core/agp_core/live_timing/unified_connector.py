"""Unified live timing connector for multiple data sources"""

from __future__ import annotations
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Callable
from enum import Enum

from agp_core.live_timing.models import (
    Driver,
    Standing,
    SessionInfo,
    GapAnalysis,
    ThreatLevel,
    LapTime,
    SessionType,
    PitStatus,
)

logger = logging.getLogger(__name__)


class DataSource(Enum):
    """Available data sources for live timing."""
    SHARED_MEMORY = "shared_memory"
    RF2_HTTP = "rf2_http"
    SMS = "sms"  # SimHub Message Service


@dataclass
class LiveTimingState:
    """Current state of live timing data."""
    session: SessionInfo | None = None
    standings: list[Standing] = field(default_factory=list)
    drivers: dict[str, Driver] = field(default_factory=dict)
    player_id: str | None = None
    last_update: float = 0.0


class UnifiedLiveTimingConnector:
    """
    Unified connector that aggregates live timing data from multiple sources.

    Priority order:
    1. Shared Memory (most accurate, lowest latency)
    2. rF2 HTTP API (good for remote monitoring)
    3. SMS/SimHub (fallback)
    """

    def __init__(self):
        self.state = LiveTimingState()
        self.sources: dict[DataSource, bool] = {
            DataSource.SHARED_MEMORY: False,
            DataSource.RF2_HTTP: False,
            DataSource.SMS: False,
        }
        self.callbacks: list[Callable[[LiveTimingState], None]] = []
        self._running = False
        self._lap_history: dict[str, list[float]] = {}  # driver_id -> lap times

    def register_callback(self, callback: Callable[[LiveTimingState], None]) -> None:
        """Register a callback for state updates."""
        self.callbacks.append(callback)

    def _notify_callbacks(self) -> None:
        """Notify all registered callbacks of state change."""
        for callback in self.callbacks:
            try:
                callback(self.state)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    def update_from_shared_memory(self, data: dict[str, Any]) -> None:
        """Update state from shared memory telemetry data."""
        if not data:
            return

        self.sources[DataSource.SHARED_MEMORY] = True

        # Update session info
        if "session" in data:
            session_data = data["session"]
            self.state.session = SessionInfo(
                session_type=self._parse_session_type(session_data.get("session_type", 0)),
                track_name=data.get("track", "Unknown"),
                air_temp=session_data.get("ambient_temp", 20),
                track_temp=session_data.get("track_temp", 25),
                rain=session_data.get("rain", 0),
            )

        # Update player data
        if "player_id" in data:
            self.state.player_id = data["player_id"]

        # Update standings from scoring data
        if "scoring" in data:
            self._update_standings_from_scoring(data["scoring"])

        self._calculate_threats()
        self._notify_callbacks()

    def update_from_http_api(self, data: dict[str, Any]) -> None:
        """Update state from rF2 HTTP API response."""
        if not data:
            return

        self.sources[DataSource.RF2_HTTP] = True

        # Parse standings
        if "standings" in data:
            standings = []
            for entry in data["standings"]:
                driver = self._get_or_create_driver(entry.get("driverId", ""))
                driver.name = entry.get("driverName", "Unknown")
                driver.car_number = entry.get("carNumber", "")
                driver.car_class = entry.get("carClass", "")
                driver.position = entry.get("position", 0)
                driver.laps_completed = entry.get("lapsCompleted", 0)

                if entry.get("bestLapTime"):
                    driver.best_lap = LapTime(total=entry["bestLapTime"])
                if entry.get("lastLapTime"):
                    driver.last_lap = LapTime(total=entry["lastLapTime"])

                standing = Standing(
                    position=driver.position,
                    driver=driver,
                    gap_to_leader=entry.get("gapToLeader", 0),
                    gap_to_ahead=entry.get("gapToAhead", 0),
                    interval=entry.get("interval", 0),
                    last_lap=driver.last_lap,
                    best_lap=driver.best_lap,
                    laps=driver.laps_completed,
                    pit_stops=entry.get("pitStops", 0),
                )
                standings.append(standing)

            self.state.standings = sorted(standings, key=lambda s: s.position)

        self._calculate_threats()
        self._notify_callbacks()

    def update_from_sms(self, data: dict[str, Any]) -> None:
        """Update state from SimHub Message Service."""
        if not data:
            return

        self.sources[DataSource.SMS] = True

        # SMS typically provides simpler data
        if "drivers" in data:
            for driver_data in data["drivers"]:
                driver = self._get_or_create_driver(driver_data.get("id", ""))
                driver.name = driver_data.get("name", "Unknown")
                driver.position = driver_data.get("position", 0)
                driver.gap_to_leader = driver_data.get("gap", 0)

        self._notify_callbacks()

    def _get_or_create_driver(self, driver_id: str) -> Driver:
        """Get existing driver or create new one."""
        if driver_id not in self.state.drivers:
            self.state.drivers[driver_id] = Driver(id=driver_id, name="Unknown")
        return self.state.drivers[driver_id]

    def _update_standings_from_scoring(self, scoring_data: list[dict]) -> None:
        """Update standings from shared memory scoring data."""
        standings = []

        for entry in scoring_data:
            driver_id = entry.get("driver_id", str(entry.get("slot", 0)))
            driver = self._get_or_create_driver(driver_id)

            driver.name = entry.get("driver_name", "Unknown")
            driver.car_number = str(entry.get("car_number", ""))
            driver.car_class = entry.get("car_class", "")
            driver.car_name = entry.get("vehicle_name", "")
            driver.position = entry.get("place", 0)
            driver.class_position = entry.get("class_place", 0)
            driver.laps_completed = entry.get("total_laps", 0)
            driver.is_player = entry.get("is_player", False)
            driver.in_pit = entry.get("in_pits", False)
            driver.pit_stops = entry.get("num_pitstops", 0)

            if driver.is_player:
                self.state.player_id = driver_id

            # Pit status
            if entry.get("in_garage", False):
                driver.pit_status = PitStatus.IN_GARAGE
            elif driver.in_pit:
                driver.pit_status = PitStatus.IN_PIT_LANE
            else:
                driver.pit_status = PitStatus.ON_TRACK

            # Lap times
            best_time = entry.get("best_lap_time", 0)
            last_time = entry.get("last_lap_time", 0)

            if best_time > 0:
                driver.best_lap = LapTime(
                    total=best_time,
                    sector1=entry.get("best_sector1", None),
                    sector2=entry.get("best_sector2", None),
                    sector3=entry.get("best_sector3", None),
                )

            if last_time > 0:
                driver.last_lap = LapTime(
                    total=last_time,
                    sector1=entry.get("last_sector1", None),
                    sector2=entry.get("last_sector2", None),
                    sector3=entry.get("last_sector3", None),
                )
                # Track lap history for pace analysis
                if driver_id not in self._lap_history:
                    self._lap_history[driver_id] = []
                if len(self._lap_history[driver_id]) == 0 or self._lap_history[driver_id][-1] != last_time:
                    self._lap_history[driver_id].append(last_time)
                    # Keep last 10 laps
                    self._lap_history[driver_id] = self._lap_history[driver_id][-10:]

            # Gaps
            driver.gap_to_leader = entry.get("time_behind_leader", 0)
            driver.gap_to_ahead = entry.get("time_behind_next", 0)

            standing = Standing(
                position=driver.position,
                driver=driver,
                gap_to_leader=driver.gap_to_leader,
                gap_to_ahead=driver.gap_to_ahead,
                interval=driver.gap_to_ahead,
                last_lap=driver.last_lap,
                best_lap=driver.best_lap,
                laps=driver.laps_completed,
                pit_stops=driver.pit_stops,
                status="pit" if driver.in_pit else "running",
            )
            standings.append(standing)

        self.state.standings = sorted(standings, key=lambda s: s.position)

    def _calculate_threats(self) -> None:
        """Calculate threat levels for all drivers relative to player."""
        if not self.state.player_id:
            return

        player = self.state.drivers.get(self.state.player_id)
        if not player:
            return

        player_pace = self._get_average_pace(self.state.player_id)

        for driver_id, driver in self.state.drivers.items():
            if driver_id == self.state.player_id:
                driver.threat_level = ThreatLevel.NONE
                continue

            # Calculate gap to player
            if driver.position < player.position:
                # Driver is ahead
                driver.gap_to_player = -driver.gap_to_leader + player.gap_to_leader
            else:
                # Driver is behind
                driver.gap_to_player = driver.gap_to_leader - player.gap_to_leader

            # Calculate pace delta
            driver_pace = self._get_average_pace(driver_id)
            if player_pace > 0 and driver_pace > 0:
                driver.pace_delta = driver_pace - player_pace  # negative = faster
            else:
                driver.pace_delta = 0

            # Determine threat level
            driver.threat_level = self._assess_threat(driver, player)

    def _get_average_pace(self, driver_id: str) -> float:
        """Get average lap time for a driver (last 5 laps)."""
        if driver_id not in self._lap_history:
            return 0
        laps = self._lap_history[driver_id][-5:]
        if not laps:
            return 0
        return sum(laps) / len(laps)

    def _assess_threat(self, driver: Driver, player: Driver) -> ThreatLevel:
        """Assess the threat level of a driver."""
        # Driver is behind player
        if driver.position > player.position:
            gap = abs(driver.gap_to_player)

            # Closing fast
            if driver.pace_delta < -0.5:  # More than 0.5s/lap faster
                if gap < 5:
                    return ThreatLevel.CRITICAL
                elif gap < 15:
                    return ThreatLevel.HIGH
                elif gap < 30:
                    return ThreatLevel.MEDIUM
                else:
                    return ThreatLevel.LOW

            # Similar pace
            elif abs(driver.pace_delta) < 0.3:
                if gap < 3:
                    return ThreatLevel.HIGH
                elif gap < 10:
                    return ThreatLevel.MEDIUM
                else:
                    return ThreatLevel.LOW

            # Slower
            else:
                return ThreatLevel.NONE

        # Driver is ahead of player
        else:
            gap = abs(driver.gap_to_player)

            # Player is catching
            if driver.pace_delta > 0.3:  # Driver is slower
                if gap < 5:
                    return ThreatLevel.LOW  # Opportunity to overtake
                else:
                    return ThreatLevel.NONE
            else:
                return ThreatLevel.NONE

    def _parse_session_type(self, session_type: int) -> SessionType:
        """Parse session type from numeric value."""
        mapping = {
            0: SessionType.PRACTICE,
            1: SessionType.PRACTICE,
            2: SessionType.PRACTICE,
            5: SessionType.QUALIFYING,
            6: SessionType.WARMUP,
            7: SessionType.RACE,
        }
        return mapping.get(session_type, SessionType.PRACTICE)

    def get_standings_by_class(self, car_class: str | None = None) -> list[Standing]:
        """Get standings filtered by car class."""
        if car_class is None:
            return self.state.standings

        return [s for s in self.state.standings if s.driver.car_class == car_class]

    def get_classes(self) -> list[str]:
        """Get list of unique car classes."""
        classes = set()
        for driver in self.state.drivers.values():
            if driver.car_class:
                classes.add(driver.car_class)
        return sorted(list(classes))

    def get_gap_analysis(self, driver_id: str, target_id: str) -> GapAnalysis | None:
        """Get detailed gap analysis between two drivers."""
        driver = self.state.drivers.get(driver_id)
        target = self.state.drivers.get(target_id)

        if not driver or not target:
            return None

        # Calculate current gap
        current_gap = abs(driver.gap_to_leader - target.gap_to_leader)

        # Calculate pace difference
        driver_pace = self._get_average_pace(driver_id)
        target_pace = self._get_average_pace(target_id)

        pace_diff = 0
        if driver_pace > 0 and target_pace > 0:
            pace_diff = target_pace - driver_pace  # positive = driver is faster

        # Project catch lap
        catch_lap = None
        if pace_diff > 0.1 and current_gap > 0:  # Driver is faster
            laps_to_catch = current_gap / pace_diff
            catch_lap = driver.laps_completed + int(laps_to_catch)

        return GapAnalysis(
            driver_id=driver_id,
            target_id=target_id,
            current_gap=current_gap,
            gap_trend=-pace_diff,  # negative trend = closing
            projected_catch_lap=catch_lap,
            pace_difference=pace_diff,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert current state to dictionary for serialization."""
        return {
            "session": self.state.session.to_dict() if self.state.session else None,
            "standings": [s.to_dict() for s in self.state.standings],
            "player_id": self.state.player_id,
            "classes": self.get_classes(),
            "sources": {k.value: v for k, v in self.sources.items()},
        }
