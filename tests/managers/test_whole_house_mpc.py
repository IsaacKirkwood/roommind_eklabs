"""Whole-house MPC readiness and forecast tests."""

from unittest.mock import Mock

from custom_components.roommind_eklabs.managers.whole_house_mpc import (
    WHOLE_HOUSE_MODEL_ID,
    get_whole_house_mpc_advice,
)


def _models(*, counts=(60, 20, 20), prediction_std=0.2, predicted=17.5):
    models = Mock()
    models.get_mode_counts.return_value = counts
    models.get_confidence.return_value = 0.8
    model = models.get_model.return_value
    model.Q_heat = 2.0
    model.Q_cool = 3.0
    model.predict.return_value = predicted
    models.get_prediction_std.return_value = prediction_std
    return models


def test_house_model_is_isolated_and_mode_ready():
    models = _models()
    advice = get_whole_house_mpc_advice(models, 18.0, 10.0)
    assert advice.heating_ready is True
    assert advice.cooling_ready is True
    assert advice.predicted_temperature == 17.5
    models.get_mode_counts.assert_called_once_with(WHOLE_HOUSE_MODEL_ID)


def test_heating_and_cooling_graduate_independently():
    advice = get_whole_house_mpc_advice(_models(counts=(60, 20, 3)), 18.0, 10.0)
    assert advice.heating_ready is True
    assert advice.cooling_ready is False


def test_uncertain_model_remains_in_fallback():
    advice = get_whole_house_mpc_advice(_models(prediction_std=0.8), 24.0, 32.0)
    assert advice.heating_ready is False
    assert advice.cooling_ready is False


def test_forecast_is_bounded_against_runaway_model():
    advice = get_whole_house_mpc_advice(_models(predicted=40.0), 24.0, 35.0)
    assert advice.predicted_temperature == 27.0
