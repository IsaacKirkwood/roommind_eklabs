"""Tests for whole-house plant safety and mode planning."""

from custom_components.roommind_eklabs.managers.whole_house_plant_manager import (
    MODE_COOL,
    MODE_OFF,
    MODE_VENTILATE,
    WholeHousePlantConfig,
    WholeHousePlantManager,
    dew_point_celsius,
    wet_bulb_celsius,
)


def _evaluate(manager, **overrides):
    values = {
        "indoor_temperature": 27.0,
        "indoor_humidity": 50.0,
        "outdoor_temperature": 21.9,
        "outdoor_humidity": 40.0,
        "home_occupied": True,
        "area_occupied": True,
        "heating_active": False,
        "exhaust_ready": True,
        "outdoor_air_safe": True,
        "ventilation_requested": False,
        "reported_mode": MODE_OFF,
        "feedback_available": True,
        "feedback_age_seconds": 0,
        "now": 1000,
    }
    values.update(overrides)
    return manager.evaluate(**values)


def test_fresh_air_is_preferred_for_temperature_demand():
    manager = WholeHousePlantManager(WholeHousePlantConfig("climate.magiqtouch_zone_1"))
    plan = _evaluate(manager)
    assert plan.mode == MODE_VENTILATE
    assert plan.cooling_allowed is True
    assert plan.fresh_air_suitable is True
    assert plan.reason == "fresh air preferred for cooling"


def test_evaporative_cooling_is_used_when_outside_is_above_fresh_air_limit():
    manager = WholeHousePlantManager(WholeHousePlantConfig("climate.magiqtouch_zone_1"))
    plan = _evaluate(manager, outdoor_temperature=25.0)
    assert plan.mode == MODE_COOL
    assert plan.fresh_air_suitable is False


def test_evaporative_cooling_is_used_when_outside_is_too_humid_for_fresh_air():
    manager = WholeHousePlantManager(
        WholeHousePlantConfig(
            "climate.magiqtouch_zone_1",
            fresh_air_max_outdoor_humidity=55.0,
            evaporative_max_outdoor_humidity=70.0,
        )
    )
    plan = _evaluate(manager, outdoor_humidity=60.0)
    assert plan.mode == MODE_COOL


def test_fresh_air_requires_outside_to_be_cooler_than_inside():
    manager = WholeHousePlantManager(
        WholeHousePlantConfig(
            "climate.magiqtouch_zone_1",
            fresh_air_max_outdoor_temperature=30.0,
        )
    )
    plan = _evaluate(manager, indoor_temperature=27.0, outdoor_temperature=28.0)
    assert plan.mode == MODE_COOL


def test_configured_fresh_air_threshold_allows_warmer_outdoor_air():
    manager = WholeHousePlantManager(
        WholeHousePlantConfig(
            "climate.magiqtouch_zone_1",
            cooling_target=23.0,
            cooling_start_delta=0.5,
            fresh_air_max_outdoor_temperature=28.0,
            fresh_air_requires_cooler_outdoor=False,
            fresh_air_min_indoor_temperature=23.0,
            minimum_outdoor_cooling_temp=28.0,
        )
    )
    plan = _evaluate(manager, indoor_temperature=26.1, outdoor_temperature=27.1)
    assert plan.mode == MODE_VENTILATE
    assert plan.reason == "fresh air preferred for cooling"

    manager.state.commanded_mode = MODE_OFF
    plan = _evaluate(manager, indoor_temperature=23.1, outdoor_temperature=27.1)
    assert plan.mode == MODE_VENTILATE

    manager.state.commanded_mode = MODE_OFF
    plan = _evaluate(manager, indoor_temperature=23.0, outdoor_temperature=27.1)
    assert plan.mode == MODE_OFF

    plan = _evaluate(manager, indoor_temperature=26.1, outdoor_temperature=28.0)
    assert plan.mode == MODE_COOL


