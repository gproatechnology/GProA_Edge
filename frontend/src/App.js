import { useState, useEffect, useCallback } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useNavigate, useParams } from "react-router-dom";
import axios from "axios";
import Sidebar from "@/components/Sidebar";
import ProjectDashboard from "@/components/ProjectDashboard";
import ProjectDetail from "@/components/ProjectDetail";

import SplashScreen from "./components/SplashScreen";
import Login from "./components/Login";

let API = "/api";
if (process.env.REACT_APP_BACKEND_URL) {
  const url = process.env.REACT_APP_BACKEND_URL;
  API = url.startsWith("http")
    ? `${url}/api`
    : url.startsWith("localhost")
    ? `http://${url}/api`
    : `https://${url}/api`;
} else if (process.env.NODE_ENV === "development") {
  API = "http://localhost:8000/api";
}

export { API };

function AppLayout() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchProjects = useCallback(async () => {
    try {
      setLoading(true);
      const res = await axios.get(`${API}/projects`);
      setProjects(res.data);
    } catch (e) {
      console.error("Error fetching projects:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const stats = {
    critical: projects.filter(p => p.priority === "Crítica").length,
    high: projects.filter(p => p.priority === "Alta").length,
    efficiency: projects.length > 0 
      ? (projects.reduce((sum, p) => sum + (p.efficiency || 0), 0) / projects.length).toFixed(1)
      : 0
  };

  return (
    <div className="flex min-h-screen bg-background text-foreground transition-colors duration-300" data-testid="app-layout">
      <Sidebar projects={projects} onNavigate={navigate} stats={stats} />
      <main className="flex-1 ml-[260px]">
        <Routes>
          <Route
            path="/"
            element={
              <ProjectDashboard
                projects={projects}
                loading={loading}
                stats={stats}
                onProjectCreated={fetchProjects}
                onNavigate={navigate}
              />
            }
          />
          <Route
            path="/projects/:projectId"
            element={<ProjectDetailWrapper onProjectDeleted={fetchProjects} />}
          />
        </Routes>
      </main>
    </div>
  );
}

function ProjectDetailWrapper({ onProjectDeleted }) {
  const { projectId } = useParams();
  const navigate = useNavigate();
  return (
    <ProjectDetail
      projectId={projectId}
      onProjectDeleted={() => {
        onProjectDeleted();
        navigate("/");
      }}
    />
  );
}

import { Toaster } from "sonner";

function MainApp() {
  const [showSplash, setShowSplash] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Check local storage for existing session
  useEffect(() => {
    const session = localStorage.getItem("gproa_session");
    if (session) {
      setIsAuthenticated(true);
    }
  }, []);

  const handleLogin = () => {
    localStorage.setItem("gproa_session", "true");
    setIsAuthenticated(true);
  };

  if (showSplash) {
    return <SplashScreen onFinish={() => setShowSplash(false)} />;
  }

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <>
      <Toaster position="top-right" richColors closeButton />
      <AppLayout />
    </>
  );
}

function App() {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <MainApp />
    </BrowserRouter>
  );
}

export default App;
