import { useEffect, useState } from "react";
import api from "../services/api";
import Card from "../components/Card";

export default function Matches() {
  const [season, setSeason] = useState("");
  const [team, setTeam] = useState("");
  const [rows, setRows] = useState<any[]>([]);
  useEffect(() => {
    api.get("/api/matches", { params: { season: season || undefined, team: team || undefined, limit: 100 } })
      .then((r) => setRows(r.data.data || []))
      .catch(() => setRows([]));
  }, [season, team]);
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Matches</h1>
      <div className="flex gap-3 mb-4">
        <input value={season} onChange={(e) => setSeason(e.target.value)} placeholder="Season" className="bg-slate-800 rounded px-3 py-2 text-sm" />
        <input value={team} onChange={(e) => setTeam(e.target.value)} placeholder="Team" className="bg-slate-800 rounded px-3 py-2 text-sm" />
      </div>
      <Card>
        <div className="overflow-x-auto max-h-[70vh] overflow-y-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-slate-400 text-left"><th className="py-2 pr-3">Date</th><th className="py-2 pr-3">Match</th><th className="py-2 pr-3">Venue</th><th className="py-2 pr-3">Winner</th></tr></thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i} className="border-b border-slate-800/50">
                  <td className="py-2 pr-3">{r.date ?? "—"}</td>
                  <td className="py-2 pr-3">{r.team1} vs {r.team2}</td>
                  <td className="py-2 pr-3">{r.venue ?? "—"}</td>
                  <td className="py-2 pr-3">{r.winner ?? "—"}</td>
                </tr>
              ))}
              {rows.length === 0 && <tr><td colSpan={4} className="py-6 text-center text-slate-400">No matches.</td></tr>}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}