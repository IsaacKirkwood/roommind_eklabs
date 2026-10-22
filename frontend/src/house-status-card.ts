/** A read-only Lovelace summary of RoomMind's whole-house cooler. */
import { LitElement, css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { HomeAssistant, WholeHousePlant } from "./types";

interface CardConfig {
  type: string;
  title?: string;
  control_source_entity?: string;
  compact?: boolean;
}

interface HouseResponse {
  whole_house_plant?: WholeHousePlant;
  outdoor_temp?: number | null;
  outdoor_humidity?: number | null;
}

const REFRESH_MS = 60_000;

function temperature(value: number | null | undefined): string {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(1) : "–";
}

function temperatureWithUnit(value: number | null | undefined): string {
  return typeof value === "number" && Number.isFinite(value) ? `${value.toFixed(1)}°C` : "–";
}

function explanation(reason: string | undefined): string {
  if (!reason) return "RoomMind is checking the house conditions.";
  const plain = reason.split("; waiting for controller")[0];
  const known: Record<string, string> = {
    "fresh air preferred for cooling": "RoomMind is using fresh air instead of the evaporative cooler under the configured outdoor limits.",
    "evaporative cooling demand": "The house is warm, so evaporative cooling is running.",
    "cooling selected": "Evaporative cooling was selected in RoomMind.",
    "fresh air selected": "Fresh air was selected in RoomMind.",
    "cooling target satisfied": "The house has reached its cooling target.",
    "minimum cooling run": "The cooler is completing its minimum run.",
    "minimum fresh-air run": "The fresh-air fan is completing its minimum run.",
    "evaporative rest; fresh air preferred": "The cooler is resting while the fan brings in cooler outdoor air.",
    "evaporative run limit; fresh air preferred": "The cooler has finished its run and fresh air is taking over.",
    "evaporative run limit; resting": "The cooler is taking a scheduled break.",
    "forecast pre-cooling before hot peak": "RoomMind started cooling early because a hot afternoon is forecast.",
    "occupancy gate clear": "Cooling is paused because the house is not marked occupied.",
    "heating interlock": "Cooling is paused while heating is active.",
    "open an exhaust path": "Cooling is waiting for an open path for air to leave the house.",
    "outdoor air quality lockout": "Cooling is paused because outdoor air quality is poor.",
    "manually off": "Whole-house cooling is turned off in RoomMind.",
    "maximum runtime exceeded": "Cooling has paused after reaching its maximum run time.",
    "waiting for temperature data": "Cooling is waiting for a valid house or outdoor temperature.",
  };
  return known[plain] ?? plain.charAt(0).toUpperCase() + plain.slice(1);
}

@customElement("roommind-house-status-card")
export class RoomMindHouseStatusCard extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistant;
  @state() private _config: CardConfig = { type: "custom:roommind-house-status-card" };
  @state() private _house?: HouseResponse;
  @state() private _error = "";
  @state() private _updatedAt = 0;
  private _timer?: number;
  private _loading = false;

  setConfig(config: CardConfig): void {
    this._config = { ...config };
  }

  getCardSize(): number {
    return this._config.compact ? 2 : 4;
  }

  getGridOptions(): { columns: number; rows: string } {
    return { columns: 12, rows: "auto" };
  }

  connectedCallback(): void {
    super.connectedCallback();
    this._timer = window.setInterval(() => void this._refresh(), REFRESH_MS);
    void this._refresh();
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    if (this._timer !== undefined) window.clearInterval(this._timer);
    this._timer = undefined;
  }

  protected updated(changed: Map<PropertyKey, unknown>): void {
    if (changed.has("hass") && this.hass && !this._house) void this._refresh();
  }

  private async _refresh(): Promise<void> {
    if (!this.hass || this._loading || !this.isConnected) return;
    this._loading = true;
    try {
      this._house = await this.hass.callWS<HouseResponse>({ type: "roommind_eklabs/rooms/list" });
      this._updatedAt = Date.now();
      this._error = "";
    } catch {
      this._error = "RoomMind status is unavailable. The card will try again shortly.";
    } finally {
      this._loading = false;
    }
  }

  private _modeLabel(plant: WholeHousePlant): string {
    const live = plant.live;
    if (!plant.enabled) return "RoomMind cooling is off";
    if (live?.command_pending) return "Waiting for the cooler";
    if (live?.mode === "cool") return "Evaporative cooling";
    if (live?.mode === "fan_only") return "Fresh-air cooling";
    return "Cooling is resting";
  }

  private _sourceWarning(): string | null {
    const entityId = this._config.control_source_entity;
    if (!entityId || !this.hass) return null;
    const source = this.hass.states[entityId]?.state;
    if (!source || source === "unavailable" || source === "unknown") return "Controller source is unavailable.";
    return source === "Home Assistant" ? null : `${source} is in control. RoomMind cannot change the cooler right now.`;
  }

  render() {
    const plant = this._house?.whole_house_plant;
    const live = plant?.live;
    const current = live?.current_temperature;
    const target = live?.target_temperature ?? plant?.cooling_target;
    const delta = typeof current === "number" && typeof target === "number" ? current - target : null;
    const predicted = live?.operating_predicted_temperature;
    const sourceWarning = this._sourceWarning();
    const status = plant ? this._modeLabel(plant) : "Waiting for RoomMind";
    const accent = live?.fault || sourceWarning ? "warning" : live?.mode === "cool" ? "cool" : live?.mode === "fan_only" ? "fan" : "idle";
    const unit = "°C"; // RoomMind's whole-house model and cooling settings use Celsius.

    if (this._config.compact) {
      return html`
        <ha-card>
          <div class="card compact ${accent}">
            <div class="compact-header">
              <h2>${this._config.title || "House cooling"}</h2>
              <span class="status"><span class="status-dot"></span>${status}</span>
            </div>
            <div class="compact-main">
              <div class="compact-temperature">
                <div><span class="number">${temperature(current)}</span><span class="unit">${unit}</span></div>
                <span class="caption">Inside now</span>
              </div>
              <div class="compact-readings">
                <div class="compact-prediction">
                  <span>In 30 min with RoomMind</span>
                  <strong>${typeof predicted === "number" ? temperatureWithUnit(predicted) : "Learning…"}</strong>
                </div>
                <div class="compact-fan">Fan ${typeof live?.fan_speed === "number" ? `${live.fan_speed} / 10` : live?.mode === "off" ? "off" : "–"}</div>
              </div>
            </div>
            ${this._error ? html`<p class="notice" role="status">${this._error}</p>` : nothing}
            ${sourceWarning ? html`<p class="notice" role="status">${sourceWarning}</p>` : nothing}
            ${live?.fault ? html`<p class="notice" role="status">${explanation(live.fault)}</p>` : nothing}
          </div>
        </ha-card>
      `;
    }

    return html`
      <ha-card>
        <div class="card ${accent}">
          <div class="header">
            <div>
              <div class="eyebrow">ROOMMIND · WHOLE HOUSE</div>
              <h2>${this._config.title || "House cooling"}</h2>
            </div>
            <span class="status"><span class="status-dot"></span>${status}</span>
          </div>

          ${this._error ? html`<p class="notice" role="status">${this._error}</p>` : nothing}
          ${sourceWarning ? html`<p class="notice" role="status">${sourceWarning}</p>` : nothing}
          ${live?.fault ? html`<p class="notice" role="status">${explanation(live.fault)}</p>` : nothing}

          <div class="temperatures">
            <div class="hero"><span class="number">${temperature(current)}</span><span class="unit">${unit}</span><span class="caption">Inside now</span></div>
            <div class="comparison">
              <div><span>Cooling target</span><strong>${temperatureWithUnit(target)}</strong></div>
              <div><span>Outside now</span><strong>${temperatureWithUnit(this._house?.outdoor_temp)}</strong></div>
              ${typeof delta === "number" ? html`<div><span>From target</span><strong>${delta > 0 ? "+" : ""}${delta.toFixed(1)}${unit}</strong></div>` : nothing}
            </div>
          </div>

          <div class="decision">
            <ha-icon icon=${live?.mode === "cool" ? "mdi:snowflake" : live?.mode === "fan_only" ? "mdi:weather-windy" : "mdi:home-thermometer-outline"}></ha-icon>
            <p>${plant?.enabled ? explanation(live?.reason) : "Whole-house cooling is not enabled in RoomMind."}</p>
          </div>

          <div class="details">
            <div><span class="detail-label">Fan</span><strong>${typeof live?.fan_speed === "number" ? `${live.fan_speed} / 10` : live?.mode === "off" ? "Off" : "–"}</strong></div>
            <div><span class="detail-label">Humidity</span><strong>${typeof live?.current_humidity === "number" ? `${Math.round(live.current_humidity)}%` : "–"}</strong></div>
            <div><span class="detail-label">High ahead</span><strong>${temperatureWithUnit(live?.forecast_high_temperature)}</strong></div>
          </div>

          <div class="outlook">
            <div class="outlook-icon"><ha-icon icon="mdi:chart-line"></ha-icon></div>
            <div>
              <div class="outlook-title">What the model predicts</div>
              ${typeof predicted === "number"
                ? html`<div class="outlook-value">With RoomMind running: about <strong>${temperature(predicted)}${unit}</strong> in 30 minutes.</div>`
                : html`<div class="outlook-value">RoomMind is still learning the cooling effect, or waiting for the controller.</div>`}
              <div class="outlook-note">Follows planned fresh-air, evaporative and rest periods at today's outdoor conditions. Actual temperature may differ.</div>
            </div>
          </div>
          <div class="footer">${this._updatedAt ? `Updated ${new Date(this._updatedAt).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}` : "Waiting for an update"} · View only</div>
        </div>
      </ha-card>
    `;
  }

  static styles = css`
    :host { display: block; }
    ha-card { overflow: hidden; border-radius: var(--ha-card-border-radius, 18px); }
    .card { --accent: #728397; padding: 22px; color: var(--primary-text-color); background: var(--ha-card-background, var(--card-background-color, #fff)); }
    .card.cool { --accent: #2189ce; }
    .card.fan { --accent: #20a38c; }
    .card.warning { --accent: #d68b22; }
    .header { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
    .eyebrow { color: var(--secondary-text-color); font-size: 10px; font-weight: 700; letter-spacing: .14em; }
    h2 { margin: 4px 0 0; font-size: 21px; line-height: 1.2; }
    .status { display: inline-flex; align-items: center; gap: 7px; flex: 0 0 auto; max-width: 48%; padding: 7px 10px; border-radius: 999px; background: color-mix(in srgb, var(--accent) 12%, transparent); color: var(--accent); font-size: 12px; font-weight: 700; line-height: 1.2; }
    .status-dot { width: 7px; height: 7px; border-radius: 50%; background: currentColor; flex: 0 0 auto; }
    .notice { margin: 16px 0 0; padding: 10px 12px; border-radius: 9px; background: color-mix(in srgb, #d68b22 14%, transparent); color: var(--primary-text-color); font-size: 13px; }
    .temperatures { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 18px; align-items: end; margin-top: 23px; }
    .hero { display: grid; grid-template-columns: max-content max-content; align-items: start; column-gap: 5px; }
    .number { font-size: clamp(48px, 10vw, 66px); font-weight: 650; letter-spacing: -.07em; line-height: 1; }
    .unit { font-size: 22px; font-weight: 600; margin-top: 6px; }
    .caption { grid-column: 1 / -1; margin-top: 5px; color: var(--secondary-text-color); font-size: 12px; }
    .comparison { display: grid; gap: 7px; min-width: 0; }
    .comparison div { display: flex; justify-content: space-between; gap: 8px; border-bottom: 1px solid var(--divider-color); padding-bottom: 5px; font-size: 12px; }
    .comparison span { color: var(--secondary-text-color); }
    .comparison strong { font-size: 13px; white-space: nowrap; }
    .decision { display: flex; align-items: flex-start; gap: 10px; margin-top: 20px; padding: 14px; border-radius: 11px; background: color-mix(in srgb, var(--accent) 9%, transparent); }
    .decision ha-icon { color: var(--accent); --mdc-icon-size: 21px; flex: 0 0 auto; }
    .decision p { margin: 0; font-size: 13px; line-height: 1.45; }
    .details { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; margin-top: 18px; }
    .details > div { display: grid; gap: 2px; min-width: 0; }
    .detail-label { color: var(--secondary-text-color); font-size: 11px; }
    .details strong { font-size: 14px; }
    .outlook { display: flex; gap: 11px; align-items: flex-start; border-top: 1px solid var(--divider-color); margin-top: 20px; padding-top: 18px; }
    .outlook-icon { display: grid; place-items: center; width: 32px; height: 32px; flex: 0 0 auto; border-radius: 9px; color: var(--accent); background: color-mix(in srgb, var(--accent) 10%, transparent); }
    .outlook-icon ha-icon { --mdc-icon-size: 19px; }
    .outlook-title { font-size: 13px; font-weight: 700; }
    .outlook-value { margin-top: 3px; font-size: 14px; }
    .outlook-note { margin-top: 5px; color: var(--secondary-text-color); font-size: 11px; line-height: 1.35; }
    .footer { margin-top: 18px; color: var(--secondary-text-color); font-size: 10px; text-align: right; }
    .compact { padding: 16px 18px; }
    .compact-header { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px 12px; }
    .compact-header h2 { margin: 0; font-size: 16px; }
    .compact .status { max-width: 100%; padding: 5px 8px; font-size: 11px; }
    .compact-main { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 13px; }
    .compact-temperature { min-width: 0; }
    .compact-temperature > div { display: flex; align-items: flex-start; white-space: nowrap; }
    .compact .number { font-size: 43px; }
    .compact .unit { font-size: 15px; margin-top: 3px; }
    .compact .caption { display: block; margin-top: 2px; font-size: 11px; }
    .compact-readings { display: grid; justify-items: end; gap: 7px; min-width: 0; text-align: right; }
    .compact-prediction { display: grid; gap: 2px; }
    .compact-prediction span { color: var(--secondary-text-color); font-size: 10px; line-height: 1.2; }
    .compact-prediction strong { font-size: 16px; line-height: 1.15; }
    .compact-fan { color: var(--secondary-text-color); font-size: 11px; }
    .compact .notice { margin-top: 12px; font-size: 11px; }
    @media (max-width: 420px) { .card { padding: 18px; } .header { flex-wrap: wrap; } .status { max-width: 100%; } .temperatures { grid-template-columns: 1fr; gap: 18px; } .number { font-size: 56px; } .card.compact { padding: 16px; } .compact .number { font-size: 40px; } }
  `;
}

declare global {
  interface Window {
    customCards?: Array<{ type: string; name: string; description: string; preview: boolean }>;
  }
}

window.customCards = window.customCards || [];
window.customCards.push({
  type: "roommind-house-status-card",
  name: "RoomMind House Status",
  description: "A simple, read-only view of whole-house cooling and its prediction.",
  preview: false,
});
