import React, { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  BarChart,
  Bar,
} from "recharts";
import { api } from "./api";

function todayISO(offsetDays = 0) {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  return d.toISOString().slice(0, 10);
}

function KpiCard({ label, value, tone }) {
  return (
    <div className="kpi-card">
      <div className="label">{label}</div>
      <div className={`value ${tone || ""}`}>{value}</div>
    </div>
  );
}

function rankBadgeClass(rank) {
  if (rank === 1) return "badge rank-1";
  if (rank === 2) return "badge rank-2";
  return "badge rank-other";
}

export default function App() {
  const [lines, setLines] = useState([]);
  const [line, setLine] = useState("ALL");
  const [startDate, setStartDate] = useState(todayISO(-30));
  const [endDate, setEndDate] = useState(todayISO());

  const [kpis, setKpis] = useState(null);
  const [trend, setTrend] = useState([]);
  const [ranking, setRanking] = useState([]);
  const [downtime, setDowntime] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.lines().then(setLines).catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    const params = { start_date: startDate, end_date: endDate, line };
    setLoading(true);
    setError(null);
    Promise.all([
      api.kpis(params),
      api.trend(params),
      api.machineRanking({ start_date: startDate, end_date: endDate }),
      api.downtimeBreakdown(params),
    ])
      .then(([k, t, r, d]) => {
        setKpis(k);
        setTrend(t);
        setRanking(r);
        setDowntime(d);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [line, startDate, endDate]);

  return (
    <div className="app">
      <div className="header">
        <div>
          <h1>Manufacturing KPI Dashboard</h1>
          <p>SQL-backed production metrics · yield, defect rate, downtime &amp; machine ranking</p>
        </div>
        <div className="controls">
          <select value={line} onChange={(e) => setLine(e.target.value)}>
            <option value="ALL">All lines</option>
            {lines.map((l) => (
              <option key={l} value={l}>{l}</option>
            ))}
          </select>
          <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
          <span style={{ color: "var(--muted)" }}>to</span>
          <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
        </div>
      </div>

      {error && <div className="error">Couldn't load data: {error}. Is the API running on :8000?</div>}
      {loading && !error && <div className="loading">Loading dashboard…</div>}

      {!loading && !error && kpis && (
        <>
          <div className="kpi-grid">
            <KpiCard label="Planned Units" value={kpis.planned_units?.toLocaleString()} />
            <KpiCard label="Good Units" value={kpis.good_units?.toLocaleString()} tone="good" />
            <KpiCard label="Defective Units" value={kpis.defective_units?.toLocaleString()} tone="bad" />
            <KpiCard label="Yield %" value={`${kpis.yield_pct}%`} tone="good" />
            <KpiCard label="Defect Rate %" value={`${kpis.defect_rate_pct}%`} tone="bad" />
            <KpiCard label="Downtime (min)" value={kpis.downtime_minutes?.toLocaleString()} />
          </div>

          <div className="panels">
            <div className="panel">
              <h2>Defect Rate Trend (with 7-day rolling avg)</h2>
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={trend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#232b40" />
                  <XAxis dataKey="run_date" tick={{ fontSize: 11, fill: "#8b96ab" }} minTickGap={30} />
                  <YAxis tick={{ fontSize: 11, fill: "#8b96ab" }} unit="%" />
                  <Tooltip contentStyle={{ background: "#161d2e", border: "1px solid #232b40" }} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Line type="monotone" dataKey="defect_rate_pct" name="Daily defect rate" stroke="#4f9dff" dot={false} strokeWidth={1.5} />
                  <Line type="monotone" dataKey="defect_rate_7d_avg" name="7-day avg" stroke="#ef5a5a" dot={false} strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="panel">
              <h2>Downtime by Reason</h2>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={downtime} layout="vertical" margin={{ left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#232b40" />
                  <XAxis type="number" tick={{ fontSize: 11, fill: "#8b96ab" }} />
                  <YAxis type="category" dataKey="reason" tick={{ fontSize: 11, fill: "#8b96ab" }} width={110} />
                  <Tooltip contentStyle={{ background: "#161d2e", border: "1px solid #232b40" }} />
                  <Bar dataKey="total_minutes" name="Minutes" fill="#4f9dff" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="panel">
            <h2>Machine Ranking (period totals)</h2>
            <table>
              <thead>
                <tr>
                  <th>Machine</th>
                  <th>Type</th>
                  <th>Line</th>
                  <th>Planned</th>
                  <th>Defect Rate %</th>
                  <th>Downtime (min)</th>
                  <th>Rank</th>
                </tr>
              </thead>
              <tbody>
                {ranking.map((m) => (
                  <tr key={m.machine_id}>
                    <td>{m.machine_id}</td>
                    <td>{m.machine_type}</td>
                    <td>{m.line}</td>
                    <td>{m.planned_units?.toLocaleString()}</td>
                    <td>{m.defect_rate_pct}%</td>
                    <td>{m.downtime_minutes?.toLocaleString()}</td>
                    <td><span className={rankBadgeClass(m.defect_rate_rank)}>#{m.defect_rate_rank}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
