import { useEffect, useState } from 'react'
import './App.css'

const DEMAND_LIMIT = 160
const CRITICAL_LIMIT = 200

// Preview data for the first dashboard implementation.
// We will replace this with actual Flask API responses later.
// Preview data for the first dashboard implementation.
// We will replace this with actual Flask API responses later.
const API_BASE_URL = 'http://127.0.0.1:5000'
const formatHour = (hour) =>
  `${String(hour).padStart(2, '0')}:00`

function getGridDecision(demand, hour) {
  const isEvening = hour >= 18 && hour <= 22

  const gridMode =
    demand > DEMAND_LIMIT || isEvening
      ? 'Renewable Storage Mode'
      : 'Main Grid Mode'

  const criticalAlert = demand >= CRITICAL_LIMIT

  let explanation

  if (criticalAlert) {
    explanation =
      `Demand is ${demand} kW, meeting or exceeding the ` +
      `${CRITICAL_LIMIT} kW critical threshold.`
  } else if (demand > DEMAND_LIMIT) {
    explanation =
      `Demand is above ${DEMAND_LIMIT} kW, so storage mode is required.`
  } else if (isEvening) {
    explanation =
      'The evening operating window requires renewable storage mode.'
  } else {
    explanation =
      `Demand is at or below ${DEMAND_LIMIT} kW and outside the evening window.`
  }

  return {
    gridMode,
    criticalAlert,
    explanation,
  }
}

