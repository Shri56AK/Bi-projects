import React, { useEffect, useState, useCallback } from "react";
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";
import { api } from "./api";

const emptyForm = { metric_name: "refund_rate_pct", comparison: ">", threshold: 8, lookback_mins: 10, channel: "console" };

function RuleForm({ onCreated }) {
  const [form, setForm] = useState(emptyForm);
  const [submitting, setSubmitting] = useState(false);

  const update = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.createRule({
        ...form,
        threshold: parseFloat(form.threshold),
        lookback_mins: parseInt(form.lookback_mins, 10),
      });
      setForm(emptyForm);
      onCreated();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="rule-form" onSubmit={submit}>
      <input placeholder="metric name" value={form.metric_name} onChange={update("metric_name")} required />
      <select value={form.comparison} onChange={update("comparison")}>
        <option value=">">&gt;</option>
        <option value="<">&lt;</option>
        <option value=">=">&gt;=</option>
        <option value="<=">&lt;=</option>
      </select>
      <input type="number" step="any" placeholder="threshold" value={form.threshold} onChange={update("threshold")} required />
      <input type="number" placeholder="lookback (mins)" value={form.lookback_mins} onChange={update("lookback_mins")} required />
      <select value={form.channel} onChange={update("channel")}>
        <option value="console">console</option>
        <option value="webhook">webhook</option>
        <option value="email">email</option>
      </select>
      <button className="full" type="submit" disabled={submitting}>
        {submitting ? "Adding…" : "Add alert rule"}
      </button>
    </form>
  );
}

export default function App() {
  const [rules, setRules] = useState([]);
  const [events, setEvents] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [selectedMetric, setSelectedMetric] = useState(null);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState(null);

  const refresh = useCallback(() => {
    Promise.all([api.rules(), api.events(20), api.metrics()])
      .then(([r, e, m]) => {
        setRules(r);
        setEvents(e);
        setMetrics(m);
        if (!selectedMetric && m.length) setSelectedMetric(m[0]);
      })
      .catch((err) => setError(err.message));
  }, [selectedMetric]);

  useEffect(() => { refresh(); }, [refresh]);

  useEffect(() => {
    if (!selectedMetric) return;
    api.metricHistory(selectedMetric, 120).then(setHistory).catch((e) => setError(e.message));
  }, [selectedMetric]);

  return (
    <div className="app">
      <h1>Realtime Alert Engine Console</h1>
      <p className="subtitle">SQL-evaluated threshold rules over business metrics — mirrors the alerting layer of a BI stack.</p>

      {error && <div className="error">Couldn't reach the API: {error}. Is it running on :8001?</div>}

      <div className="grid">
        <div className="panel">
          <h2>Alert Rules</h2>
          <table>
            <thead>
              <tr><th>Metric</th><th>Condition</th><th>Lookback</th><th>Channel</th><th>Status</th><th></th></tr>
            </thead>
            <tbody>
              {rules.map((r) => (
                <tr key={r.rule_id}>
                  <td>{r.metric_name}</td>
                  <td>{r.comparison} {r.threshold}</td>
                  <td>{r.lookback_mins}m</td>
                  <td>{r.channel}</td>
                  <td><span className={`pill ${r.is_active ? "active" : "inactive"}`}>{r.is_active ? "active" : "paused"}</span></td>
                  <td>
                    <button className="ghost" onClick={() => api.toggleRule(r.rule_id).then(refresh)}>toggle</button>{" "}
                    <button className="danger" onClick={() => api.deleteRule(r.rule_id).then(refresh)}>del</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <RuleForm onCreated={refresh} />
        </div>

        <div className="panel">
          <h2>Recent Alert Events</h2>
          <table>
            <thead><tr><th>Metric</th><th>Value</th><th>Fired</th></tr></thead>
            <tbody>
              {events.map((e) => (
                <tr className="event-row bad" key={e.event_id}>
                  <td>{e.metric_name}</td>
                  <td>{e.metric_value} {e.comparison} {e.threshold}</td>
                  <td>{e.fired_at}</td>
                </tr>
              ))}
              {events.length === 0 && <tr><td colSpan={3} style={{ color: "var(--muted)" }}>No alerts fired yet.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>

      <div className="panel">
        <h2>Metric History</h2>
        <div style={{ marginBottom: 10 }}>
          {metrics.map((m) => (
            <button
              key={m}
              className={m === selectedMetric ? "" : "ghost"}
              style={{ marginRight: 6 }}
              onClick={() => setSelectedMetric(m)}
            >
              {m}
            </button>
          ))}
        </div>
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={history}>
            <CartesianGrid strokeDasharray="3 3" stroke="#232b40" />
            <XAxis dataKey="recorded_at" tick={{ fontSize: 10, fill: "#8b96ab" }} minTickGap={40} />
            <YAxis tick={{ fontSize: 11, fill: "#8b96ab" }} />
            <Tooltip contentStyle={{ background: "#161d2e", border: "1px solid #232b40" }} />
            <Line type="monotone" dataKey="metric_value" stroke="#4f9dff" dot={false} strokeWidth={1.5} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
