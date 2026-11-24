import { useEffect, useState } from "react";
import api from "../services/api";
import Card from "../components/Card";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

const metrics = ["wickets","bowling_average","economy","bowling_strike_rate","maidens","four_wicket_hauls","five_wicket_hauls"];

export default function Bowling() {
  const [metric, setMetric] = useState("wickets");
  const [rows, setRows] = useState<any[]>([]);
  useEffect(() => {
    api.get("/api/leaderboards/all-time/bowling", { params: { metric, limit: 15 } })
      .then((r) => setRows(r.data.data || []))
      .catch(() => setRows([]));
  }, [metric]);
  const chart = rows.map((r) => ({ name: r.player, value: r[metric] }));
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Bowling Analysis</h1>
      <div className="mb-4">
        <select value={metric} onChange={(e) => setMetric(e.target.value)} className="bg-slate-800 text-white rounded px-3 py-2 text-sm">
          {metrics.map((m) => <option key={m} value={m}>{m}</option>)}
        </select>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title={`Top 15 — ${metric}`}>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chart}><XAxis dataKey="name" hide /><YAxis /><Tooltip /><Bar dataKey="value" fill="#22c55e" /></BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
        <Card title="Table">
          <div className="overflow-x-auto max-h-80 overflow-y-auto">
            <table className="w-full text-sm">
              <thead><tr className="text-slate-400 text-left"><th className="py-2 pr-3">Rank</th><th className="py-2 pr-3">Player</th><th className="py-2 pr-3">{metric}</th><th className="py-2 pr-3">Wkts</th><th className="py-2 pr-3">Econ</th></tr></thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={i} className="border-b border-slate-800/50">
                    <td className="py-2 pr-3">{r.rank ?? i + 1}</td>
                    <td className="py-2 pr-3">{r.player}</td>
                    <td className="py-2 pr-3">{r[metric] ?? "—"}</td>
                    <td className="py-2 pr-3">{r.wickets ?? "—"}</td>
                    <td className="py-2 pr-3">{r.economy ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  );
}