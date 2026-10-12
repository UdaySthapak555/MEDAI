import "./Results.css";
import { Link } from "react-router-dom";
import {
  ArrowLeft,
  CheckCircle2,
  FileText,
  Activity,
  Droplets,
  HeartPulse,
} from "lucide-react";

function Results() {
  const storedResult = sessionStorage.getItem("medai_result");

  if (!storedResult) {
    return (
      <div className="results-page">
        <Link to="/upload" className="back-button">
          <ArrowLeft size={17} />
          Analyze Another Report
        </Link>

        <div className="results-header">
          <span className="page-overline">NO REPORT</span>
          <h1>No Analysis Found</h1>
          <p>Please upload and analyze a medical report first.</p>
        </div>
      </div>
    );
  }

  const result = JSON.parse(storedResult);

  const medicalData = result.medical_data || {};
  const classification = result.classification || {};

  const status = classification.status || "UNKNOWN";
  const confidence = Math.round(
    (classification.confidence || 0) * 100
  );

  const flags = classification.flags || [];

  const parameters = [
    {
      name: "HEMOGLOBIN",
      value: medicalData.hemoglobin,
      unit: "g/dL",
      icon: <Activity size={20} />,
    },
    {
      name: "WBC",
      value: medicalData.wbc,
      unit: "/µL",
      icon: <Droplets size={20} />,
    },
    {
      name: "PLATELETS",
      value: medicalData.platelets,
      unit: "/µL",
      icon: <HeartPulse size={20} />,
    },
    {
      name: "GLUCOSE",
      value: medicalData.glucose,
      unit: "mg/dL",
      icon: <Activity size={20} />,
    },
    {
      name: "CHOLESTEROL",
      value: medicalData.cholesterol,
      unit: "mg/dL",
      icon: <HeartPulse size={20} />,
    },
    {
      name: "RBC",
      value: medicalData.rbc,
      unit: "M/µL",
      icon: <Activity size={20} />,
    },
  ];

  return (
    <div className="results-page">

      {/* Back */}
      <Link to="/upload" className="back-button">
        <ArrowLeft size={17} />
        Analyze Another Report
      </Link>

      {/* Header */}
      <div className="results-header">
        <span className="page-overline">
          ANALYSIS COMPLETE
        </span>

        <h1>Medical Report Results</h1>

        <p>
          AI-assisted screening summary based on the uploaded report.
        </p>
      </div>

      {/* Status */}
      <div className="result-status-card">

        <div className="result-status-icon">
          <CheckCircle2 size={34} />
        </div>

        <div>
          <span className="result-label">
            OVERALL STATUS
          </span>

          <h2>{status}</h2>

          <p>
            Prototype screening classification
          </p>
        </div>

        <div className="confidence-box">
          <span>CONFIDENCE</span>

          <strong>
            {confidence}%
          </strong>
        </div>

      </div>

      {/* Medical Parameters */}
      <div className="results-section">

        <div className="section-heading">

          <div>
            <span className="page-overline">
              EXTRACTED DATA
            </span>

            <h2>
              Medical Parameters
            </h2>
          </div>

          <FileText size={22} />

        </div>

        <div className="parameter-grid">

          {parameters.map((parameter) => (

            <div
              className="parameter-card"
              key={parameter.name}
            >

              <div className="parameter-icon">
                {parameter.icon}
              </div>

              <span>
                {parameter.name}
              </span>

              <strong>
                {parameter.value ?? "N/A"}
              </strong>

              <small>
                {parameter.unit}
              </small>

            </div>

          ))}

        </div>

      </div>

      {/* Screening Summary */}
      <div className="report-summary-card">

        <div className="summary-icon">
          <CheckCircle2 size={22} />
        </div>

        <div>

          <span className="result-label">
            SCREENING SUMMARY
          </span>

          {flags.length === 0 ? (

            <>
              <h3>
                No parameters flagged
              </h3>

              <p>
                The extracted values did not trigger
                any of the current prototype screening rules.
              </p>
            </>

          ) : (

            <>
              <h3>
                {flags.length} parameter
                {flags.length > 1 ? "s" : ""} flagged
              </h3>

              <ul>
                {flags.map((flag, index) => (
                  <li key={index}>
                    {flag}
                  </li>
                ))}
              </ul>
            </>

          )}

        </div>

      </div>

      {/* Disclaimer */}
      <div className="medical-disclaimer">

        <strong>
          Important
        </strong>

        <p>
          MEDAI is an educational and informational
          prototype. This classification does not
          constitute a medical diagnosis or medical
          advice. Always consult a qualified healthcare
          professional for interpretation of medical
          reports.
        </p>

      </div>

    </div>
  );
}

export default Results;