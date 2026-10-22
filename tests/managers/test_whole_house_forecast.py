"""The card forecast must follow real whole-house mode transitions."""

from custom_components.roommind_eklabs.control.thermal_model import RCModel
from custom_components.roommind_eklabs.managers.whole_house_forecast import (
    FreshAirEffect,
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
