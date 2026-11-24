import { useEffect, useState } from "react";
import api from "../services/api";
import Card from "../components/Card";

export default function Players() {
  const [q, setQ] = useState("");
  const [list, setList] = useState<any[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    api.get("/api/players", { params: { search: q || undefined, limit: 50 } })
      .then((r) => setList(r.data.data || []))
      .catch(() => setList([]));
  }, [q]);

  const open = (p: any) => {
    setSelected(p);
    const id = p.provider_id || p.id || p.name;
    api.get(`/api/players/${encodeURIComponent(id)}/stats`)
      .then((r) => setStats(r.data))
      .catch(() => setStats(null));
  };

  return (
    <div className="p-8 grid grid-cols-1 md:grid-cols-3 gap-6">
      <div>
        <h1 className="text-2xl font-bold mb-4">Players</h1>
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search player…"
          className="w-full mb-3 bg-slate-800 rounded px-3 py-2 text-sm" />
        <div className="space-y-1 max-h-[70vh] overflow-y-auto">
          {list.map((p, i) => (
            <button key={i} onClick={() => open(p)}
              className={`w-full text-left px-3 py-2 rounded text-sm ${selected?.name === p.name ? "bg-accent/20" : "hover:bg-slate-800"}`}>
              {p.name}
            </button>
          ))}
          {list.length === 0 && <div className="text-slate-400 text-sm">No players.</div>}
        </div>
      </div>
      <div className="md:col-span-2">
        {stats ? (
          <>
            <h2 className="text-xl font-bold mb-4">{selected?.name}</h2>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <Card title="Batting">
                {stats.batting && Object.keys(stats.batting).length ? (
                  <ul className="text-sm space-y-1">
                    {Object.entries(stats.batting).filter(([k]) => k !== "season_wise").map(([k, v]) => (
                      <li key={k} className="flex justify-between"><span className="text-slate-400">{k}</span><span>{String(v ?? "—")}</span></li>
                    ))}
                  </ul>
                ) : <div className="text-slate-400 text-sm">No batting data.</div>}
              </Card>
              <Card title="Bowling">
                {stats.bowling && Object.keys(stats.bowling).length ? (
                  <ul className="text-sm space-y-1">
                    {Object.entries(stats.bowling).map(([k, v]) => (
                      <li key={k} className="flex justify-between"><span className="text-slate-400">{k}</span><span>{String(v ?? "—")}</span></li>
                    ))}
                  </ul>
                ) : <div className="text-slate-400 text-sm">No bowling data.</div>}
              </Card>
            </div>
          </>
        ) : (
          <div className="text-slate-400">Select a player to view stats.</div>
        )}
      </div>
    </div>
  );
}