"""Predictive advice for the isolated whole-house thermal model."""

from __future__ import annotations

from dataclasses import dataclass

from ..control.thermal_model import RoomModelManager

WHOLE_HOUSE_MODEL_ID = "__whole_house_plant__"
FORECAST_MINUTES = 30.0
READINESS_MINUTES = 5.0
MIN_IDLE_UPDATES = 60
MIN_ACTIVE_UPDATES = 20
MPC_MAX_PREDICTION_STD = 0.5


@dataclass(frozen=True)
class WholeHouseMpcAdvice:
    """Current readiness and idle-drift forecast for the central plant."""

    predicted_temperature: float | None
    heating_ready: bool
    cooling_ready: bool
    confidence: float
    n_idle: int
    n_heating: int
    n_cooling: int


def get_whole_house_mpc_advice(
    models: RoomModelManager,
    current_temperature: float | None,
    outdoor_temperature: float | None,
) -> WholeHouseMpcAdvice:
    """Return mode-specific readiness and a bounded 30-minute idle forecast."""
    n_idle, n_heating, n_cooling = models.get_mode_counts(WHOLE_HOUSE_MODEL_ID)
    confidence = models.get_confidence(WHOLE_HOUSE_MODEL_ID)
    if current_temperature is None or outdoor_temperature is None:
        return WholeHouseMpcAdvice(None, False, False, confidence, n_idle, n_heating, n_cooling)

    model = models.get_model(WHOLE_HOUSE_MODEL_ID)
    idle_std = models.get_prediction_std(
        WHOLE_HOUSE_MODEL_ID,
        0.0,
        current_temperature,
        outdoor_temperature,
        READINESS_MINUTES,
    )
    predicted = model.predict(current_temperature, outdoor_temperature, 0.0, FORECAST_MINUTES)
    predicted = max(current_temperature - 3.0, min(current_temperature + 3.0, predicted))
    idle_ready = n_idle >= MIN_IDLE_UPDATES and idle_std < MPC_MAX_PREDICTION_STD
    heat_std = models.get_prediction_std(
        WHOLE_HOUSE_MODEL_ID,
        model.Q_heat,
        current_temperature,
        outdoor_temperature,
        READINESS_MINUTES,
    )
    cool_std = models.get_prediction_std(
        WHOLE_HOUSE_MODEL_ID,
        -model.Q_cool,
        current_temperature,
        outdoor_temperature,
        READINESS_MINUTES,
    )
    return WholeHouseMpcAdvice(
        predicted_temperature=predicted,
        heating_ready=idle_ready and n_heating >= MIN_ACTIVE_UPDATES and heat_std < MPC_MAX_PREDICTION_STD,
        cooling_ready=idle_ready and n_cooling >= MIN_ACTIVE_UPDATES and cool_std < MPC_MAX_PREDICTION_STD,
        confidence=confidence,
        n_idle=n_idle,
        n_heating=n_heating,
        n_cooling=n_cooling,
    )
