import { BrowserRouter, Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Overview from "./pages/Overview";
import Leaderboards from "./pages/Leaderboards";
import Players from "./pages/Players";
import Batting from "./pages/Batting";
import Bowling from "./pages/Bowling";
import Teams from "./pages/Teams";
import Matches from "./pages/Matches";
import Venues from "./pages/Venues";
import Seasons from "./pages/Seasons";

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/leaderboards" element={<Leaderboards />} />
            <Route path="/players" element={<Players />} />
            <Route path="/batting" element={<Batting />} />
            <Route path="/bowling" element={<Bowling />} />
            <Route path="/teams" element={<Teams />} />
            <Route path="/matches" element={<Matches />} />
            <Route path="/venues" element={<Venues />} />
            <Route path="/seasons" element={<Seasons />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}