import { LitElement, html, css } from "lit";
import { customElement, property } from "lit/decorators.js";
import type { HomeAssistant, WholeHouseAverage } from "../../types";
import { inputStyles } from "../../styles/input-styles";

@customElement("rme-settings-whole-house-average")
export class RmeSettingsWholeHouseAverage extends LitElement {
  @property({ attribute: false }) public hass!: HomeAssistant;
  @property({ attribute: false }) public average!: WholeHouseAverage;

  static styles = [
    inputStyles,
    css`
      .grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px 20px;
      }
      .wide {
        grid-column: 1 / -1;
      }
      .row {
        display: grid;
        grid-template-columns: minmax(0, 1fr) 120px auto;
        gap: 8px;
        align-items: center;
        min-height: 42px;
      }
      .entity-row {
        grid-template-columns: minmax(0, 1fr) auto;
      }
      .hint {
        color: var(--secondary-text-color);
        font-size: 12px;
        margin: 4px 0 12px;
      }
      ha-entity-picker,
      ha-textfield {
        width: 100%;
      }
      @media (max-width: 600px) {
        .grid {
          grid-template-columns: 1fr;
        }
        .wide {
          grid-column: auto;
        }
        .row {
          grid-template-columns: minmax(0, 1fr) 100px auto;
        }
      }
    `,
  ];

  render() {
    const a = this.average;
    return html`<div class="grid">
      <div class="wide">
        ${this._picker("Add temperature sensor", "temperature_sensors", ["sensor"])}
        <div class="hint">
          Valid readings are corrected, then averaged for all whole-house heating and cooling
          decisions.
        </div>
        ${a.temperature_sensors.map((id) => this._temperatureRow(id))}
      </div>
      <div class="wide">
        ${this._picker("Add humidity sensor", "humidity_sensors", ["sensor"])}
        <div class="hint">
          Valid corrected readings are averaged for evaporative-cooling decisions.
        </div>
        ${a.humidity_sensors.map((id) => this._humidityRow(id))}
      </div>
      ${this._picker("Add household member", "home_presence_entities", ["person"])}
      ${this._picker("Add downstairs presence sensor", "occupancy_entities", ["binary_sensor"])}
      ${this._picker("Add downstairs media player", "media_player_entities", ["media_player"])}
      <div class="hint">
        These shared inputs gate both central heating and cooling. Local room control remains
        independent.
      </div>
    </div>`;
  }

  private _picker(
    label: string,
    key:
      | "temperature_sensors"
      | "humidity_sensors"
      | "home_presence_entities"
      | "occupancy_entities"
      | "media_player_entities",
    domains: string[],
  ) {
    const entities = this.average[key] ?? [];
    return html`<div>
      <ha-entity-picker
        .hass=${this.hass}
        .value=${""}
        .includeDomains=${domains}
        label=${label}
        @value-changed=${(e: CustomEvent) => {
          const id = e.detail?.value;
          if (id) this._set(key, [...new Set([...entities, id])]);
        }}
      ></ha-entity-picker>
      ${
        key === "temperature_sensors" || key === "humidity_sensors"
          ? ""
          : entities.map(
              (id) =>
                html`<div class="row entity-row">
                  <span>${this.hass.states[id]?.attributes?.friendly_name ?? id}</span>
                  <ha-icon-button
                    label="Remove"
                    icon="mdi:close"
                    @click=${() =>
                      this._set(
                        key,
                        entities.filter((x) => x !== id),
                      )}
                  ></ha-icon-button>
                </div>`,
            )
      }
    </div>`;
  }

  private _temperatureRow(id: string) {
    const offset = this.average.temperature_offsets[id] ?? 0;
    return html`<div class="row">
      <span>${this.hass.states[id]?.attributes?.friendly_name ?? id}</span>
      <ha-textfield
        type="number"
        label="Correction"
        suffix="°C"
        min="-20"
        max="20"
        step="0.1"
        .value=${String(offset)}
        @change=${(e: Event) =>
          this._set("temperature_offsets", {
            ...this.average.temperature_offsets,
            [id]: Number((e.target as HTMLInputElement).value),
          })}
      ></ha-textfield>
      <ha-icon-button
        label="Remove"
        icon="mdi:close"
        @click=${() => this._removeTemperature(id)}
      ></ha-icon-button>
    </div>`;
  }

  private _removeTemperature(id: string) {
    const offsets = { ...this.average.temperature_offsets };
    delete offsets[id];
    this._fire({
      ...this.average,
      temperature_sensors: this.average.temperature_sensors.filter((value) => value !== id),
      temperature_offsets: offsets,
    });
  }

  private _humidityRow(id: string) {
    const offset = this.average.humidity_offsets[id] ?? 0;
    return html`<div class="row">
      <span>${this.hass.states[id]?.attributes?.friendly_name ?? id}</span>
      <ha-textfield
        type="number"
        label="Correction"
        suffix="%"
        min="-50"
        max="50"
        step="1"
        .value=${String(offset)}
        @change=${(e: Event) =>
          this._set("humidity_offsets", {
            ...this.average.humidity_offsets,
            [id]: Number((e.target as HTMLInputElement).value),
          })}
      ></ha-textfield>
      <ha-icon-button
        label="Remove"
        icon="mdi:close"
        @click=${() => this._removeHumidity(id)}
      ></ha-icon-button>
    </div>`;
  }

  private _removeHumidity(id: string) {
    const offsets = { ...this.average.humidity_offsets };
    delete offsets[id];
    this._fire({
      ...this.average,
      humidity_sensors: this.average.humidity_sensors.filter((value) => value !== id),
      humidity_offsets: offsets,
    });
  }

  private _set(key: keyof WholeHouseAverage, value: unknown) {
    this._fire({ ...this.average, [key]: value });
  }

  private _fire(value: WholeHouseAverage) {
    this.dispatchEvent(
      new CustomEvent("setting-changed", {
        detail: { key: "wholeHouseAverage", value },
        bubbles: true,
        composed: true,
      }),
    );
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "rme-settings-whole-house-average": RmeSettingsWholeHouseAverage;
  }
}
