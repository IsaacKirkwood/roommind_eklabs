"""Short whole-house forecast using the same mode decisions as plant control."""

from __future__ import annotations

from collections import deque
from copy import deepcopy
from dataclasses import dataclass
from math import isfinite

from ..control.thermal_model import RCModel
from .whole_house_plant_manager import (
    MODE_COOL,
    MODE_OFF,
    MODE_VENTILATE,
    WholeHousePlantManager,
    WholeHousePlantPlan,
)

FORECAST_MINUTES = 30
STEP_MINUTES = 5


class FreshAirEffect:
    """Learn additional outdoor-air exchange from sustained fan-only operation."""

    def __init__(self) -> None:
        self._samples: deque[tuple[float, float, float, int]] = deque(maxlen=12)
        self._rates: deque[float] = deque(maxlen=8)

    @property
    def rate(self) -> float | None:
        """Estimated additional exchange rate at full fan speed, per hour."""
        return sum(self._rates) / len(self._rates) if len(self._rates) >= 3 else None

    def observe(
        self,
        *,
        timestamp: float,
        indoor: float | None,
        outdoor: float | None,
        fan_speed: int | None,
        mode: str,
        model: RCModel,
        q_solar: float = 0.0,
    ) -> None:
        if (
            mode != MODE_VENTILATE or indoor is None or outdoor is None
            or fan_speed is None or not 1 <= fan_speed <= 10 or outdoor >= indoor - 1.0
        ):
            self._samples.clear()
            return
        self._samples.append((timestamp, indoor, outdoor, fan_speed))
        if len(self._samples) < 5:
            return
        start = self._samples[-5]
        minutes = (timestamp - start[0]) / 60.0
        if not 10 <= minutes <= 25:
            return
        if any(abs(sample[2] - outdoor) > 2.0 for sample in list(self._samples)[-5:]):
            return
        fan_fraction = sum(sample[3] for sample in list(self._samples)[-5:]) / 50.0
        outdoor_mean = sum(sample[2] for sample in list(self._samples)[-5:]) / 5.0
        gap = start[1] - outdoor_mean
        if gap < 1.0:
            return
        idle_end = model.predict(start[1], outdoor_mean, 0.0, minutes, q_solar=q_solar)
        rate = (idle_end - indoor) / ((minutes / 60.0) * gap * fan_fraction)
        if isfinite(rate) and 0 <= rate <= 3.0:
            self._rates.append(rate)


@dataclass(frozen=True)
class WholeHouseForecast:
    temperature: float | None
    modes: tuple[str, ...]


def predict_whole_house_operation(
    *,
    manager: WholeHousePlantManager,
    initial_plan: WholeHousePlantPlan,
    model: RCModel,
    fresh_air_rate: float | None,
    idle_ready: bool,
    cooling_ready: bool,
    indoor_temperature: float | None,
    indoor_humidity: float | None,
    outdoor_temperature: float | None,
    outdoor_humidity: float | None,
    home_occupied: bool,
    area_occupied: bool,
    heating_active: bool,
    exhaust_ready: bool,
    outdoor_air_safe: bool,
    ventilation_requested: bool,
    forecast_high_temperature: float | None,
    forecast_peak_hours_away: float | None,
    now: float,
    q_solar: float = 0.0,
) -> WholeHouseForecast:
    """Simulate thirty minutes of RoomMind decisions at fixed outdoor conditions."""
    if indoor_temperature is None or outdoor_temperature is None or not idle_ready:
        return WholeHouseForecast(None, ())
    simulated = deepcopy(manager)
    temperature = indoor_temperature
    plan = initial_plan
    modes: list[str] = []
    for step in range(FORECAST_MINUTES // STEP_MINUTES):
        if step:
            elapsed_hours = step * STEP_MINUTES / 60.0
            idle_prediction = model.predict(temperature, outdoor_temperature, 0.0, FORECAST_MINUTES, q_solar=q_solar)
            plan = simulated.evaluate(
                indoor_temperature=temperature,
                indoor_humidity=indoor_humidity,
                outdoor_temperature=outdoor_temperature,
                outdoor_humidity=outdoor_humidity,
                home_occupied=home_occupied,
                area_occupied=area_occupied,
                heating_active=heating_active,
                exhaust_ready=exhaust_ready,
                outdoor_air_safe=outdoor_air_safe,
                ventilation_requested=ventilation_requested,
                reported_mode=simulated.state.commanded_mode,
                feedback_available=True,
                feedback_age_seconds=0.0,
                predicted_temperature=idle_prediction,
                mpc_cooling_active=cooling_ready,
                forecast_high_temperature=forecast_high_temperature,
                forecast_peak_hours_away=(
                    max(0.0, forecast_peak_hours_away - elapsed_hours)
                    if forecast_peak_hours_away is not None else None
                ),
                now=now + step * STEP_MINUTES * 60,
            )
        modes.append(plan.mode)
        if plan.mode == MODE_COOL:
            if not cooling_ready:
                return WholeHouseForecast(None, tuple(modes))
            power = -model.Q_cool * (plan.fan_speed or 10) / 10.0
            temperature = model.predict(temperature, outdoor_temperature, power, STEP_MINUTES, q_solar=q_solar)
        elif plan.mode == MODE_VENTILATE:
            if fresh_air_rate is None:
                return WholeHouseForecast(None, tuple(modes))
            ventilated = deepcopy(model)
            ventilated.U += fresh_air_rate * model.C * (plan.fan_speed or 10) / 10.0
            temperature = ventilated.predict(temperature, outdoor_temperature, 0.0, STEP_MINUTES, q_solar=q_solar)
        else:
            temperature = model.predict(temperature, outdoor_temperature, 0.0, STEP_MINUTES, q_solar=q_solar)
    return WholeHouseForecast(max(indoor_temperature - 3.0, min(indoor_temperature + 3.0, temperature)), tuple(modes))
