import { Link } from "react-router-dom";
import {
  Activity,
  ArrowUpRight,
  FileText,
  HeartPulse,
  MessageSquareText,
  ShieldCheck,
  Upload,
} from "lucide-react";

function hasStoredAnalysis() {
  try {
    return Boolean(sessionStorage.getItem("medai_result"));
  } catch {
    return false;
  }
}

function Dashboard() {
  const hasAnalysis = hasStoredAnalysis();

  return (
    <div className="dashboard-page">
      <header className="dashboard-page-header">
        <div>
          <span className="page-eyebrow">YOUR REPORT WORKSPACE</span>
          <h1 className="page-title">Dashboard</h1>
        </div>
        <Link to="/assistant" className="secondary-button dashboard-assistant-link">
          <MessageSquareText size={17} />
          Health Assistant
        </Link>
      </header>

      <section className="dashboard-hero surface-card" aria-labelledby="dashboard-hero-title">
        <div className="dashboard-hero-content">
          <span className="dashboard-kicker"><Activity size={14} /> AI-POWERED REPORT ANALYSIS</span>
          <h2 id="dashboard-hero-title">
            Your medical reports,<br />
            <span>explained. Simplified.</span>
          </h2>
          <p>
            Explore supported values and document categories from a report, with
            clear educational context. Results may be incomplete and are not a diagnosis.
          </p>
          <div className="dashboard-hero-actions">
            <Link to="/upload" className="primary-button">
              <Upload size={17} />
              Analyze a Report
              <ArrowUpRight size={16} />
            </Link>
            <Link to="/assistant" className="dashboard-text-link">
              Explore health topics
              <ArrowUpRight size={15} />
            </Link>
          </div>
        </div>
        <div className="dashboard-hero-art" aria-hidden="true">
          <div className="dashboard-art-halo" />
          <div className="dashboard-art-card dashboard-art-card-back"><Activity size={20} /></div>
          <div className="dashboard-art-card dashboard-art-card-front">
            <span className="dashboard-art-card-icon"><FileText size={19} /></span>
            <span className="dashboard-art-line dashboard-art-line-wide" />
            <span className="dashboard-art-line" />
            <span className="dashboard-art-value"><HeartPulse size={16} /> Report insights</span>
          </div>
          <span className="dashboard-art-spark dashboard-art-spark-one" />
          <span className="dashboard-art-spark dashboard-art-spark-two" />
        </div>
      </section>

      <section className="dashboard-capabilities" aria-label="MEDAI prototype capabilities">
        <article className="dashboard-capability surface-card">
          <span className="dashboard-capability-icon orange"><Upload size={19} /></span>
          <h2>Report upload</h2>
          <p>Analyze PDF, PNG, or JPEG reports up to 10 MB.</p>
        </article>
        <article className="dashboard-capability surface-card">
          <span className="dashboard-capability-icon yellow"><Activity size={19} /></span>
          <h2>Supported lab markers</h2>
          <p>View up to six recognized values. Missing or unclear results stay unavailable.</p>
        </article>
        <article className="dashboard-capability surface-card">
          <span className="dashboard-capability-icon peach"><ShieldCheck size={19} /></span>
          <h2>Prototype classification</h2>
          <p>Document categories use a synthetic English dataset and are not validated on real reports.</p>
        </article>
      </section>

      <section className="dashboard-activity surface-card" aria-labelledby="dashboard-history-title">
        <div className="dashboard-activity-icon"><FileText size={20} /></div>
        <div className="dashboard-activity-copy">
          <span className="page-eyebrow">REPORT ACTIVITY</span>
          <h2 id="dashboard-history-title">Report history is unavailable</h2>
          <p>
            {hasAnalysis
              ? "MEDAI does not keep report history or aggregate statistics. Your latest analysis is temporarily available in this browser session."
              : "MEDAI does not keep report history or aggregate statistics. Analyze a report to view its result in this session."}
          </p>
          <div className="dashboard-activity-actions">
            <Link to="/upload" className="primary-button">
              <Upload size={16} />
              Analyze a Report
            </Link>
            {hasAnalysis && (
              <Link to="/results" className="dashboard-text-link">
                View latest result <ArrowUpRight size={15} />
              </Link>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}

export default Dashboard;
