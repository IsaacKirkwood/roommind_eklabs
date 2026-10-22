"""The card forecast must follow real whole-house mode transitions."""

from datetime import datetime, timedelta, timezone

from custom_components.roommind_eklabs.control.thermal_model import RCModel
from custom_components.roommind_eklabs.managers.whole_house_forecast import (
    FreshAirEffect,
    _forecast_value,
    predict_whole_house_operation,
)
from custom_components.roommind_eklabs.managers.whole_house_plant_manager import (
    MODE_COOL,
    MODE_VENTILATE,
    WholeHousePlantConfig,
    WholeHousePlantManager,
    WholeHousePlantPlan,
)


def _forecast(fresh_air_rate: float | None):
    manager = WholeHousePlantManager(WholeHousePlantConfig(
        entity_id="climate.cooler",
        cooling_target=23.0,
        fresh_air_max_outdoor_temperature=28.0,
        minimum_outdoor_cooling_temp=18.0,
        maximum_cooling_run_minutes=10,
        cooling_rest_minutes=20,
        minimum_cooling_run_minutes=0,
        minimum_ventilation_run_minutes=0,
        require_home_presence=False,
        require_occupancy=False,
    ))
    manager.state.commanded_mode = MODE_COOL
    manager.state.mode_since = 0.0
    plan = WholeHousePlantPlan(MODE_COOL, False, "cooling", None, True, True, True, 10, False)
    return predict_whole_house_operation(
        manager=manager,
        initial_plan=plan,
        model=RCModel(C=1.0, U=0.1, Q_cool=2.0),
        fresh_air_rate=fresh_air_rate,
        idle_ready=True,
        cooling_ready=True,
        indoor_temperature=26.0,
        indoor_humidity=40.0,
        outdoor_temperature=20.0,
        outdoor_humidity=40.0,
        home_occupied=True,
        area_occupied=True,
        heating_active=False,
        exhaust_ready=True,
        outdoor_air_safe=True,
        ventilation_requested=False,
        forecast_high_temperature=None,
        forecast_peak_hours_away=None,
        weather_forecast=[],
        forecast_now=datetime(2026, 10, 22, tzinfo=timezone.utc),
        now=9 * 60.0,
    ), manager


def test_forecast_follows_cooling_run_limit_into_fresh_air():
    result, manager = _forecast(0.5)
    assert result.temperature is not None
    assert result.temperature < 26.0
    assert result.modes[0] == MODE_COOL
    assert MODE_VENTILATE in result.modes[1:]
    assert manager.state.commanded_mode == MODE_COOL  # Simulation must not alter control.


def test_forecast_waits_for_fresh_air_learning():
    result, _ = _forecast(None)
    assert result.temperature is None
    assert MODE_VENTILATE in result.modes


def test_fresh_air_effect_requires_sustained_observations():
    effect = FreshAirEffect()
    model = RCModel(C=1.0, U=0.1)
    for index in range(9):
        effect.observe(
            timestamp=index * 180.0,
            indoor=26.0 - index * 0.08,
            outdoor=20.0,
            fan_speed=8,
            mode=MODE_VENTILATE,
            model=model,
        )
    assert effect.rate is not None
    assert effect.rate > 0.0


def test_fresh_air_effect_learns_at_normal_thirty_second_update_rate():
    effect = FreshAirEffect()
    model = RCModel(C=1.0, U=0.1)
    for index in range(24):
        effect.observe(
            timestamp=index * 30.0,
            indoor=26.0 - index * 0.02,
            outdoor=20.0,
            fan_speed=8,
            mode=MODE_VENTILATE,
            model=model,
        )
    assert effect.rate is None  # Less than the required 12-minute window.
    for index in range(24, 37):
        effect.observe(
            timestamp=index * 30.0,
            indoor=26.0 - index * 0.02,
            outdoor=20.0,
            fan_speed=8,
            mode=MODE_VENTILATE,
            model=model,
        )
    assert effect.rate is not None
    assert effect.rate > 0.0


def test_hourly_forecast_interpolates_from_live_outdoor_reading():
    now = datetime(2026, 10, 22, tzinfo=timezone.utc)
    value, used = _forecast_value(
        [{"datetime": (now + timedelta(hours=1)).isoformat(), "temperature": 30.0}],
        field="temperature",
        current=20.0,
        now=now,
        minutes_ahead=30.0,
    )
    assert used is True
    assert value == 25.0


def test_forecast_warming_can_switch_fresh_air_to_evaporative():
    now = datetime(2026, 10, 22, tzinfo=timezone.utc)
    manager = WholeHousePlantManager(WholeHousePlantConfig(
        entity_id="climate.cooler",
        cooling_target=23.0,
        fresh_air_max_outdoor_temperature=28.0,
        minimum_ventilation_run_minutes=0,
        require_home_presence=False,
        require_occupancy=False,
    ))
    manager.state.commanded_mode = MODE_VENTILATE
    manager.state.mode_since = 0.0
    plan = WholeHousePlantPlan(MODE_VENTILATE, False, "fresh air", None, True, True, True, 8, False)
    shared = dict(
        manager=manager,
        initial_plan=plan,
        model=RCModel(C=1.0, U=0.1, Q_cool=2.0),
        fresh_air_rate=0.5,
        idle_ready=True,
        cooling_ready=True,
        indoor_temperature=26.0,
        indoor_humidity=40.0,
        outdoor_temperature=20.0,
        outdoor_humidity=40.0,
        home_occupied=True,
        area_occupied=True,
        heating_active=False,
        exhaust_ready=True,
        outdoor_air_safe=True,
        ventilation_requested=False,
        forecast_high_temperature=None,
        forecast_peak_hours_away=None,
        forecast_now=now,
        now=1800.0,
    )
    steady = predict_whole_house_operation(**shared, weather_forecast=[])
    warming = predict_whole_house_operation(
        **shared,
        weather_forecast=[{"datetime": (now + timedelta(minutes=30)).isoformat(), "temperature": 32.0}],
    )
    assert steady.modes == (MODE_VENTILATE,) * 6
    assert MODE_COOL in warming.modes
    assert warming.weather_forecast_used is True
    assert warming.temperature != steady.temperature