def test_forecast_precool_uses_wet_bulb_before_fan_changeover():
    config = WholeHousePlantConfig(
        "climate.plant",
        cooling_target=25.0,
        fresh_air_max_outdoor_temperature=28.0,
        fresh_air_requires_cooler_outdoor=False,
        fresh_air_min_indoor_temperature=23.0,
        minimum_outdoor_cooling_temp=28.0,
        forecast_precool_enabled=True,
        forecast_precool_high_temperature=32.0,
        forecast_precool_lead_hours=6,
        evaporative_min_indoor_outdoor_delta=2.0,
    )
    manager = WholeHousePlantManager(config)
    plan = _evaluate(
        manager,
        indoor_temperature=26.0,
        outdoor_temperature=27.0,
        outdoor_humidity=40.0,
        forecast_high_temperature=35.0,
        forecast_peak_hours_away=3.0,
    )
    assert plan.mode == MODE_COOL
    assert plan.reason == "forecast pre-cooling before hot peak"

    manager = WholeHousePlantManager(config)
    no_forecast = _evaluate(manager, indoor_temperature=26.0, outdoor_temperature=27.0)
    assert no_forecast.mode == MODE_VENTILATE

    manager = WholeHousePlantManager(config)
    cool_air = _evaluate(
        manager,
        indoor_temperature=26.0,
        outdoor_temperature=24.0,
        forecast_high_temperature=35.0,
        forecast_peak_hours_away=3.0,
    )
    assert cool_air.mode == MODE_VENTILATE

    manager = WholeHousePlantManager(config)
    humid = _evaluate(
        manager,
        indoor_temperature=26.0,
        outdoor_temperature=27.0,
        outdoor_humidity=90.0,
        forecast_high_temperature=35.0,
        forecast_peak_hours_away=3.0,
    )
    assert humid.mode == MODE_OFF


def test_evaporative_run_limit_moves_to_fan_then_allows_restart_after_rest():
    manager = WholeHousePlantManager(
        WholeHousePlantConfig(
            "climate.plant",
            cooling_target=25.0,
            fresh_air_max_outdoor_temperature=28.0,
            fresh_air_requires_cooler_outdoor=False,
            minimum_outdoor_cooling_temp=28.0,
            forecast_precool_enabled=True,
            forecast_precool_high_temperature=32.0,
            maximum_cooling_run_minutes=90,
            cooling_rest_minutes=20,
            minimum_cooling_run_minutes=20,
            minimum_ventilation_run_minutes=0,
        )
    )
    conditions = dict(
        indoor_temperature=27.0,
        outdoor_temperature=26.7,
        forecast_high_temperature=35.0,
        forecast_peak_hours_away=3.0,
    )
    assert _evaluate(manager, now=1000, **conditions).mode == MODE_COOL
    resting = _evaluate(manager, now=6401, reported_mode=MODE_COOL, **conditions)
    assert resting.mode == MODE_VENTILATE
    assert resting.reason == "evaporative run limit; fresh air preferred"
    assert _evaluate(manager, now=7000, reported_mode=MODE_VENTILATE, **conditions).mode == MODE_VENTILATE
    assert _evaluate(manager, now=7602, reported_mode=MODE_VENTILATE, **conditions).mode == MODE_COOL


def test_evaporative_rest_turns_off_when_fresh_air_is_too_hot():
    manager = WholeHousePlantManager(
        WholeHousePlantConfig(
            "climate.plant",
            fresh_air_max_outdoor_temperature=28.0,
            maximum_cooling_run_minutes=60,
            cooling_rest_minutes=20,
        )
    )
    assert _evaluate(manager, now=1000, outdoor_temperature=32.0).mode == MODE_COOL
    resting = _evaluate(manager, now=4601, outdoor_temperature=32.0, reported_mode=MODE_COOL)
    assert resting.mode == MODE_OFF
    assert resting.reason == "evaporative run limit; resting"
    assert _evaluate(manager, now=5000, outdoor_temperature=32.0).mode == MODE_OFF
    assert _evaluate(manager, now=5802, outdoor_temperature=32.0).mode == MODE_COOL


def test_evaporative_rest_does_not_use_warmer_fan_air():
    manager = WholeHousePlantManager(
        WholeHousePlantConfig(
            "climate.plant",
            cooling_target=25.0,
            fresh_air_max_outdoor_temperature=28.0,
            fresh_air_requires_cooler_outdoor=False,
            minimum_outdoor_cooling_temp=28.0,
            forecast_precool_enabled=True,
            forecast_precool_high_temperature=32.0,
            maximum_cooling_run_minutes=30,
            minimum_cooling_run_minutes=20,
            cooling_rest_minutes=20,
        )
    )
    conditions = dict(
        indoor_temperature=26.0,
        outdoor_temperature=27.0,
        forecast_high_temperature=35.0,
        forecast_peak_hours_away=2.0,
    )
    assert _evaluate(manager, now=1000, **conditions).mode == MODE_COOL
    rested = _evaluate(manager, now=2801, reported_mode=MODE_COOL, **conditions)
    assert rested.mode == MODE_OFF
    assert rested.reason == "evaporative run limit; resting"


def test_hot_dry_air_uses_wet_bulb_advantage():
    manager = WholeHousePlantManager(WholeHousePlantConfig("climate.magiqtouch_zone_1"))
    plan = _evaluate(
        manager,
        indoor_temperature=28.0,
        outdoor_temperature=32.0,
        outdoor_humidity=20.0,
    )
    assert wet_bulb_celsius(32.0, 20.0) < 20.0
    assert plan.mode == MODE_COOL


