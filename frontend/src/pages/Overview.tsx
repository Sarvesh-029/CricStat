import { useEffect, useState } from "react";
import api from "../services/api";
import Card from "../components/Card";

export default function Overview() {
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/api/dashboard/overview")
      .then((r) => setData(r.data))
      .catch((e) => setErr(e?.message || "Failed to load"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-slate-400">Loading dashboard…</div>;
  if (err) return <div className="p-8 text-red-400">{err}</div>;
  if (!data?.data_available) {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-bold mb-4">CricStat Overview</h1>
        <Card title="No data yet">
          <p className="text-slate-300">
            No processed IPL data found. Run the ingestion pipeline with a CricAPI key:
          </p>
          <pre className="mt-3 text-xs bg-slate-900 p-3 rounded">cd backend{"\n"}python -m scripts.ingest --limit 20</pre>
        </Card>
      </div>
    );
  }

  const stats = [
    { label: "Seasons", value: data.seasons_covered },
    { label: "Matches", value: data.matches_played },
    { label: "Teams", value: data.teams },
    { label: "Players", value: data.players },
    { label: "Total Runs", value: data.total_runs },
    { label: "Total Wickets", value: data.total_wickets },
  ];

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">CricStat Overview</h1>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        {stats.map((s) => (
          <Card key={s.label} title={s.label}>
            <div className="text-2xl font-bold">{s.value ?? "—"}</div>
          </Card>
        ))}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card title="Highest Team Score">
          <div className="text-xl font-bold">{data.highest_team_score ?? "N/A"}</div>
        </Card>
        <Card title="Most Successful Team">
          <div className="text-xl font-bold">{data.most_successful_team?.team ?? "N/A"}</div>
          <div className="text-sm text-slate-400">{data.most_successful_team?.wins ?? 0} wins</div>
        </Card>
        <Card title="Top Run Scorer">
          <div className="text-xl font-bold">{data.top_run_scorer?.player ?? "N/A"}</div>
          <div className="text-sm text-slate-400">{data.top_run_scorer?.runs ?? 0} runs</div>
        </Card>
      </div>
    </div>
  );
}