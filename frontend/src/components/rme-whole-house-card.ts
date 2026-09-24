import { LitElement, html, css, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import type { HomeAssistant, SharedHeatSource, WholeHousePlant } from "../types";
import { inputStyles } from "../styles/input-styles";

@customElement("rme-whole-house-card")
export class RmeWholeHouseCard extends LitElement {
  @property({ attribute: false }) public hass!: HomeAssistant;
  @property({ attribute: false }) public source!: SharedHeatSource;
  @property({ attribute: false }) public plant?: WholeHousePlant;

  static styles = [
    inputStyles,
    css`
      ha-card {
        padding: 18px;
        border-radius: 8px;
      }
      .top,
      .temperatures,
      .mode {
        display: flex;
        align-items: center;
      }
      .top {
        justify-content: space-between;
        gap: 16px;
      }
      .identity {
        display: flex;
        align-items: center;
        gap: 12px;
        min-width: 0;
      }
      .identity ha-icon {
        color: var(--warning-color, #ff9800);
        --mdc-icon-size: 28px;
      }
      h3 {
        margin: 0;
        font-size: 18px;
        letter-spacing: 0;
      }
      .status {
        color: var(--secondary-text-color);
        font-size: 13px;
        margin-top: 3px;
      }
      .current {
        font-size: 28px;
        white-space: nowrap;
      }
      .current small {
        color: var(--secondary-text-color);
        font-size: 14px;
      }
      .body {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 20px;
        margin-top: 18px;
      }
      .plant-section {
        min-width: 0;
      }
      .plant-section + .plant-section {
        border-left: 1px solid var(--divider-color);
        padding-left: 20px;
      }
      .section-heading {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 10px;
      }
      .section-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        font-weight: 600;
      }
      .section-title ha-icon {
        --mdc-icon-size: 19px;
      }
      .plant-status {
        color: var(--secondary-text-color);
        font-size: 12px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .mode {
        gap: 8px;
      }
      .mode button {
        border: 1px solid var(--divider-color);
        background: transparent;
        color: var(--primary-text-color);
        min-height: 40px;
        padding: 0 16px;
        cursor: pointer;
        font: inherit;
      }
      .mode button:first-child {
        border-radius: 6px 0 0 6px;
      }
      .mode button:last-child {
        border-radius: 0 6px 6px 0;
        margin-left: -9px;
      }
      .cooling-controls {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 12px;
        align-items: center;
      }
      .cooling-controls .mode {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0;
      }
      .cooling-controls .mode button {
        padding: 0 10px;
        margin-left: -1px;
      }
      .cooling-controls .mode button:first-child {
        margin-left: 0;
      }
      .cooling-controls .mode button:last-child {
        margin-left: -1px;
      }
      .mode button[active] {
        background: var(--primary-color);
        color: var(--text-primary-color, white);
        border-color: var(--primary-color);
      }
      .temperatures {
        gap: 12px;
      }
      ha-textfield {
        width: 100%;
      }
      .off {
        opacity: 0.65;
      }
      @media (max-width: 700px) {
        .body {
          grid-template-columns: 1fr;
        }
        .plant-section + .plant-section {
          border-left: 0;
          border-top: 1px solid var(--divider-color);
          padding-left: 0;
          padding-top: 18px;
        }
        .temperatures {
          align-items: stretch;
        }
      }
    `,
  ];

  render() {
    if (!this.source) return nothing;
    const live = this.source.live;
    const current = live?.current_temperature;
    const enabled = this.source.thermostat_enabled ?? true;
    const scheduleConfigured = Boolean(this.source.schedule_entity);
    const scheduled = scheduleConfigured && live?.schedule_active != null;
    const effectivePreset = live?.preset_mode ?? this.source.preset_mode ?? "comfort";
    const plant = this.plant;
    const plantLive = plant?.live;
    const plantEnabled = plant?.enabled ?? false;
    const plantMode = plantEnabled ? (plant?.operating_mode ?? "auto") : "off";
    const houseTemperature =
      typeof plantLive?.current_temperature === "number" ? plantLive.current_temperature : current;
    const overallStatus = live?.active
      ? "Gas heating"
      : plantLive?.mode === "cool"
        ? "Evaporative cooling"
        : plantLive?.mode === "fan_only"
          ? "Fresh air"
          : "Ready";
    const mpcActive = Boolean(
      live?.mpc_active || plantLive?.mpc_heating_active || plantLive?.mpc_cooling_active,
    );
    const mpcStatus = !plant?.mpc_enabled
      ? "MPC off"
      : mpcActive
        ? "MPC active"
        : `MPC learning ${Math.round((plantLive?.mpc_confidence ?? live?.mpc_confidence ?? 0) * 100)}%`;
    return html`
      <ha-card class=${enabled || plantEnabled ? "" : "off"}>
        <div class="top">
          <div class="identity">
            <ha-icon icon="mdi:home-thermometer"></ha-icon>
            <div>
              <h3>Whole House</h3>
              <div class="status">
                ${overallStatus} · ${mpcStatus}
                ${typeof plantLive?.current_humidity === "number" ? ` · ${plantLive.current_humidity.toFixed(0)}% RH` : ""}
                ${
                  scheduled
                    ? ` · Schedule ${effectivePreset === "eco" ? "Eco" : "Comfort"}`
                    : scheduleConfigured
                      ? ` · Schedule unavailable · Manual ${effectivePreset === "eco" ? "Eco" : "Comfort"}`
                      : ""
                }
              </div>
            </div>
          </div>
          <div class="current">
            ${typeof houseTemperature === "number" ? houseTemperature.toFixed(1) : "--"}<small>
              °C</small
            >
          </div>
        </div>
        <div class="body">
          <div class="plant-section">
            <div class="section-heading">
              <div class="section-title"><ha-icon icon="mdi:radiator"></ha-icon> Heating</div>
              <div class="plant-status">${enabled ? live?.reason || "Ready" : "Off"}</div>
            </div>
            <div class="mode">
              <button
                ?active=${enabled && effectivePreset !== "eco"}
                ?disabled=${scheduled}
                @click=${() => this._mode("comfort")}
              >
                Comfort
              </button>
              <button
                ?active=${enabled && effectivePreset === "eco"}
                ?disabled=${scheduled}
                @click=${() => this._mode("eco")}
              >
                Eco
              </button>
              <ha-icon-button
                label=${enabled ? "Turn whole-house heating off" : "Turn whole-house heating on"}
                icon=${enabled ? "mdi:power" : "mdi:power-off"}
                @click=${() => this._change({ thermostat_enabled: !enabled })}
              ></ha-icon-button>
            </div>
            <div class="temperatures">
              <ha-textfield
                type="number"
                min="5"
                max="30"
                step="0.5"
                label="Comfort"
                suffix="°C"
                .value=${String(this.source.comfort_temperature ?? this.source.target_temperature ?? 18)}
                @change=${(e: Event) => this._temperature("comfort_temperature", e)}
              ></ha-textfield>
              <ha-textfield
                type="number"
                min="5"
                max="30"
                step="0.5"
                label="Eco"
                suffix="°C"
                .value=${String(this.source.eco_temperature ?? 16)}
                @change=${(e: Event) => this._temperature("eco_temperature", e)}
              ></ha-textfield>
            </div>
          </div>
          <div class="plant-section">
            <div class="section-heading">
              <div class="section-title">
                <ha-icon icon="mdi:weather-windy"></ha-icon> Cooling & fresh air
              </div>
              <div class="plant-status">
                ${plantLive?.fault || plantLive?.reason || "Not configured"}
                ${
                  typeof plantLive?.fan_speed === "number"
                    ? html` · Fan ${plantLive.fan_speed}/10`
                    : nothing
                }
              </div>
            </div>
            <div class="cooling-controls">
              <div class="mode">
                <button
                  ?active=${plantMode === "auto"}
                  ?disabled=${!plant?.entity_id}
                  @click=${() => this._plantMode("auto")}
                >
                  Auto
                </button>
                <button
                  ?active=${plantMode === "cool"}
                  ?disabled=${!plant?.entity_id}
                  @click=${() => this._plantMode("cool")}
                >
                  Cool
                </button>
                <button
                  ?active=${plantMode === "fan_only"}
                  ?disabled=${!plant?.entity_id}
                  @click=${() => this._plantMode("fan_only")}
                >
                  Fresh
                </button>
                <button
                  ?active=${plantMode === "off"}
                  ?disabled=${!plant?.entity_id}
                  @click=${() => this._plantMode("off")}
                >
                  Off
                </button>
              </div>
              <ha-textfield
                type="number"
                min="16"
                max="35"
                step="0.5"
                label="Cool to"
                suffix="°C"
                .value=${String(plant?.cooling_target ?? 24)}
                ?disabled=${!plant?.entity_id}
                @change=${this._coolingTarget}
              ></ha-textfield>
            </div>
          </div>
        </div>
      </ha-card>
    `;
  }

  private _mode(preset_mode: "comfort" | "eco") {
    this._change({ preset_mode, thermostat_enabled: true });
  }

  private _temperature(field: "comfort_temperature" | "eco_temperature", event: Event) {
    const value = Number((event.target as HTMLInputElement).value);
    if (Number.isFinite(value)) this._change({ [field]: value });
  }

  private _change(changes: Partial<SharedHeatSource>) {
    this.dispatchEvent(
      new CustomEvent("whole-house-changed", {
        detail: { source: { ...this.source, ...changes } },
        bubbles: true,
        composed: true,
      }),
    );
  }

  private _plantMode(operating_mode: WholeHousePlant["operating_mode"]) {
    if (!this.plant) return;
    this._changePlant({ operating_mode, enabled: operating_mode !== "off" });
  }

  private _coolingTarget(event: Event) {
    const cooling_target = Number((event.target as HTMLInputElement).value);
    if (Number.isFinite(cooling_target)) this._changePlant({ cooling_target });
  }

  private _changePlant(changes: Partial<WholeHousePlant>) {
    if (!this.plant) return;
    this.dispatchEvent(
      new CustomEvent("whole-house-plant-changed", {
        detail: { plant: { ...this.plant, ...changes } },
        bubbles: true,
        composed: true,
      }),
    );
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "rme-whole-house-card": RmeWholeHouseCard;
  }
}
