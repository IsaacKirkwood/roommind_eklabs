"""Short whole-house forecast using the same mode decisions as plant control."""

from __future__ import annotations

from collections import deque
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta
from math import isfinite

from ..control.thermal_model import RCModel
from .whole_house_plant_manager import (
    MODE_COOL,
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
    weather_forecast_used: bool = False


def _forecast_value(
    forecast: list[dict],
    *,
    field: str,
    current: float | None,
    now: datetime,
    minutes_ahead: float,
) -> tuple[float | None, bool]:
    """Interpolate from the current reading to upcoming hourly weather values."""
    if current is None or now.tzinfo is None:
        return current, False
    points: list[tuple[datetime, float]] = []
    for entry in forecast:
        try:
            when = datetime.fromisoformat(str(entry.get("datetime", "")).replace("Z", "+00:00"))
            value = float(entry[field])
        except (TypeError, ValueError, KeyError):
            continue
        if (
            when.tzinfo is not None
            and now < when <= now + timedelta(hours=2)
            and isfinite(value)
            and (field != "humidity" or 0.0 <= value <= 100.0)
        ):
            points.append((when, value))
    if not points:
        return current, False
    points.sort(key=lambda item: item[0])
    target = now + timedelta(minutes=minutes_ahead)
    previous_time, previous_value = now, current
    for when, value in points:
        if target <= when:
            fraction = (target - previous_time) / (when - previous_time)
            return previous_value + (value - previous_value) * fraction, True
        previous_time, previous_value = when, value
    return previous_value, True


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
    weather_forecast: list[dict],
    forecast_now: datetime,
    now: float,
    q_solar: float = 0.0,
) -> WholeHouseForecast:
    """Simulate RoomMind decisions using the available hourly weather forecast."""
    if indoor_temperature is None or outdoor_temperature is None or not idle_ready:
        return WholeHouseForecast(None, ())
    simulated = deepcopy(manager)
    temperature = indoor_temperature
    plan = initial_plan
    modes: list[str] = []
    weather_used = False
    for step in range(FORECAST_MINUTES // STEP_MINUTES):
        elapsed_minutes = step * STEP_MINUTES
        step_outdoor, temperature_forecast_used = _forecast_value(
            weather_forecast,
            field="temperature",
            current=outdoor_temperature,
            now=forecast_now,
            minutes_ahead=elapsed_minutes,
        )
        step_humidity, humidity_forecast_used = _forecast_value(
            weather_forecast,
            field="humidity",
            current=outdoor_humidity,
            now=forecast_now,
            minutes_ahead=elapsed_minutes,
        )
        midpoint_outdoor, _ = _forecast_value(
            weather_forecast,
            field="temperature",
            current=outdoor_temperature,
            now=forecast_now,
            minutes_ahead=elapsed_minutes + STEP_MINUTES / 2,
        )
        weather_used = weather_used or temperature_forecast_used or humidity_forecast_used
        assert step_outdoor is not None and midpoint_outdoor is not None
        if step:
            elapsed_hours = step * STEP_MINUTES / 60.0
            idle_prediction = model.predict(temperature, step_outdoor, 0.0, FORECAST_MINUTES, q_solar=q_solar)
            plan = simulated.evaluate(
                indoor_temperature=temperature,
                indoor_humidity=indoor_humidity,
                outdoor_temperature=step_outdoor,
                outdoor_humidity=step_humidity,
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
                return WholeHouseForecast(None, tuple(modes), weather_used)
            power = -model.Q_cool * (plan.fan_speed or 10) / 10.0
            temperature = model.predict(temperature, midpoint_outdoor, power, STEP_MINUTES, q_solar=q_solar)
        elif plan.mode == MODE_VENTILATE:
            if fresh_air_rate is None:
                return WholeHouseForecast(None, tuple(modes), weather_used)
            ventilated = deepcopy(model)
            ventilated.U += fresh_air_rate * model.C * (plan.fan_speed or 10) / 10.0
            temperature = ventilated.predict(temperature, midpoint_outdoor, 0.0, STEP_MINUTES, q_solar=q_solar)
        else:
            temperature = model.predict(temperature, midpoint_outdoor, 0.0, STEP_MINUTES, q_solar=q_solar)
    return WholeHouseForecast(
        max(indoor_temperature - 3.0, min(indoor_temperature + 3.0, temperature)),
        tuple(modes),
        weather_used,
    )
