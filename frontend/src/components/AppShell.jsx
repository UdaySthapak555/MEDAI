import { NavLink, Outlet } from "react-router-dom";
import {
  Activity,
  FileText,
  HeartPulse,
  Home,
  MessageSquareText,
  ShieldCheck,
  Upload,
} from "lucide-react";
import "./AppShell.css";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: Home, end: true },
  { to: "/upload", label: "Analyze Report", icon: Upload },
  { to: "/results", label: "Results", icon: FileText },
  { to: "/assistant", label: "Health Assistant", icon: MessageSquareText },
];

function AppShell() {
  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <NavLink to="/" className="app-brand" aria-label="MEDAI Dashboard">
          <span className="app-brand-mark"><HeartPulse size={21} /></span>
          <span className="app-brand-copy">
            <strong>MEDAI</strong>
            <small>Health report insights</small>
          </span>
        </NavLink>

        <nav className="app-navigation" aria-label="Main navigation">
          <span className="app-navigation-label">WORKSPACE</span>
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) => `app-nav-link${isActive ? " is-active" : ""}`}
            >
              <Icon size={18} aria-hidden="true" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="app-sidebar-note">
          <ShieldCheck size={18} aria-hidden="true" />
          <div>
            <strong>Session-only prototype</strong>
            <p>MEDAI does not keep report history.</p>
          </div>
        </div>
        <div className="app-sidebar-footer">
          <Activity size={15} aria-hidden="true" />
          Educational information only
        </div>
      </aside>

      <div className="app-main-column">
        <header className="mobile-app-header">
          <NavLink to="/" className="app-brand" aria-label="MEDAI Dashboard">
            <span className="app-brand-mark"><HeartPulse size={20} /></span>
            <span className="app-brand-copy"><strong>MEDAI</strong></span>
          </NavLink>
        </header>
        <main className="app-main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default AppShell;