function EnergyClock({ forecast, selectedHour, onSelectHour }) {
  const center = 180
  const innerRadius = 77
  const outerRadius = 143

  function pointOnCircle(radius, angle) {
    return {
      x: center + radius * Math.cos(angle),
      y: center + radius * Math.sin(angle),
    }
  }

  function createSegmentPath(hour, demand) {
    const startAngle = (hour / 24) * Math.PI * 2 - Math.PI / 2
    const endAngle =
      ((hour + 0.72) / 24) * Math.PI * 2 - Math.PI / 2

    const normalizedDemand = Math.min(
      Math.max(demand / 240, 0.2),
      1,
    )

    const radius =
      innerRadius +
      normalizedDemand * (outerRadius - innerRadius)

    const start = pointOnCircle(innerRadius, startAngle)
    const outerStart = pointOnCircle(radius, startAngle)
    const outerEnd = pointOnCircle(radius, endAngle)
    const end = pointOnCircle(innerRadius, endAngle)

    return [
      `M ${start.x} ${start.y}`,
      `L ${outerStart.x} ${outerStart.y}`,
      `A ${radius} ${radius} 0 0 1 ${outerEnd.x} ${outerEnd.y}`,
      `L ${end.x} ${end.y}`,
      `A ${innerRadius} ${innerRadius} 0 0 0 ${start.x} ${start.y}`,
      'Z',
    ].join(' ')
  }

  function segmentColor(demand, hour) {
    if (demand >= CRITICAL_LIMIT) return '#FF2E63'

    if (demand > DEMAND_LIMIT || (hour >= 18 && hour <= 22)) {
      return '#FFB020'
    }

    return '#B79CFF'
  }

  const selectedDemand = forecast[selectedHour]
  const selectedDecision = getGridDecision(
    selectedDemand,
    selectedHour,
  )

  return (
    <section className="panel energy-panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">24-HOUR PREDICTION</span>
          <h2>The Energy Clock</h2>
        </div>

        <span className="preview-badge">
          <span className="status-dot" />
          PREVIEW
        </span>
      </div>

      <div className="clock-layout">
        <div className="energy-clock">
          <svg
            viewBox="0 0 360 360"
            role="img"
            aria-label="Interactive 24-hour energy demand clock"
          >
            <defs>
              <filter
                id="clock-glow"
                x="-100%"
                y="-100%"
                width="300%"
                height="300%"
              >
                <feGaussianBlur stdDeviation="3" />
              </filter>
            </defs>

            <circle
              cx={center}
              cy={center}
              r={outerRadius + 7}
              fill="none"
              stroke="#FFFFFF"
              strokeOpacity="0.05"
              strokeWidth="1"
            />

            <circle
              cx={center}
              cy={center}
              r={innerRadius - 8}
              fill="none"
              stroke="#B79CFF"
              strokeOpacity="0.25"
              strokeDasharray="3 6"
            />

            {forecast.map((demand, hour) => {
              const isSelected = selectedHour === hour
              const color = segmentColor(demand, hour)

              return (
                <g key={hour}>
                  {isSelected && (
                    <path
                      d={createSegmentPath(hour, demand)}
                      fill={color}
                      opacity="0.5"
                      filter="url(#clock-glow)"
                    />
                  )}

                  <path
                    d={createSegmentPath(hour, demand)}
                    fill={color}
                    opacity={isSelected ? 1 : 0.72}
                    stroke={isSelected ? '#F4E9D8' : '#211A29'}
                    strokeWidth={isSelected ? 2 : 1}
                    className={
                      demand >= CRITICAL_LIMIT
                        ? 'clock-segment critical-segment'
                        : 'clock-segment'
                    }
                    role="button"
                    tabIndex="0"
                    aria-label={`${formatHour(hour)}, ${demand} kilowatts`}
                    aria-pressed={isSelected}
                    onClick={() => onSelectHour(hour)}
                    onKeyDown={(event) => {
                      if (
                        event.key === 'Enter' ||
                        event.key === ' '
                      ) {
                        event.preventDefault()
                        onSelectHour(hour)
                      }
                    }}
                  />
                </g>
              )
            })}

            <circle
              cx={center}
              cy={center}
              r={innerRadius - 15}
              fill="#1F1826"
              stroke="#FFFFFF"
              strokeOpacity="0.07"
            />

            <text
              x={center}
              y={center - 28}
              textAnchor="middle"
              className="clock-caption"
            >
              SELECTED HOUR
            </text>

            <text
              x={center}
              y={center + 2}
              textAnchor="middle"
              className="clock-hour"
            >
              {formatHour(selectedHour)}
            </text>

            <text
              x={center}
              y={center + 27}
              textAnchor="middle"
              className="clock-demand"
            >
              {selectedDemand} kW
            </text>

            <text
              x={center}
              y={center + 48}
              textAnchor="middle"
              className="clock-caption"
            >
              DEMAND
            </text>
          </svg>
        </div>

        <div className="clock-details">
          <span className="eyebrow">SELECTED DECISION</span>

          <div
            className={`mode-indicator ${
              selectedDecision.gridMode === 'Main Grid Mode'
                ? 'mode-main'
                : 'mode-storage'
            }`}
          >
            <span className="mode-indicator-dot" />

            <span>{selectedDecision.gridMode}</span>
          </div>

          <div className="detail-divider" />

          <div className="detail-row">
            <span>Predicted demand</span>
            <strong>{selectedDemand} kW</strong>
          </div>

          <div className="detail-row">
            <span>Storage threshold</span>
            <strong>{DEMAND_LIMIT} kW</strong>
          </div>

          <div className="detail-row">
            <span>Critical threshold</span>
            <strong className="critical-text">
              {CRITICAL_LIMIT} kW
            </strong>
          </div>

          <div className="explanation-box">
            <span className="explanation-label">
              WHY THIS DECISION?
            </span>

            <p>{selectedDecision.explanation}</p>
          </div>
        </div>
      </div>

      <div className="clock-legend">
        <span>
          <i className="legend-dot lavender-dot" />
          Main Grid
        </span>

        <span>
          <i className="legend-dot amber-dot" />
          Renewable Storage
        </span>

        <span>
          <i className="legend-dot coral-dot" />
          Critical Demand
        </span>
      </div>
    </section>
  )
}

function BatteryCell() {
  return (
    <section className="panel battery-panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">ENERGY RESERVE</span>
          <h2>Battery Cell</h2>
        </div>

        <span className="simulation-label">SIMULATED</span>
      </div>

      <div className="battery-content">
        <div className="battery-visual">
          <div className="battery-terminal" />

          <div className="battery-shell">
            <div className="battery-fill">
              <span className="battery-light light-one" />
              <span className="battery-light light-two" />
              <span className="battery-light light-three" />
            </div>
          </div>
        </div>

        <div className="battery-reading">
          <strong>72<span>%</span></strong>
          <span>Illustrative charge</span>
        </div>
      </div>

      <div className="battery-meter">
        <span />
      </div>

      <div className="battery-footer">
        <span>Reserve status</span>
        <strong>Simulation only</strong>
      </div>

      <p className="muted-note">
        Actual battery telemetry is not available in the supplied dataset.
      </p>
    </section>
  )
}

