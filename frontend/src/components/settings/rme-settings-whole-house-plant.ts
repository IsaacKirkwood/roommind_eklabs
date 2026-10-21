import { LitElement, html, css, nothing, type TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import type { HomeAssistant, WholeHousePlant } from "../../types";
import { inputStyles } from "../../styles/input-styles";
import "../shared/rme-toggle-row";

type PlantEntityList =
  "ventilation_request_entities" | "exhaust_ready_entities" | "outdoor_air_lockout_entities";

@customElement("rme-settings-whole-house-plant")
export class RmeSettingsWholeHousePlant extends LitElement {
  @property({ attribute: false }) public hass!: HomeAssistant;
  @property({ attribute: false }) public plant!: WholeHousePlant;

  static styles = [
    inputStyles,
    css`
      .sections {
        display: grid;
        gap: 24px;
      }
      .section {
        border-top: 1px solid var(--divider-color);
        padding-top: 18px;
      }
      .section:first-child {
        border-top: 0;
        padding-top: 0;
      }
      h3 {
        font-size: 15px;
        margin: 0 0 4px;
      }
      .intro,
      .hint {
        color: var(--secondary-text-color);
        font-size: 12px;
        line-height: 1.45;
      }
      .intro {
        margin: 0 0 14px;
      }
      .grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 14px 16px;
      }
      .wide {
        grid-column: 1 / -1;
      }
      .field {
        min-width: 0;
      }
      .hint {
        display: block;
        margin-top: 5px;
      }
      .entity {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 8px;
        align-items: center;
        min-height: 40px;
      }
      .entity-list {
        margin-top: 8px;
      }
      ha-entity-picker,
      ha-textfield {
        width: 100%;
      }
      @media (max-width: 700px) {
        .grid {
          grid-template-columns: 1fr;
        }
        .wide {
          grid-column: auto;
        }
      }
    `,
  ];

  render() {
    const p = this.plant;
    return html`<div class="sections">
      ${this._section(
        "System",
        "Connect the one-zone cooler and choose whether RoomMind may control it.",
        html`
          <div class="grid">
            ${this._toggle("Enable whole-house cooling", "Allows RoomMind to operate the configured cooler. Turning this off stops automatic control.", "enabled", p.enabled)}
            ${this._toggle("Enable MPC learning", "Learns the house cooling response and may start early to meet the target smoothly.", "mpc_enabled", p.mpc_enabled)}
            <div class="field wide">
              <ha-entity-picker
                .hass=${this.hass}
                .value=${p.entity_id}
                .includeDomains=${["climate"]}
                label="Whole-house cooler"
                @value-changed=${(e: CustomEvent) => this._set("entity_id", e.detail?.value ?? "")}
              ></ha-entity-picker>
              <span class="hint"
                >Select the MagIQtouch climate entity for the single whole-house zone.</span
              >
            </div>
          </div>
        `,
      )}
      ${this._section(
        "Automatic cooling",
        "Auto mode tries fresh outside air first. It switches to evaporative cooling when outside air is too warm or humid, provided evaporative conditions remain safe.",
        html`
          <div class="grid">
            ${this._number("Cooling target", "cooling_target", "°C", 16, 35, 0.5, "The whole-house temperature Auto mode aims to maintain.")}
            ${this._number("Start above target", "cooling_start_delta", "°C", 0.1, 5, 0.1, "Starts when measured or predicted temperature reaches target plus this amount.")}
            ${this._number("Stop above target", "cooling_stop_delta", "°C", 0, 5, 0.1, "May stop once measured temperature falls to target plus this amount.")}
            ${this._number("Fresh-air maximum outdoor temperature", "fresh_air_max_outdoor_temperature", "°C", 0, 40, 0.5, "Use fan-only cooling when outside is no warmer than this and is cooler than the house.")}
            ${this._number("Fresh-air maximum outdoor humidity", "fresh_air_max_outdoor_humidity", "%", 10, 100, 1, "Use fan-only cooling only when outdoor humidity is at or below this value.")}
          </div>
        `,
      )}
      ${this._section(
        "Evaporative limits",
        "These limits prevent ineffective cooling and excess indoor moisture. House temperature and humidity come from House averages.",
        html`
          <div class="grid">
            ${this._number("Minimum outdoor temperature", "minimum_outdoor_cooling_temp", "°C", 0, 40, 0.5, "Blocks evaporative cooling below this outdoor temperature.")}
            ${this._number("Maximum outdoor humidity", "evaporative_max_outdoor_humidity", "%", 10, 100, 1, "Blocks evaporative cooling when outside air is wetter than this limit.")}
            ${this._number("Maximum indoor humidity", "evaporative_max_indoor_humidity", "%", 30, 100, 1, "Stops evaporative cooling when the house reaches this humidity.")}
            ${this._number("Humidity restart margin", "evaporative_humidity_resume_delta", "%", 1, 20, 1, "Indoor humidity must fall this far below the limit before cooling restarts.")}
            ${this._number("Minimum evaporative advantage", "evaporative_min_indoor_outdoor_delta", "°C", 0, 15, 0.5, "Required difference between indoor temperature and estimated outdoor wet-bulb temperature.")}
          </div>
        `,
      )}
      ${this._section(
        "Run times & fan speed",
        "Minimum runs reduce rapid cycling. Cooling fan speed scales with demand; fresh air uses a fixed speed.",
        html`
          <div class="grid">
            ${this._number("Minimum evaporative run", "minimum_cooling_run_minutes", "min", 0, 120, 5, "Keep evaporative cooling running for at least this long unless a safety gate opens.")}
            ${this._number("Minimum fresh-air run", "minimum_ventilation_run_minutes", "min", 0, 120, 5, "Keep fan-only cooling running for at least this long unless a safety gate opens.")}
            ${this._number("Cooling minimum fan speed", "cooling_fan_min_speed", "/ 10", 1, 10, 1, "Lowest fan level for a small evaporative cooling demand.")}
            ${this._number("Cooling maximum fan speed", "cooling_fan_max_speed", "/ 10", 1, 10, 1, "Highest fan level used as cooling demand grows.")}
            ${this._number("Fresh-air fan speed", "ventilation_fan_speed", "/ 10", 1, 10, 1, "Fixed fan level for fan-only cooling and fresh-air requests.")}
            ${this._number("Maximum continuous run", "max_continuous_runtime_minutes", "min", 15, 720, 15, "Stops the plant after this continuous runtime and reports a fault.")}
          </div>
        `,
      )}
      ${this._section(
        "Occupancy & safety",
        "These gates apply to fresh-air and evaporative operation. Gas heating always interlocks the cooler.",
        html`
          <div class="grid">
            ${this._toggle("Require someone home", "Do not run when House averages reports nobody home.", "require_home_presence", p.require_home_presence)}
            ${this._toggle("Require downstairs occupancy", "Run only while a downstairs presence sensor or media player in House averages is active.", "require_occupancy", p.require_occupancy)}
            ${this._toggle("Require an open exhaust path", "Run only when a configured window, door, or helper confirms air can leave the house.", "require_exhaust_ready", p.require_exhaust_ready)}
            ${this._picker("Add exhaust-ready sensor", "exhaust_ready_entities", ["binary_sensor", "input_boolean"], "On or open means an exhaust path is ready.")}
            ${this._picker("Add outdoor-air lockout", "outdoor_air_lockout_entities", ["binary_sensor", "input_boolean"], "When on, blocks both fresh-air and evaporative operation.")}
            ${this._picker("Add fresh-air request", "ventilation_request_entities", ["binary_sensor", "input_boolean"], "When on, requests ventilation even without a cooling demand.")}
          </div>
        `,
      )}
      ${this._section(
        "Controller feedback",
        "RoomMind checks that the climate entity follows each command and stops safely if it does not.",
        html`
          <div class="grid">
            ${this._number("Command response timeout", "feedback_timeout_seconds", "sec", 30, 600, 10, "Time allowed for the controller to report the requested mode before a fault.")}
            ${this._number("Legacy stale threshold", "stale_after_seconds", "sec", 60, 1800, 30, "Retained for compatibility; availability and command feedback provide live safety checks.")}
          </div>
        `,
      )}
    </div>`;
  }

  private _section(title: string, intro: string, content: TemplateResult) {
    return html`<section class="section">
      <h3>${title}</h3>
      <p class="intro">${intro}</p>
      ${content}
    </section>`;
  }

  private _toggle(label: string, hint: string, key: keyof WholeHousePlant, checked: boolean) {
    return html`<rme-toggle-row
      .label=${label}
      .hint=${hint}
      .checked=${checked}
      @toggle-changed=${(e: CustomEvent) => this._set(key, e.detail)}
    ></rme-toggle-row>`;
  }

  private _number(
    label: string,
    key: keyof WholeHousePlant,
    suffix: string,
    min: number,
    max: number,
    step: number,
    hint: string,
  ) {
    return html`<div class="field">
      <ha-textfield
        type="number"
        label=${label}
        suffix=${suffix}
        min=${String(min)}
        max=${String(max)}
        step=${String(step)}
        .value=${String(this.plant[key])}
        @change=${(e: Event) => this._set(key, Number((e.target as HTMLInputElement).value))}
      ></ha-textfield
      ><span class="hint">${hint}</span>
    </div>`;
  }

  private _picker(label: string, key: PlantEntityList, domains: string[], hint: string) {
    const entities = this.plant[key] ?? [];
    return html`<div class="field">
      <ha-entity-picker
        .hass=${this.hass}
        .value=${""}
        .includeDomains=${domains}
        label=${label}
        @value-changed=${(e: CustomEvent) => {
          const id = e.detail?.value;
          if (!id || entities.includes(id)) return;
          this._set(key, [...entities, id]);
          (e.currentTarget as { value?: string }).value = "";
        }}
      ></ha-entity-picker>
      <span class="hint">${hint}</span>
      ${
        entities.length
          ? html`<div class="entity-list">
              ${entities.map(
                (id) =>
                  html`<div class="entity">
                    <span>${this.hass.states[id]?.attributes?.friendly_name ?? id}</span>
                    <ha-icon-button
                      label="Remove"
                      .path=${"M19,13H5V11H19V13Z"}
                      @click=${() =>
            this._set(
              key,
              entities.filter((entity) => entity !== id),
            )}
                    ></ha-icon-button>
                  </div>`,
              )}
            </div>`
          : nothing
      }
    </div>`;
  }

  private _set(key: keyof WholeHousePlant, value: unknown) {
    this.dispatchEvent(
      new CustomEvent("setting-changed", {
        detail: { key: "wholeHousePlant", value: { ...this.plant, [key]: value } },
        bubbles: true,
        composed: true,
      }),
    );
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "rme-settings-whole-house-plant": RmeSettingsWholeHousePlant;
  }
}
