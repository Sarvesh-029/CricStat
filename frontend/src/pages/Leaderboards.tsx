import { useEffect, useState } from "react";
import api from "../services/api";
import Card from "../components/Card";

const battingMetrics = ["runs","centuries","half_centuries","sixes","fours","batting_average","strike_rate","highest_score","innings"];
const bowlingMetrics = ["wickets","bowling_average","economy","bowling_strike_rate","maidens","four_wicket_hauls","five_wicket_hauls"];

export default function Leaderboards() {
  const [type, setType] = useState<"batting"|"bowling">("batting");
  const [metric, setMetric] = useState("runs");
  const [rows, setRows] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const metrics = type === "batting" ? battingMetrics : bowlingMetrics;
    if (!metrics.includes(metric)) setMetric(metrics[0]);
  }, [type]);

  useEffect(() => {
    setLoading(true);
    const url = type === "batting" ? "/api/leaderboards/all-time/batting" : "/api/leaderboards/all-time/bowling";
    api.get(url, { params: { metric, limit: 25 } })
      .then((r) => setRows(r.data.data || []))
      .catch(() => setRows([]))
      .finally(() => setLoading(false));
  }, [type, metric]);

  const metrics = type === "batting" ? battingMetrics : bowlingMetrics;

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">All-Time Leaderboards</h1>
      <div className="flex gap-2 mb-4">
        {(["batting","bowling"] as const).map((t) => (
          <button key={t} onClick={() => setType(t)}
            className={`px-4 py-2 rounded-lg text-sm ${type===t ? "bg-accent text-white" : "bg-slate-800 text-slate-300"}`}>
            {t}
          </button>
        ))}
        <select value={metric} onChange={(e)=>setMetric(e.target.value)}
          className="ml-4 bg-slate-800 text-white rounded px-3 py-2 text-sm">
          {metrics.map((m) => <option key={m} value={m}>{m}</option>)}
        </select>
      </div>
      <Card>
        {loading ? <div className="text-slate-400">Loading…</div> : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-400 text-left border-b border-slate-700">
                  <th className="py-2 pr-3">Rank</th>
                  <th className="py-2 pr-3">Player</th>
                  <th className="py-2 pr-3">{metric}</th>
                  {type==="batting" && <><th className="py-2 pr-3">Innings</th><th className="py-2 pr-3">Runs</th><th className="py-2 pr-3">SR</th></>}
                  {type==="bowling" && <><th className="py-2 pr-3">Wickets</th><th className="py-2 pr-3">Econ</th></>}
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={i} className="border-b border-slate-800/50">
                    <td className="py-2 pr-3">{r.rank ?? i+1}</td>
                    <td className="py-2 pr-3 font-medium">{r.player}</td>
                    <td className="py-2 pr-3">{r[metric] ?? "—"}</td>
                    {type==="batting" && <><td className="py-2 pr-3">{r.innings ?? "—"}</td><td className="py-2 pr-3">{r.runs ?? "—"}</td><td className="py-2 pr-3">{r.strike_rate ?? "—"}</td></>}
                    {type==="bowling" && <><td className="py-2 pr-3">{r.wickets ?? "—"}</td><td className="py-2 pr-3">{r.economy ?? "—"}</td></>}
                  </tr>
                ))}
                {rows.length === 0 && <tr><td colSpan={6} className="py-6 text-center text-slate-400">No data available.</td></tr>}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}