function OverloadRadar({ forecast, onSelectHour }) {
  const overloads = forecast
    .map((demand, hour) => ({ demand, hour }))
    .filter(({ demand }) => demand >= CRITICAL_LIMIT)
    .sort((a, b) => b.demand - a.demand)

  return (
    <section className="panel radar-panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">THRESHOLD MONITOR</span>
          <h2>Overload Radar</h2>
        </div>

        <span className="alert-count">
          {overloads.length} EVENTS
        </span>
      </div>

      <div className="radar-summary">
        <div className="radar-icon">!</div>

        <div>
          <strong>{overloads.length} critical hours</strong>
          <p>Preview demand at or above 200 kW</p>
        </div>
      </div>

      <div className="overload-list">
        {overloads.length === 0 ? (
          <div className="empty-alerts">
            No critical demand in this preview.
          </div>
        ) : (
          overloads.slice(0, 4).map(({ hour, demand }) => (
            <button
              className="overload-item"
              key={hour}
              onClick={() => onSelectHour(hour)}
              type="button"
            >
              <span className="overload-time">
                {formatHour(hour)}
              </span>

              <span className="overload-bar-track">
                <span
                  className="overload-bar"
                  style={{
                    width: `${Math.min((demand / 240) * 100, 100)}%`,
                  }}
                />
              </span>

              <strong>{demand} kW</strong>

              <span className="overload-arrow">↗</span>
            </button>
          ))
        )}
      </div>

      <p className="muted-note radar-note">
        Select an event to inspect its hourly decision.
      </p>
    </section>
  )
}

function DecisionStrip({ forecast, selectedHour, onSelectHour }) {
  return (
    <section className="panel decision-panel">
      <div className="panel-heading decision-heading">
        <div>
          <span className="eyebrow">HOURLY GRID DECISIONS</span>
          <h2>Decision Strip</h2>
        </div>

        <span className="muted-note">
          Select a tile to inspect its decision
        </span>
      </div>

      <div className="decision-strip">
        {forecast.map((demand, hour) => {
          const decision = getGridDecision(demand, hour)

          let stateClass = 'decision-main'

          if (decision.criticalAlert) {
            stateClass = 'decision-critical'
          } else if (
            decision.gridMode === 'Renewable Storage Mode'
          ) {
            stateClass = 'decision-storage'
          }

          return (
            <button
              key={hour}
              type="button"
              className={`decision-tile ${stateClass} ${
                selectedHour === hour ? 'selected-tile' : ''
              }`}
              onClick={() => onSelectHour(hour)}
              aria-pressed={selectedHour === hour}
              title={`${formatHour(hour)} — ${demand} kW`}
            >
              <span className="tile-hour">
                {String(hour).padStart(2, '0')}
              </span>

              <span className="tile-demand">{demand}</span>

              <span className="tile-unit">kW</span>
            </button>
          )
        })}
      </div>

      <div className="strip-footer">
        <span>
          <i className="legend-dot lavender-dot" />
          Main Grid
        </span>

        <span>
          <i className="legend-dot amber-dot" />
          Storage
        </span>

        <span>
          <i className="legend-dot coral-dot" />
          Critical
        </span>

        <span className="strip-unit">DEMAND IN kW</span>
      </div>
    </section>
  )
}