def test_heating_interlock_blocks_cooling():
    manager = WholeHousePlantManager(WholeHousePlantConfig("climate.magiqtouch_zone_1"))
    plan = _evaluate(manager, heating_active=True)
    assert plan.mode == MODE_OFF
    assert plan.reason == "heating interlock"


def test_manual_fresh_air_selects_fan_only():
    manager = WholeHousePlantManager(
        WholeHousePlantConfig("climate.magiqtouch_zone_1", operating_mode="fan_only")
    )
    plan = _evaluate(manager, indoor_temperature=22.0)
    assert plan.mode == MODE_VENTILATE
    assert plan.reason == "fresh air selected"


def test_manual_cooling_still_obeys_evaporative_lockout():
    manager = WholeHousePlantManager(
        WholeHousePlantConfig("climate.magiqtouch_zone_1", operating_mode="cool")
    )
    plan = _evaluate(manager, outdoor_humidity=95.0)
    assert plan.mode == MODE_OFF
    assert plan.reason == "outdoor humidity too high for evaporative cooling"


def test_evaporative_cooling_blocks_high_humidity_but_allows_fresh_air():
    manager = WholeHousePlantManager(WholeHousePlantConfig("climate.magiqtouch_zone_1"))
    plan = _evaluate(manager, outdoor_humidity=90.0, ventilation_requested=True)
    assert plan.mode == MODE_VENTILATE
    assert plan.cooling_allowed is False


def test_evaporative_cooling_stops_at_indoor_humidity_limit_and_waits_for_margin():
    manager = WholeHousePlantManager(
        WholeHousePlantConfig(
            "climate.plant",
            minimum_cooling_run_minutes=30,
            evaporative_max_indoor_humidity=70.0,
            evaporative_humidity_resume_delta=5.0,
        )
    )
    _evaluate(manager, indoor_humidity=60.0, outdoor_temperature=25.0, now=1000)
    stopped = _evaluate(
        manager,
        indoor_humidity=70.0,
        outdoor_temperature=25.0,
        reported_mode=MODE_COOL,
        now=1100,
    )
    assert stopped.mode == MODE_OFF
    assert stopped.reason == "indoor humidity limit reached"

    waiting = _evaluate(manager, indoor_humidity=68.0, outdoor_temperature=25.0, now=1200)
    assert waiting.mode == MODE_OFF
    assert waiting.reason == "waiting for indoor humidity to fall"

    restarted = _evaluate(manager, indoor_humidity=65.0, outdoor_temperature=25.0, now=1300)
    assert restarted.mode == MODE_COOL


def test_refrigerated_cooling_has_dew_point_guard():
    config = WholeHousePlantConfig("climate.plant", cooling_type="refrigerated", cooling_target=18.0)
    manager = WholeHousePlantManager(config)
    plan = _evaluate(manager, indoor_temperature=25.0, indoor_humidity=80.0, outdoor_temperature=25.0)
    assert dew_point_celsius(25.0, 80.0) > 21.0
    assert plan.mode == MODE_OFF
    assert plan.reason == "dew-point protection"


def test_nobody_home_blocks_cooling_and_ventilation():
    manager = WholeHousePlantManager(WholeHousePlantConfig("climate.plant"))
    plan = _evaluate(manager, home_occupied=False, ventilation_requested=True)
    assert plan.mode == MODE_OFF
    assert plan.ventilation_allowed is False


def test_unchanged_available_feedback_is_not_treated_as_stale():
    manager = WholeHousePlantManager(WholeHousePlantConfig("climate.plant"))
    plan = _evaluate(manager, feedback_age_seconds=181)
    assert plan.mode == MODE_VENTILATE
    assert plan.fault is None


def test_command_mismatch_becomes_fault_after_timeout():
    manager = WholeHousePlantManager(WholeHousePlantConfig("climate.plant", feedback_timeout_seconds=120))
    _evaluate(manager, outdoor_temperature=25.0, now=1000)
    pending = _evaluate(manager, outdoor_temperature=25.0, reported_mode=MODE_OFF, now=1010)
    faulted = _evaluate(manager, outdoor_temperature=25.0, reported_mode=MODE_OFF, now=1131)
    assert pending.fault is None
    assert faulted.mode == MODE_OFF
    assert faulted.fault == "plant failed to follow command"


def test_maximum_runtime_stops_plant():
    manager = WholeHousePlantManager(WholeHousePlantConfig("climate.plant", max_continuous_runtime_minutes=10))
    _evaluate(manager, outdoor_temperature=25.0, now=1000)
    plan = _evaluate(manager, outdoor_temperature=25.0, reported_mode=MODE_COOL, now=1601)
    assert plan.mode == MODE_OFF
    assert plan.fault == "maximum runtime exceeded"


