"""SVM (Setup Vehicle Mod) file parser for rFactor 2"""

from __future__ import annotations
import configparser
from pathlib import Path
from typing import Any

from agp_core.setup.entities.setup import (
    Setup,
    SuspensionSetup,
    CornerSetup,
    CornerPosition,
    DifferentialSetup,
    AeroSetup,
    BrakeSetup,
)
from agp_core.setup.value_objects import (
    Angle,
    Distance,
    Pressure,
    Rate,
    Percentage,
)


class SVMParser:
    """Parser for rFactor 2 .svm setup files."""

    # Default value mappings (index to actual value)
    # These are approximations - actual values depend on the car's HDV file
    CAMBER_BASE = 0.0
    CAMBER_STEP = -0.1  # degrees per index
    PRESSURE_BASE = 140.0  # kPa
    PRESSURE_STEP = 5.0  # kPa per index
    SPRING_BASE = 50000  # N/m
    SPRING_STEP = 5000  # N/m per index
    RIDE_HEIGHT_BASE = 20  # mm
    RIDE_HEIGHT_STEP = 2  # mm per index

    def parse(self, file_path: Path) -> Setup:
        """Parse an SVM file and return a Setup entity."""
        if not file_path.exists():
            raise FileNotFoundError(f"Setup file not found: {file_path}")

        content = file_path.read_text(encoding='utf-8', errors='ignore')

        # Parse as INI-style file
        config = configparser.ConfigParser()
        config.read_string(self._preprocess_content(content))

        setup = Setup(
            name=file_path.stem,
            source_path=file_path,
        )

        # Parse general section
        if config.has_section('GENERAL'):
            setup.tire_compound = self._get_tire_compound(config)
            setup.fuel_load = self._safe_get_float(config, 'GENERAL', 'FuelSetting', 0)

        # Parse suspension
        setup.suspension = self._parse_suspension(config)

        # Parse differential
        setup.differential = self._parse_differential(config)

        # Parse aero
        setup.aero = self._parse_aero(config)

        # Parse brakes
        setup.brakes = self._parse_brakes(config)

        return setup

    def _preprocess_content(self, content: str) -> str:
        """Preprocess SVM content for configparser."""
        lines = []
        for line in content.split('\n'):
            # Remove comments
            if '//' in line:
                line = line.split('//')[0]
            # Clean up the line
            line = line.strip()
            if line:
                lines.append(line)
        return '\n'.join(lines)

    def _safe_get_int(
        self, config: configparser.ConfigParser, section: str, key: str, default: int = 0
    ) -> int:
        """Safely get an integer value."""
        try:
            if config.has_option(section, key):
                value = config.get(section, key)
                # Handle values like "0//comment"
                value = value.split('//')[0].strip()
                return int(value)
        except (ValueError, configparser.Error):
            pass
        return default

    def _safe_get_float(
        self, config: configparser.ConfigParser, section: str, key: str, default: float = 0.0
    ) -> float:
        """Safely get a float value."""
        try:
            if config.has_option(section, key):
                value = config.get(section, key)
                value = value.split('//')[0].strip()
                return float(value)
        except (ValueError, configparser.Error):
            pass
        return default

    def _get_tire_compound(self, config: configparser.ConfigParser) -> str:
        """Get tire compound from settings."""
        front = self._safe_get_int(config, 'GENERAL', 'FrontTireCompoundSetting', 1)
        compounds = ["Soft", "Medium", "Hard", "Wet", "Intermediate"]
        if 0 <= front < len(compounds):
            return compounds[front]
        return "Medium"

    def _parse_corner(
        self, config: configparser.ConfigParser, section: str, position: CornerPosition
    ) -> CornerSetup:
        """Parse corner-specific settings."""
        camber_idx = self._safe_get_int(config, section, 'CamberSetting', 15)
        pressure_idx = self._safe_get_int(config, section, 'PressureSetting', 5)
        spring_idx = self._safe_get_int(config, section, 'SpringSetting', 5)
        rh_idx = self._safe_get_int(config, section, 'RideHeightSetting', 10)

        return CornerSetup(
            position=position,
            camber=Angle.from_degrees(self.CAMBER_BASE + camber_idx * self.CAMBER_STEP),
            pressure=Pressure.from_kpa(self.PRESSURE_BASE + pressure_idx * self.PRESSURE_STEP),
            spring_rate=Rate.from_nm(self.SPRING_BASE + spring_idx * self.SPRING_STEP),
            ride_height=Distance.from_mm(self.RIDE_HEIGHT_BASE + rh_idx * self.RIDE_HEIGHT_STEP),
            slow_bump=self._safe_get_int(config, section, 'SlowBumpSetting', 10),
            fast_bump=self._safe_get_int(config, section, 'FastBumpSetting', 10),
            slow_rebound=self._safe_get_int(config, section, 'SlowReboundSetting', 10),
            fast_rebound=self._safe_get_int(config, section, 'FastReboundSetting', 10),
        )

    def _parse_suspension(self, config: configparser.ConfigParser) -> SuspensionSetup | None:
        """Parse suspension settings."""
        try:
            front_left = self._parse_corner(config, 'FRONTLEFT', CornerPosition.FRONT_LEFT)
            front_right = self._parse_corner(config, 'FRONTRIGHT', CornerPosition.FRONT_RIGHT)
            rear_left = self._parse_corner(config, 'REARLEFT', CornerPosition.REAR_LEFT)
            rear_right = self._parse_corner(config, 'REARRIGHT', CornerPosition.REAR_RIGHT)

            front_arb = self._safe_get_int(config, 'FRONT', 'FrontAntiSwaySetting', 5)
            rear_arb = self._safe_get_int(config, 'REAR', 'RearAntiSwaySetting', 5)

            front_toe_idx = self._safe_get_int(config, 'FRONT', 'FrontToeInSetting', 20)
            rear_toe_idx = self._safe_get_int(config, 'REAR', 'RearToeInSetting', 20)

            return SuspensionSetup(
                front_left=front_left,
                front_right=front_right,
                rear_left=rear_left,
                rear_right=rear_right,
                front_arb=front_arb,
                rear_arb=rear_arb,
                front_toe=Angle.from_degrees((front_toe_idx - 20) * 0.05),
                rear_toe=Angle.from_degrees((rear_toe_idx - 20) * 0.05),
            )
        except Exception:
            return None

    def _parse_differential(self, config: configparser.ConfigParser) -> DifferentialSetup | None:
        """Parse differential settings."""
        try:
            if not config.has_section('REAR'):
                return None

            power_idx = self._safe_get_int(config, 'REAR', 'RearSplitSetting', 5)
            coast_idx = self._safe_get_int(config, 'REAR', 'RearSplitSetting', 5)

            return DifferentialSetup(
                power_lock=Percentage.from_value(20 + power_idx * 10),
                coast_lock=Percentage.from_value(20 + coast_idx * 8),
                preload=50.0,
            )
        except Exception:
            return None

    def _parse_aero(self, config: configparser.ConfigParser) -> AeroSetup | None:
        """Parse aerodynamic settings."""
        try:
            front_wing = 0
            rear_wing = 0

            if config.has_section('FRONT'):
                front_wing = self._safe_get_int(config, 'FRONT', 'FrontWingSetting', 10)

            if config.has_section('REAR'):
                rear_wing = self._safe_get_int(config, 'REAR', 'RearWingSetting', 15)

            return AeroSetup(
                front_wing=front_wing,
                rear_wing=rear_wing,
            )
        except Exception:
            return None

    def _parse_brakes(self, config: configparser.ConfigParser) -> BrakeSetup | None:
        """Parse brake settings."""
        try:
            bias_idx = self._safe_get_int(config, 'GENERAL', 'BrakeBiasSetting', 10)
            pressure_idx = self._safe_get_int(config, 'GENERAL', 'BrakePressureSetting', 10)

            return BrakeSetup(
                bias=Percentage.from_value(50 + bias_idx * 1.0),
                pressure=Percentage.from_value(80 + pressure_idx * 2.0),
            )
        except Exception:
            return None

    def write(self, setup: Setup, file_path: Path) -> None:
        """Write a Setup entity back to an SVM file."""
        raise NotImplementedError("SVM writing not yet implemented")