function App() {
const [selectedHour, setSelectedHour] = useState(19)
const [activePage, setActivePage] = useState('Overview')
const [forecastData, setForecastData] = useState([])
const [apiStatus, setApiStatus] = useState('Connecting')
const [loading, setLoading] = useState(true)
const [apiError, setApiError] = useState('')

useEffect(() => {
let cancelled = false

async function loadForecast() {
  try {
    setLoading(true)
    setApiError('')

    const healthResponse = await fetch(
      `${API_BASE_URL}/api/health`,
    )

    if (!healthResponse.ok) {
      throw new Error('The backend health check failed.')
    }

    const health = await healthResponse.json()

    if (cancelled) return

    setApiStatus(
      health.api_status === 'healthy' &&
        health.model_status === 'loaded'
        ? 'Connected'
        : 'Backend available',
    )

    const fileResponse = await fetch(
      '/sample_test_input.csv',
    )

    if (!fileResponse.ok) {
      throw new Error(
        'Could not load sample_test_input.csv from the frontend.',
      )
    }

    const csvBlob = await fileResponse.blob()
    const formData = new FormData()

    formData.append(
      'file',
      csvBlob,
      'sample_test_input.csv',
    )

    const forecastResponse = await fetch(
      `${API_BASE_URL}/api/forecast`,
      {
        method: 'POST',
        body: formData,
      },
    )

    const result = await forecastResponse.json()

    if (!forecastResponse.ok || result.status !== 'success') {
      throw new Error(
        result.message || 'The forecast request failed.',
      )
    }

    if (cancelled) return

    setForecastData(result.forecast)
  } catch (error) {
    if (!cancelled) {
      setApiStatus('Disconnected')
      setApiError(
        error.message || 'Could not connect to the backend.',
      )
    }
  } finally {
    if (!cancelled) {
      setLoading(false)
    }
  }
}

loadForecast()

return () => {
  cancelled = true
}


}, [])

const previewForecast = forecastData.map(
(item) => Number(item.predicted_demand_kw),
)

const safeSelectedHour = Math.min(
selectedHour,
Math.max(previewForecast.length - 1, 0),
)

const selectedDemand = previewForecast[safeSelectedHour] ?? 0

  const selectedForecast = forecastData[safeSelectedHour]
const decision = selectedForecast
? {
gridMode: selectedForecast.grid_mode,
criticalAlert: selectedForecast.critical_alert,
explanation: selectedForecast.explanation,
}
: getGridDecision(selectedDemand, safeSelectedHour)

const storageHours = forecastData.filter(
(item) => item.grid_mode === 'Renewable Storage Mode',
).length

const criticalHours = forecastData.filter(
(item) => item.critical_alert,
).length

const mainGridHours = forecastData.filter(
(item) => item.grid_mode === 'Main Grid Mode',
).length

  const navigation = [
    { name: 'Overview', icon: '◈' },
    { name: 'Forecast', icon: '◷' },
    { name: 'Alerts', icon: '!' },
    { name: 'Upload', icon: '↑' },
    { name: 'History', icon: '↺' },
  ]

  return (
    <main className="app-shell">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />

      <header className="topbar">
        <a
          className="brand"
          href="#overview"
          onClick={() => setActivePage('Overview')}
        >
          <span className="brand-symbol">
            <span />
            <span />
            <span />
            <span />
          </span>

          <span className="brand-name">
            GRIDMIND<span>AI</span>
          </span>
        </a>

        <div className="topbar-center">
          <span className="live-indicator" />
          LOCAL DASHBOARD
          <span className="topbar-separator">/</span>
          ENERGY INTELLIGENCE
        </div>

        <div className="topbar-right">
          <span className="environment-tag">DEVELOPMENT</span>

          <div className="profile-avatar">GM</div>
        </div>
      </header>

      <section className="dashboard-content" id="overview">
        <div className="page-intro">
          <div>
            <span className="eyebrow intro-eyebrow">
              SMART GRID OPERATIONS / OVERVIEW
            </span>

            <h1>
              Think ahead.
              <br />
              <span>Power intelligently.</span>
            </h1>

            <p className="intro-description">
              Demand forecasting and explainable grid decisions,
              designed for a more responsive energy system.
            </p>
          </div>

          <div className="intro-status">
            <span className="status-ring">✳</span>

            <div>
              <span className="eyebrow">ENGINE STATUS</span>
              <strong>
  {apiStatus === 'Connected'
    ? 'MODEL CONNECTED'
    : apiStatus === 'Disconnected'
      ? 'OFFLINE'
      : 'CONNECTING'}
</strong>
              <span className="status-subtitle">
                {apiError ||
  (apiStatus === 'Connected'
    ? 'Forecast API connected'
    : apiStatus === 'Disconnected'
      ? 'Check Flask backend'
      : 'Connecting to Flask API...')}
              </span>
            </div>
          </div>
        </div>

        <section className="ticker">
          <div className="ticker-label">
            <span className="ticker-icon">↗</span>
            MODE TICKER
          </div>

          <div className="ticker-message">
            <span
              className={
                decision.gridMode === 'Main Grid Mode'
                  ? 'ticker-mode main-mode-text'
                  : 'ticker-mode storage-mode-text'
              }
            >
              {decision.gridMode}
            </span>

            <span className="ticker-divider">/</span>

            <span>
              {decision.criticalAlert
                ? 'Critical overload threshold reached'
                : `Selected hour: ${formatHour(selectedHour)}`}
            </span>
          </div>

          <div
            className={`ticker-state ${
              decision.criticalAlert ? 'ticker-critical' : ''
            }`}
          >
            <span />
            {decision.criticalAlert ? 'ALERT' : 'MONITORING'}
          </div>
        </section>

        <section className="metrics-row">
          <article className="metric-card">
            <span className="metric-label">SELECTED DEMAND</span>

            <div className="metric-value">
              {selectedDemand}
              <span>kW</span>
            </div>

            <div className="metric-bottom">
              <span className="metric-symbol lavender-symbol">↗</span>
              <span>Hour {formatHour(selectedHour)}</span>
            </div>
          </article>

          <article className="metric-card">
            <span className="metric-label">STORAGE MODE HOURS</span>

            <div className="metric-value">
              {storageHours}
              <span>/24</span>
            </div>

            <div className="metric-bottom">
              <span className="metric-symbol amber-symbol">ϟ</span>
              <span>Based on configured grid rules</span>
            </div>
          </article>

          <article className="metric-card">
            <span className="metric-label">CRITICAL HOURS</span>

            <div className="metric-value critical-value">
              {criticalHours}
              <span>/24</span>
            </div>

            <div className="metric-bottom">
              <span className="metric-symbol coral-symbol">!</span>
              <span>Threshold ≥ 200 kW</span>
            </div>
          </article>

          <article className="metric-card">
            <span className="metric-label">DECISION THRESHOLD</span>

            <div className="metric-value">
              {DEMAND_LIMIT}
              <span>kW</span>
            </div>

            <div className="metric-bottom">
              <span className="metric-symbol lavender-symbol">⌁</span>
              <span>Storage switching limit</span>
            </div>
          </article>
        </section>

        <div className="dashboard-grid">
          <div className="dashboard-main-column">
            <EnergyClock
              forecast={previewForecast}
              selectedHour={selectedHour}
              onSelectHour={setSelectedHour}
            />

            <DecisionStrip
              forecast={previewForecast}
              selectedHour={selectedHour}
              onSelectHour={setSelectedHour}
            />
          </div>

          <aside className="dashboard-side-column">
            <BatteryCell />

            <OverloadRadar
              forecast={previewForecast}
              onSelectHour={setSelectedHour}
            />

            <section className="panel rules-panel">
              <div className="panel-heading">
                <div>
                  <span className="eyebrow">DECISION LOGIC</span>
                  <h2>Grid Rules</h2>
                </div>

                <span className="rules-icon">⌘</span>
              </div>

              <div className="rule-item">
                <span className="rule-number">01</span>

                <div>
                  <strong>Demand &gt; 160 kW</strong>
                  <p>Switch to renewable storage mode.</p>
                </div>
              </div>

              <div className="rule-item">
                <span className="rule-number">02</span>

                <div>
                  <strong>18:00 – 22:00</strong>
                  <p>Use storage mode during evening hours.</p>
                </div>
              </div>

              <div className="rule-item">
                <span className="rule-number">03</span>

                <div>
                  <strong>Demand ≥ 200 kW</strong>
                  <p className="critical-text">
                    Trigger a critical overload alert.
                  </p>
                </div>
              </div>
            </section>
          </aside>
        </div>

        <footer className="dashboard-footer">
          <div className="footer-brand">
            <span className="footer-mark">G</span>
            GRIDMIND AI
          </div>

          <p>
  Demand forecasts use the trained ML model and supplied sample data.
  Grid decisions follow configured operating rules.
</p>

          <span className="footer-version">BUILD 0.1.0</span>
        </footer>
      </section>

      <nav className="floating-dock" aria-label="Main navigation">
        {navigation.map((item) => (
          <button
            key={item.name}
            type="button"
            className={`dock-item ${
              activePage === item.name ? 'dock-active' : ''
            }`}
            onClick={() => setActivePage(item.name)}
          >
            <span className="dock-icon">{item.icon}</span>
            <span>{item.name}</span>
          </button>
        ))}
      </nav>
    </main>
  )
}

export default App