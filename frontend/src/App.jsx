import Results from "./pages/Results";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import Dashboard from "./pages/Dashboard";
import UploadReport from "./pages/UploadReport";
import HealthAssistant from "./pages/HealthAssistant";
import { sanitizeStoredAnalysis } from "./utils/analysisStorage";
import AppShell from "./components/AppShell";

function App() {
  sanitizeStoredAnalysis();

  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<UploadReport />} />
          <Route path="/results" element={<Results />} />
          <Route path="/assistant" element={<HealthAssistant />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
