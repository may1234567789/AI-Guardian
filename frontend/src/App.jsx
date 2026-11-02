import { lazy, Suspense, useCallback, useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import Shell from "./components/Shell.jsx";
import { LoadingState } from "./components/Feedback.jsx";
import { healthCheck } from "./services/api.js";

const Overview = lazy(() => import("./pages/Overview.jsx"));
const PromptScanner = lazy(() => import("./pages/PromptScanner.jsx"));
const ActionAuthorization = lazy(() => import("./pages/ActionAuthorization.jsx"));
const DataLeakScanner = lazy(() => import("./pages/DataLeakScanner.jsx"));
const SecurityEvents = lazy(() => import("./pages/SecurityEvents.jsx"));
const ModelPerformance = lazy(() => import("./pages/ModelPerformance.jsx"));
const Settings = lazy(() => import("./pages/Settings.jsx"));

export default function App() {
  const [health, setHealth] = useState(null);
  const [checkedAt, setCheckedAt] = useState(null);

  const refreshHealth = useCallback(async () => {
    try {
      const current = await healthCheck();
      setHealth(current);
    } catch (error) {
      setHealth({ status: "offline", error: error.message });
    } finally {
      setCheckedAt(new Date().toISOString());
    }
  }, []);

  useEffect(() => {
    refreshHealth();
    const timer = window.setInterval(refreshHealth, 30000);
    return () => window.clearInterval(timer);
  }, [refreshHealth]);

  return (
    <Routes>
      <Route element={<Shell health={health} checkedAt={checkedAt} refreshHealth={refreshHealth} />}>
        <Route index element={<Suspense fallback={<LoadingState />}><Overview health={health} refreshHealth={refreshHealth} /></Suspense>} />
        <Route path="/scanner" element={<Suspense fallback={<LoadingState />}><PromptScanner /></Suspense>} />
        <Route path="/authorization" element={<Suspense fallback={<LoadingState />}><ActionAuthorization /></Suspense>} />
        <Route path="/data-leak" element={<Suspense fallback={<LoadingState />}><DataLeakScanner /></Suspense>} />
        <Route path="/events" element={<Suspense fallback={<LoadingState />}><SecurityEvents /></Suspense>} />
        <Route path="/models" element={<Suspense fallback={<LoadingState />}><ModelPerformance /></Suspense>} />
        <Route path="/settings" element={<Suspense fallback={<LoadingState />}><Settings health={health} refreshHealth={refreshHealth} /></Suspense>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
