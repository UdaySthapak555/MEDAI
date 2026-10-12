import { Link } from "react-router-dom";
import {
  Activity,
  Bell,
  ChevronRight,
  Clock3,
  FileText,
  HeartPulse,
  LayoutDashboard,
  MessageSquare,
  Settings,
  ShieldCheck,
  Upload,
} from "lucide-react";

const recentReports = [
  {
    name: "Complete Blood Count",
    date: "Today, 10:42 AM",
    status: "Normal",
    type: "CBC",
  },
  {
    name: "Lipid Profile",
    date: "Yesterday, 04:18 PM",
    status: "Review",
    type: "LIPID",
  },
  {
    name: "Liver Function Test",
    date: "Sep 28, 09:31 AM",
    status: "Normal",
    type: "LFT",
  },
];

function Dashboard() {
  return (
    <div className="app-shell">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            <HeartPulse size={22} />
          </div>

          <div>
            <h2>MEDAI</h2>
            <span>Intelligent Health</span>
          </div>
        </div>

        <div className="nav-section">
          <p className="nav-label">WORKSPACE</p>

          <button className="nav-item active">
            <LayoutDashboard size={19} />
            <span>Dashboard</span>
          </button>

          <button className="nav-item">
            <FileText size={19} />
            <span>Reports</span>
          </button>

          <button className="nav-item">
            <MessageSquare size={19} />
            <span>AI Assistant</span>
          </button>

          <button className="nav-item">
            <Clock3 size={19} />
            <span>History</span>
          </button>
        </div>

        <div className="nav-section settings-section">
          <p className="nav-label">SYSTEM</p>

          <button className="nav-item">
            <Settings size={19} />
            <span>Settings</span>
          </button>

          <button className="nav-item">
            <ShieldCheck size={19} />
            <span>Privacy & Security</span>
          </button>
        </div>

        <div className="sidebar-bottom">
          <div className="secure-badge">
            <ShieldCheck size={17} />

            <div>
              <strong>Secure Workspace</strong>
              <span>Your data stays protected</span>
            </div>
          </div>

          <div className="profile">
            <div className="avatar">U</div>

            <div className="profile-info">
              <strong>Uday</strong>
              <span>Personal Workspace</span>
            </div>

            <ChevronRight size={17} />
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {/* Top Navigation */}
        <header className="topbar">
          <div>
            <span className="page-overline">HEALTH INTELLIGENCE</span>
            <h1>Dashboard</h1>
          </div>

          <div className="topbar-actions">
            <button className="icon-button">
              <Bell size={19} />
              <span className="notification-dot"></span>
            </button>

            <div className="top-profile">
              <div className="avatar small">U</div>

              <div>
                <strong>Uday</strong>
                <span>Personal</span>
              </div>
            </div>
          </div>
        </header>

        {/* Welcome Section */}
        <section className="welcome-section">
          <div>
            <p className="greeting">Good evening, Uday</p>

            <h2>Your health, intelligently analyzed.</h2>

            <p className="welcome-description">
              Upload a medical report and let MEDAI transform complex medical
              information into clear, understandable insights.
            </p>
          </div>

          <div className="health-orb">
            <div className="orb-ring ring-one"></div>
            <div className="orb-ring ring-two"></div>

            <Activity size={28} />
          </div>
        </section>

        {/* Upload Card */}
        <section className="upload-card">
          <div className="upload-glow"></div>

          <div className="upload-icon">
            <Upload size={24} />
          </div>

          <div className="upload-content">
            <span className="card-eyebrow">AI REPORT ANALYSIS</span>

            <h3>Analyze a medical report</h3>

            <p>
              Upload your PDF or medical report image. MEDAI will extract,
              classify and analyze the information.
            </p>
          </div>

          <Link to="/upload" className="primary-button">
          <Upload size={18} />
          Upload Report
          </Link>
          <span className="upload-hint">
            PDF, PNG or JPG · Maximum 10 MB
          </span>
        </section>

        {/* Statistics */}
        <section className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon blue">
              <FileText size={20} />
            </div>

            <div>
              <span>Total Reports</span>
              <strong>24</strong>
            </div>

            <small>+3 this month</small>
          </div>

          <div className="stat-card">
            <div className="stat-icon green">
              <Activity size={20} />
            </div>

            <div>
              <span>Reports Analyzed</span>
              <strong>21</strong>
            </div>

            <small>87.5% processed</small>
          </div>

          <div className="stat-card">
            <div className="stat-icon purple">
              <ShieldCheck size={20} />
            </div>

            <div>
              <span>Normal Results</span>
              <strong>17</strong>
            </div>

            <small>81% of analyzed</small>
          </div>
        </section>

        {/* Recent Reports */}
        <section className="reports-section">
          <div className="section-header">
            <div>
              <span className="card-eyebrow">YOUR ANALYSIS</span>
              <h3>Recent reports</h3>
            </div>

            <button className="view-all">
              View all
              <ChevronRight size={16} />
            </button>
          </div>

          <div className="reports-list">
            {recentReports.map((report) => (
              <div className="report-row" key={report.name}>
                <div className="report-file-icon">
                  <FileText size={20} />
                </div>

                <div className="report-name">
                  <strong>{report.name}</strong>

                  <span>
                    {report.type} · {report.date}
                  </span>
                </div>

                <div
                  className={`status ${
                    report.status === "Normal" ? "normal" : "review"
                  }`}
                >
                  <span></span>
                  {report.status}
                </div>

                <button className="row-arrow">
                  <ChevronRight size={17} />
                </button>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}

export default Dashboard;