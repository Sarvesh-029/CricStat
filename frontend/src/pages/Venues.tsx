import { useEffect, useState } from "react";
import api from "../services/api";
import Card from "../components/Card";

export default function Venues() {
  const [rows, setRows] = useState<any[]>([]);
  useEffect(() => { api.get("/api/venues").then((r) => setRows(r.data.data || [])).catch(() => setRows([])); }, []);
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Venues</h1>
      <Card>
        <div className="overflow-x-auto max-h-[70vh] overflow-y-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-slate-400 text-left"><th className="py-2 pr-3">Venue</th><th className="py-2 pr-3">City</th><th className="py-2 pr-3">Matches</th></tr></thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i} className="border-b border-slate-800/50">
                  <td className="py-2 pr-3">{r.name}</td>
                  <td className="py-2 pr-3">{r.city ?? "—"}</td>
                  <td className="py-2 pr-3">{r.matches_played ?? "—"}</td>
                </tr>
              ))}
              {rows.length === 0 && <tr><td colSpan={3} className="py-6 text-center text-slate-400">No venues.</td></tr>}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}