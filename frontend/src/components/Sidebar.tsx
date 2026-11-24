import { NavLink } from "react-router-dom";
import { BarChart3, Trophy, Users, Swords, Target, MapPin, Calendar, Activity } from "lucide-react";

const items = [
  { to: "/", label: "Overview", icon: BarChart3 },
  { to: "/leaderboards", label: "Leaderboards", icon: Trophy },
  { to: "/players", label: "Players", icon: Users },
  { to: "/batting", label: "Batting", icon: Target },
  { to: "/bowling", label: "Bowling", icon: Activity },
  { to: "/teams", label: "Teams", icon: Swords },
  { to: "/matches", label: "Matches", icon: Calendar },
  { to: "/venues", label: "Venues", icon: MapPin },
  { to: "/seasons", label: "Seasons", icon: Calendar },
];

export default function Sidebar() {
  return (
    <aside className="w-60 shrink-0 bg-card border-r border-slate-800 h-screen sticky top-0 flex flex-col">
      <div className="px-5 py-6 border-b border-slate-800">
        <div className="text-xl font-bold text-white">CricStat</div>
        <div className="text-xs text-slate-400 mt-1">Every Run. Every Wicket. Every Statistic.</div>
      </div>
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {items.map((it) => (
          <NavLink
            key={it.to}
            to={it.to}
            end={it.to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition ${
                isActive ? "bg-accent/20 text-white" : "text-slate-300 hover:bg-slate-800"
              }`
            }
          >
            <it.icon size={18} />
            {it.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}