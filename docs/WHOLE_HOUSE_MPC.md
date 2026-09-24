# Whole-House MPC

RoomMind keeps one dedicated thermal model for the central plant. It is stored under
`__whole_house_plant__` and is independent of every room model.

## Learned dynamics

- Idle heat loss against outdoor temperature
- Whole-house gas-heating gain at full output
- Evaporative-cooling gain weighted by Magiqtouch fan speed
- Solar gain from RoomMind's existing irradiance estimate

Fresh-air operation is excluded from training because deliberate outdoor-air exchange is neither
idle behavior nor evaporative cooling.

## Activation

The controller starts with the existing hysteresis policy. Heating and cooling graduate
independently to MPC after at least 60 idle observations, 20 observations for the relevant active
mode, and a five-minute prediction uncertainty below 0.5 C.

An MPC-ready model forecasts idle drift 30 minutes ahead. The bounded forecast may start heating
or cooling early, but an active plant always stops from the measured corrected house average. All
presence, gas/cooling exclusion, humidity, wet-bulb, feedback, sensor, minimum-run, and maximum-run
guards remain authoritative.

## Simulation audit

The deterministic audit used a synthetic house with known heat loss of 0.09 per hour, gas gain of
3.2 C/hour, cooling gain of 4.4 C/hour, five-minute samples, variable outdoor temperatures, and
fan-weighted cooling.

After 1,000 mixed-mode samples, the EKF learned:

| Parameter | True | Learned |
| --- | ---: | ---: |
| Heat loss | 0.090 | 0.090 |
| Gas gain | 3.200 | 3.212 |
| Cooling gain | 4.400 | 4.416 |

The model reached 95.6% confidence and independently enabled heating and cooling MPC. A seven-day
comparison with 30-minute minimum runs removed all modeled comfort-threshold misses in the winter
and summer scenarios. Runtime increased by about 2.5 hours per week because the predictive policy
starts before a threshold crossing; this is the expected comfort-versus-energy tradeoff.

The safety matrix also verifies fallback before calibration, immediate nobody-home shutdown,
gas/cooling interlock, high-humidity lockout, missing-temperature fail-closed behavior, fresh-air
separation, minimum runs, adaptive fan limits, bounded forecasts, and measured-temperature stop
decisions.
