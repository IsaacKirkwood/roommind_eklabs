# RoomMind - EKLabs Fork

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.5%2B-blue.svg)](https://www.home-assistant.io/)
[![License](https://img.shields.io/github/license/IsaacKirkwood/roommind_eklabs)](https://github.com/IsaacKirkwood/roommind_eklabs/blob/main/LICENSE)
[![Tests](https://github.com/IsaacKirkwood/roommind_eklabs/actions/workflows/ci.yml/badge.svg)](https://github.com/IsaacKirkwood/roommind_eklabs/actions/workflows/ci.yml)
![Coverage](https://raw.githubusercontent.com/IsaacKirkwood/roommind_eklabs/python-coverage-comment-action-data/badge.svg)
[![GitHub Release](https://img.shields.io/github/v/release/IsaacKirkwood/roommind_eklabs)](https://github.com/IsaacKirkwood/roommind_eklabs/releases/latest)

**Room-by-room and whole-house climate control for Home Assistant**, with self-learning thermal models, proportional device control, central plant coordination, and a dedicated management panel.

> [!IMPORTANT]
> This is an experimental community fork of [RoomMind](https://github.com/snazzybean/roommind), originally created by [SnazzyBean](https://github.com/snazzybean). It is not the official upstream release. The EKLabs changes are being developed through an AI-assisted "vibe coding" workflow: ideas and implementations are produced collaboratively with coding agents, then reviewed and exercised with automated tests. Treat new releases as enthusiast software and keep a working Home Assistant backup.

![Dashboard](docs/images/page-dashboard.png)

## Features

### EKLabs additions

- **Whole-House Gas Heating** - A central heat source can maintain a configurable house target while local room heaters provide targeted trim heating.
- **Corrected Sensor Averaging** - Combine multiple temperature and humidity sensors into whole-house readings and apply a correction to each sensor independently.
- **Occupancy-Led Plant Control** - Gate whole-house operation using household presence, downstairs presence sensors, and active media players.
- **Whole-House Comfort Schedule** - Switch the central heating target between Comfort and Eco using a Home Assistant schedule helper.
- **Fresh-Air-First Whole-House Cooling** - MagIQtouch plant control tries fan-only outside-air cooling before evaporative cooling when configurable outdoor temperature and humidity limits are met. Optional forecast pre-cooling can start evaporative cooling ahead of a hot peak when fan-only air will not cool the house. A configurable evaporative run limit and rest period prevent continuous water cooling; the plant moves to fan-only during the rest when outside air is suitable. It also includes adaptive fan speed, minimum runs, indoor-humidity hysteresis, optional exhaust-path confirmation and outdoor-air-quality lockouts, live controls on the Rooms page, and weather, wet-bulb, runtime, feedback, presence, and gas-heating interlocks.
- **Demand-Based Fan Control** - Evaporative cooling raises fan speed between its configured minimum and maximum as the indoor temperature rises above target, then steps back down as the house cools. Fresh-air cooling does the same when outdoor air is cooler than indoors, starting at the fresh-air minimum and using the cooling maximum. An ordinary fresh-air request, or fan-only operation with warmer outdoor air allowed by settings, stays at the fresh-air minimum. Failed fan commands are retried after controller control returns to Home Assistant.
- **Whole-House MPC** - A dedicated persisted thermal model learns gas-heating gain, fan-weighted evaporative-cooling gain, and idle heat loss without mixing data into any room model. Heating and cooling graduate independently from hysteresis fallback to 30-minute predictive control.
- **Whole-House Analytics** - Select **Whole House** in Analytics to see the central temperature, cooling target, heating/evaporative/fan-only periods, model learning statistics, and a three-hour idle-temperature projection based on the weather forecast. History starts collecting after this version is installed; the live reading appears immediately. The projection assumes heating and cooling stay off and does not simulate future automatic mode changes or fan cooling.
- **Independent Room Learning** - Shared gas heat is exposed separately to each room's thermal model so central heating does not masquerade as local heater output.

### Original RoomMind capabilities

- **Self-Learning MPC** - Per-room thermal model (Extended Kalman Filter) that learns your home's heating/cooling behavior over time. Automatic fallback to on/off control while learning.
- **Proportional Valve Control** - TRVs receive calculated setpoints instead of simple on/off, producing smoother temperature curves with less overshoot.
- **Solar Gain Awareness** - Estimates solar irradiance from sun position and weather data. The model learns each room's solar response and reduces unnecessary heating.
- **Multi-Scheduler** - Multiple `schedule.*` entities per room with selector switching via `input_boolean` or `input_number`.
- **Manual Override** - Boost, eco, or custom temperature with configurable duration and instant UI feedback.
- **Presence Detection** - Link `person.*`, `device_tracker.*`, `binary_sensor.*`, or `input_boolean.*` entities globally or per room. Eco temperature is used when all assigned persons are away.
- **Ignore Presence per Room** - Rooms can opt out of presence detection to always follow their schedule.
- **Vacation Mode** - Global setback temperature with end date for all rooms.
- **Window/Door Pause** - Pauses climate control when windows or doors are open, with configurable open/close delays.
- **Mold Risk Detection & Prevention** - Surface humidity estimation using the DIN 4108-2 method. Configurable notifications and automatic temperature raise to prevent mold growth.
- **Automatic Blind/Cover Shading** - Smart cover deployment based on predicted solar overheating. Includes night close, manual override detection, and cover schedules.
- **Valve Protection** - Periodic cycling of idle TRV valves to prevent seizing and calcification.
- **Heat Source Orchestration** - Rooms with both TRVs and ACs automatically route heating demand to the most efficient device based on temperature gap and outdoor conditions.
- **Compressor Group Protection** - Define groups of climate devices sharing an outdoor compressor. Enforces minimum run and off times to prevent short-cycling.
- **Fan-only & Setback Idle Modes** - AC and heat pump devices can switch to fan-only or setback mode instead of turning off, keeping air circulation or low-load operation active.
- **Per-Device Setpoint Mode** - Choose proportional (boost setpoint) or direct (exact target) control per device for optimal results with different hardware.
- **Separate Heat/Cool Targets** - Independent comfort and eco temperatures for heating and cooling in auto mode, creating a natural dead-band.
- **Per-Room Climate Toggle** - Disable climate control for individual rooms while keeping other rooms active.
- **Outdoor Areas** - Mark rooms as outdoor (e.g. balcony) to disable climate control while keeping monitoring.
- **Analytics Dashboard** - Temperature charts with heating power, solar irradiance, and model predictions over 24h to 90 days.
- **Mobile Ready** - Responsive layout with HA-native toolbar for the companion app.
- **Multilingual** - English and German, auto-detected from your HA language setting.

## Installation

[![Open your Home Assistant instance and add the EKLabs fork to HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=IsaacKirkwood&repository=roommind_eklabs&category=integration)

### HACS (Recommended)

1. Open HACS in Home Assistant.
2. Add `https://github.com/IsaacKirkwood/roommind_eklabs` as a custom integration repository, or use the button above.
3. Install **RoomMind - EKLabs Fork**.
4. Restart Home Assistant.
5. Go to **Settings > Devices & Services > Add Integration > RoomMind - EKLabs Fork**.

The fork uses the `roommind_eklabs` integration domain and can be installed alongside upstream RoomMind while you evaluate it. Do not point both integrations at the same climate devices for active control.

### Manual

1. Copy `custom_components/roommind_eklabs/` to your `config/custom_components/` directory
2. Restart Home Assistant
3. Go to **Settings > Devices & Services > Add Integration > RoomMind - EKLabs Fork**

## Quick Start

After installation, RoomMind appears as a panel in the HA sidebar.

1. **Open RoomMind** from the sidebar - you'll see all your HA areas as room cards
2. **Click a room card** to open the detail view
3. **Add devices** - assign at least one thermostat or AC (`climate.*` entity)
4. **Add a temperature sensor** (optional but recommended) - enables Full Control with proportional valve control
5. **Add a schedule** - create a `schedule.*` helper in HA and assign it
6. **Set temperatures** - configure comfort (schedule on) and eco (schedule off) temperatures

RoomMind starts controlling immediately. If MPC is enabled (default), the thermal model begins learning in the background.

### Whole-house humidity sensors

In **RoomMind > Settings > House averages**, add one or more humidity sensors for the whole-house evaporative cooler. You can set a correction for each sensor; RoomMind averages the valid corrected readings. Add or remove sensors there, then reload the page to confirm the selection was saved. To replace a sensor, remove the old one and add the new one. The same section holds the whole-house temperature sensors used for heating and cooling decisions.

The settings page saves each changed field without resubmitting an older copy of the whole-house configuration. Older installations with a single humidity sensor are migrated to the multi-sensor setting. Since **v0.8.17**, averaging humidity sensors also preserves the configured cooler's `climate.*` entity ID when RoomMind sends mode and fan commands.

### Whole-house fan and evaporative cooling example

In **RoomMind > Settings > Whole-house cooler**, select **Auto** to let RoomMind choose between fan-only and evaporative modes. The following is the configuration used for the EKLabs MagIQtouch installation as of v0.8.20; it is an example, not a default applied to every installation.

| Setting | EKLabs value | Effect |
|---|---:|---|
| Cooling target / start / stop margin | 25°C / 0.5°C / 0.2°C | Normally starts evaporative cooling at 25.5°C and may stop after reaching 25.2°C. |
| Fresh-air indoor start | Above 23°C | Requests fan-only below the outdoor limit, independently of the evaporative target. |
| Fresh-air outdoor limit | Below 28°C | At exactly 28°C, the normal fan-only cooling path is excluded. |
| Require cooler outside air | Off | Normal fan-only mode can run below 28°C even when outside is warmer than indoors. This may warm the house. |
| Fresh-air outdoor humidity limit | 75% | Blocks automatic fresh-air cooling above this humidity. |
| Evaporative outdoor minimum | 28°C | Normally switches to evaporative cooling at or above 28°C when cooling is needed and safeguards pass. Forecast pre-cooling is the exception below 28°C. |
| Evaporative outdoor / indoor humidity limits | 65% / 60% | Avoids water cooling in humid conditions; indoor humidity must fall 5 percentage points below the limit before restarting. |
| Minimum wet-bulb advantage | 2°C | Requires estimated outdoor wet-bulb temperature to be at least 2°C below indoor temperature. |
| Forecast pre-cooling | On; 32°C peak within 6 hours | May use evaporative cooling before 28°C on a forecast hot day when outdoor air is no more than 0.5°C cooler than indoors and the house is at least 24.5°C. Current humidity and wet-bulb limits still apply. |
| Evaporative minimum / maximum run | 20 / 90 minutes | Reduces short cycling and caps each continuous water-cooling run. |
| Evaporative rest | 20 minutes | After the run cap, uses fan-only if outside is cooler than indoors and below the fresh-air limits; otherwise turns off until the rest ends. |

Forecast pre-cooling uses the highest **remaining hourly forecast temperature for the current local day** from the configured weather entity. If the forecast is unavailable, RoomMind follows the normal temperature and humidity rules. Manual **Cool** mode or a temporary Cool override forces evaporative cooling and bypasses Auto's mode choice and timed rest. Presence, air-quality, controller feedback, and gas-heating interlocks still apply. Ducted evaporative cooling needs an open window, door, or other exhaust path; configure **Require an open exhaust path** with a suitable sensor if you have one.

### House cooling dashboard card

RoomMind includes a read-only dashboard card for household members who want to see what the whole-house cooler is doing without changing its settings. The full layout shows the indoor temperature, cooling target, outdoor temperature, fan speed, humidity, current mode, why that mode was chosen, the highest remaining forecast temperature today, and a 30-minute model estimate.

Install [RoomMind v0.8.27 or later](https://github.com/IsaacKirkwood/roommind_eklabs/releases/latest) and restart Home Assistant. In **Settings → Dashboards → Resources**, add the following URL as a **JavaScript module**. If you already added the card, **edit the existing resource URL** to this one so your dashboard loads the latest compact layout:

```text
/roommind_eklabs/roommind-house-status-card.js?v=0.8.27
```

Add a **Manual** card to any dashboard for the full layout:

```yaml
type: custom:roommind-house-status-card
title: House cooling
```

For a small tablet card, add `compact: true`. This layout shows the current indoor temperature, cooling status, a brief reason for the current mode, fan speed, indoor humidity, and the 30-minute estimate. It omits the target, outdoor temperature, target gap, forecast high, and prediction footnote:

```yaml
type: custom:roommind-house-status-card
title: House cooling
compact: true
control_source_entity: select.magiqtouch_esp32_controller_control_source
```

The `control_source_entity` line is optional; on this MagIQcool setup it adds a warning if the wall panel takes control. Leave it out on other systems. To switch an existing full card to compact, add `compact: true` to its YAML; remove the line to return to the full layout.

The single 30-minute prediction follows RoomMind's planned operation: fresh-air fan, evaporative cooling, and rest periods as its normal rules switch between them. It uses the learned whole-house cooling model and estimates the fresh-air effect from sustained fan-only operation. Outdoor temperature, and outdoor humidity when supplied, are interpolated from the current readings to the configured hourly weather forecast. If a useful hourly forecast is unavailable, current outdoor conditions are held steady. While either cooling effect is still being learned, or while the controller is changing mode, the card shows “Learning…” instead of an unsupported number. Solar input, occupancy, and demand are held at their current values; the result is an estimate, not a target arrival time. The card refreshes RoomMind's state every minute and has no controls. If the previous layout remains after the resource URL changes, reload the dashboard in the browser or reset the Home Assistant Companion app's frontend cache.

## Analytics

![Analytics](docs/images/page-analytics.png)

Select a room and time range (24h / 7d / 30d / 90d / custom) to view temperature history, heating/cooling power, solar irradiance, and model predictions. Export as CSV or diagnostics report.

## How It Works

### Target Temperature Priority

```
Manual Override > Vacation > Presence Away > Schedule Block > Comfort / Eco  (+Mold Delta)
```

### Full Control vs. Managed Mode

An external temperature sensor is really where RoomMind starts to shine. It is the single most impactful addition for any room, unlocking the full potential of the thermal model, MPC optimization, and proportional device control.

| | Full Control | Managed Mode |
|---|---|---|
| **When** | External temperature sensor assigned | No external sensor |
| **How** | RoomMind decides heating/cooling/idle | Device self-regulates |
| **Setpoints** | Proportional boost (e.g. 28°C to force heating at 80% power) | Exact target sent to device |
| **Thermal model** | EKF learns room behavior, MPC optimizes | No learning, no optimization |

In **Full Control**, RoomMind dynamically calculates device setpoints based on MPC power output. Instead of sending 22°C to a TRV or AC, it might send 28°C to force the device to heat at full capacity. This solves common issues where devices with inaccurate internal sensors or built-in deadbands refuse to turn on. Each room shows its current mode ("Full Control" or "Managed") in the detail view.

### MPC Climate Control

The Extended Kalman Filter observes temperature changes and learns each room's heat loss rate, heating/cooling power, and solar responsiveness. Once calibrated (prediction accuracy < 0.5 C), the MPC optimizer plans ahead and calculates proportional power for smoother control.

Until calibrated (~60 idle + ~20 active samples), RoomMind falls back to simple on/off control with hysteresis.

For a more detailed explanation of the `Priority` slider, device types, setpoint modes, idle behavior, and smart source selection, see the [Control and Device Guide](docs/control-and-devices.md).

## Entities Created

| Entity | Description |
|--------|-------------|
| `sensor.roommind_{area_id}_target_temp` | Current target temperature |
| `sensor.roommind_{area_id}_mode` | Current mode: `idle`, `heating`, or `cooling` |
| `climate.roommind_{area_id}_override` | Manual override climate entity (controllable from dashboards, automations, voice) |
| `switch.roommind_vacation` | Global vacation mode toggle |
| `switch.roommind_{area_id}_cover_auto` | Per-room automatic cover control toggle |
| `binary_sensor.roommind_{area_id}_cover_paused` | On when manual cover override is detected |

These can be used in HA automations, dashboards, or other integrations.

## Troubleshooting

**MPC shows "learning" for a long time** - The model needs ~60 idle and ~20 heating/cooling observations. This can take a few days for rooms that heat rarely. Check progress in the Analytics tab.

**Room not heating/cooling when expected** - Check outdoor gating thresholds in Settings > Control. Default: no cooling below 16 C, no heating above 22 C.

**Whole-house cooler stays Off with humidity sensors configured** - Update the EKLabs fork to v0.8.17 or later in HACS and restart Home Assistant. Then check the whole-house status on the Rooms page for occupancy, humidity, outdoor-air, feedback, and heating interlocks. A satisfied cooling target also keeps the cooler off.

**Fresh-air fan stays Off below the outdoor limit** - In Auto mode, RoomMind normally requires outdoor air to be cooler than indoors. From v0.8.18, disable **Require cooler outside air** and set **Fresh-air indoor start temperature** to choose a separate indoor threshold. The outdoor temperature and humidity limits, home-presence gate, feedback checks, and heating interlock still apply. A temporary whole-house Cool override forces evaporative cooling and bypasses Auto's fresh-air choice; cancel that override to use automatic fan selection. Bringing in warmer outdoor air can raise the indoor temperature.

**Forecast pre-cooling or evaporative rest not behaving as expected** - Check the [whole-house cooling example](#whole-house-fan-and-evaporative-cooling-example) for each threshold and the Auto-only behavior. A missing hourly forecast disables pre-cooling. Setting **Maximum evaporative run** to zero disables timed rests.

**Thermal model seems wrong after room changes** - If you've changed insulation, radiators, or moved sensors, reset the model in Settings > Reset Thermal Data.

**Frontend not updating after update** - Hard-refresh: **Cmd+Shift+R** (Mac) or **Ctrl+Shift+R** (Windows/Linux).

## Requirements

- **Home Assistant** 2026.5+
- At least one HA area with a `climate.*` entity
- Optional: temperature sensor, humidity sensor, window sensors, weather entity, schedule helpers, person entities

No cloud services required - everything runs locally.

## Credits and Project Lineage

RoomMind was designed and built by [SnazzyBean](https://github.com/snazzybean). The original project's architecture, thermal modelling, MPC control, frontend, documentation, and the majority of this codebase come from [snazzybean/roommind](https://github.com/snazzybean/roommind). That work made this fork possible.

The EKLabs fork is maintained by [IsaacKirkwood](https://github.com/IsaacKirkwood) for whole-house HVAC experiments and a specific Home Assistant installation. Upstream remains the best destination for the original supported project. Consider [supporting the original author on Ko-fi](https://ko-fi.com/Y8Y31VP2VK).

### Development disclosure

EKLabs updates are vibe coded with AI coding agents under human direction. This includes design discussion, implementation, tests, documentation, and release preparation. Changes are reviewed with automated tests and targeted runtime checks, but AI assistance does not guarantee correctness. Climate control can affect comfort, energy use, and equipment operation, so review settings carefully, retain native equipment safeties, and avoid treating RoomMind as a safety system.

Contributions are welcome. Please identify whether a report concerns upstream RoomMind behavior or an EKLabs-only feature, and disclose materially AI-generated contributions so they can receive the appropriate review.

## Feedback & Contributing

- **EKLabs bug reports** - [Open an issue](https://github.com/IsaacKirkwood/roommind_eklabs/issues)
- **Feature requests and ideas** - [Start a discussion](https://github.com/IsaacKirkwood/roommind_eklabs/discussions)
- **Questions and usage help** - [Ask in Discussions](https://github.com/IsaacKirkwood/roommind_eklabs/discussions)
- **Releases** - [View EKLabs releases](https://github.com/IsaacKirkwood/roommind_eklabs/releases)
- **Upstream project** - [Visit the original RoomMind repository](https://github.com/snazzybean/roommind)
