import { useEffect, useState } from "react";
import api from "../services/api";
import Card from "../components/Card";

export default function Seasons() {
  const [seasons, setSeasons] = useState<any[]>([]);
  const [sel, setSel] = useState<string | null>(null);
  const [stats, setStats] = useState<any>(null);
  useEffect(() => { api.get("/api/seasons").then((r) => setSeasons(r.data.data || [])).catch(() => setSeasons([])); }, []);
  const open = (s: any) => {
    const id = s.name || s.year || s;
    setSel(String(id));
    api.get(`/api/seasons/${encodeURIComponent(id)}/stats`).then((r) => setStats(r.data)).catch(() => setStats(null));
  };
  return (
    <div className="p-8 grid grid-cols-1 md:grid-cols-3 gap-6">
      <div>
        <h1 className="text-2xl font-bold mb-4">Seasons</h1>
        <div className="space-y-1 max-h-[70vh] overflow-y-auto">
          {seasons.map((s, i) => (
            <button key={i} onClick={() => open(s)} className={`w-full text-left px-3 py-2 rounded text-sm ${sel === String(s.name || s.year) ? "bg-accent/20" : "hover:bg-slate-800"}`}>
              {s.name || s.year}
            </button>
          ))}
        </div>
      </div>
      <div className="md:col-span-2">
        {stats ? (
          <Card>
            <pre className="text-xs overflow-auto">{JSON.stringify(stats, null, 2)}</pre>
          </Card>
        ) : <div className="text-slate-400">Select a season.</div>}
      </div>
    </div>
  );
}