def test_cooling_holds_for_minimum_run_then_stops_at_target():
    manager = WholeHousePlantManager(
        WholeHousePlantConfig("climate.plant", minimum_cooling_run_minutes=30)
    )
    started = _evaluate(manager, outdoor_temperature=25.0, now=1000)
    held = _evaluate(manager, indoor_temperature=24.0, outdoor_temperature=25.0, reported_mode=MODE_COOL, now=1600)
    stopped = _evaluate(manager, indoor_temperature=24.0, outdoor_temperature=25.0, reported_mode=MODE_COOL, now=2801)
    assert started.mode == MODE_COOL
    assert held.mode == MODE_COOL
    assert held.reason == "minimum cooling run"
    assert stopped.mode == MODE_OFF


def test_fresh_air_holds_for_minimum_run():
    manager = WholeHousePlantManager(
        WholeHousePlantConfig("climate.plant", minimum_ventilation_run_minutes=30)
    )
    _evaluate(manager, indoor_temperature=22.0, ventilation_requested=True, now=1000)
    held = _evaluate(manager, indoor_temperature=22.0, reported_mode=MODE_VENTILATE, now=1600)
    assert held.mode == MODE_VENTILATE
    assert held.reason == "minimum fresh-air run"


def test_cooling_fan_speed_scales_with_temperature_demand():
    manager = WholeHousePlantManager(
        WholeHousePlantConfig(
            "climate.plant",
            cooling_target=24.0,
            cooling_fan_min_speed=4,
            cooling_fan_max_speed=10,
        )
    )
    low = _evaluate(manager, indoor_temperature=24.5, outdoor_temperature=25.0, now=1000)
    manager = WholeHousePlantManager(manager.config)
    high = _evaluate(manager, indoor_temperature=28.0, outdoor_temperature=25.0, now=1000)
    assert low.fan_speed == 4
    assert high.fan_speed == 10


def test_safety_gate_overrides_minimum_run():
    manager = WholeHousePlantManager(
        WholeHousePlantConfig("climate.plant", minimum_cooling_run_minutes=30)
    )
    _evaluate(manager, outdoor_temperature=25.0, now=1000)
    plan = _evaluate(manager, reported_mode=MODE_COOL, home_occupied=False, now=1100)
    assert plan.mode == MODE_OFF


def test_evaporative_cooling_can_require_an_exhaust_path():
    manager = WholeHousePlantManager(
        WholeHousePlantConfig("climate.plant", require_exhaust_ready=True)
    )
    blocked = _evaluate(manager, exhaust_ready=False)
    assert blocked.mode == MODE_OFF
    assert blocked.reason == "open an exhaust path"

    manager = WholeHousePlantManager(manager.config)
    allowed = _evaluate(manager, exhaust_ready=True, outdoor_temperature=25.0)
    assert allowed.mode == MODE_COOL


def test_outdoor_air_quality_lockout_stops_cooling_and_fan():
    manager = WholeHousePlantManager(WholeHousePlantConfig("climate.plant"))
    cooling = _evaluate(manager, outdoor_air_safe=False)
    assert cooling.mode == MODE_OFF
    assert cooling.reason == "outdoor air quality lockout"

    manager = WholeHousePlantManager(
        WholeHousePlantConfig("climate.plant", operating_mode=MODE_VENTILATE)
    )
    fan = _evaluate(manager, outdoor_air_safe=False)
    assert fan.mode == MODE_OFF
    assert fan.reason == "outdoor air quality lockout"


def test_mpc_forecast_can_start_cooling_before_threshold():
    manager = WholeHousePlantManager(WholeHousePlantConfig("climate.plant", cooling_target=24.0))
    fallback = _evaluate(
        manager,
        indoor_temperature=24.2,
        outdoor_temperature=25.0,
        predicted_temperature=25.0,
    )
    assert fallback.mode == MODE_OFF

    manager = WholeHousePlantManager(manager.config)
    predictive = _evaluate(
        manager,
        indoor_temperature=24.2,
        outdoor_temperature=25.0,
        predicted_temperature=25.0,
        mpc_cooling_active=True,
    )
    assert predictive.mode == MODE_COOL
    assert predictive.fan_speed > manager.config.cooling_fan_min_speed


def test_running_cooling_stops_from_measurement_not_idle_forecast():
    manager = WholeHousePlantManager(
        WholeHousePlantConfig("climate.plant", cooling_target=24.0, minimum_cooling_run_minutes=0)
    )
    _evaluate(manager, indoor_temperature=26.0, outdoor_temperature=25.0, now=1000)
    stopped = _evaluate(
        manager,
        indoor_temperature=24.1,
        outdoor_temperature=25.0,
        predicted_temperature=26.0,
        mpc_cooling_active=True,
        reported_mode=MODE_COOL,
        now=1100,
    )
    assert stopped.mode == MODE_OFF
