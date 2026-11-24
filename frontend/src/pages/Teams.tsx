import { useEffect, useState } from "react";
import api from "../services/api";
import Card from "../components/Card";

export default function Teams() {
  const [teams, setTeams] = useState<any[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    api.get("/api/teams").then((r) => setTeams(r.data.data || [])).catch(() => setTeams([]));
  }, []);

  const open = (name: string) => {
    setSelected(name);
    api.get(`/api/teams/${encodeURIComponent(name)}/stats`).then((r) => setStats(r.data)).catch(() => setStats(null));
  };

  return (
    <div className="p-8 grid grid-cols-1 md:grid-cols-3 gap-6">
      <div>
        <h1 className="text-2xl font-bold mb-4">Teams</h1>
        <div className="space-y-1 max-h-[70vh] overflow-y-auto">
          {teams.map((t, i) => (
            <button key={i} onClick={() => open(t.name || t)} className={`w-full text-left px-3 py-2 rounded text-sm ${selected === (t.name || t) ? "bg-accent/20" : "hover:bg-slate-800"}`}>
              {t.name || t}
            </button>
          ))}
        </div>
      </div>
      <div className="md:col-span-2">
        {stats ? (
          <>
            <h2 className="text-xl font-bold mb-4">{selected}</h2>
            <Card>
              <pre className="text-xs overflow-auto">{JSON.stringify(stats, null, 2)}</pre>
            </Card>
          </>
        ) : <div className="text-slate-400">Select a team.</div>}
      </div>
    </div>
  );
}