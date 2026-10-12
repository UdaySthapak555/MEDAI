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

const PARAMETERS = [
  { key: "hemoglobin", name: "HEMOGLOBIN", unit: "g/dL", icon: Activity },
  { key: "wbc", name: "WBC", unit: "/µL", icon: Droplets },
  { key: "platelets", name: "PLATELETS", unit: "/µL", icon: HeartPulse },
  { key: "glucose", name: "GLUCOSE", unit: "mg/dL", icon: Activity },
  { key: "cholesterol", name: "CHOLESTEROL", unit: "mg/dL", icon: HeartPulse },
  { key: "rbc", name: "RBC", unit: "M/µL", icon: Activity },
];

const PARAMETER_EDUCATION = {
  hemoglobin: {
    explanation: "Hemoglobin is a protein in red blood cells that carries oxygen.",
    source: "MedlinePlus: Complete Blood Count",
    sourceUrl: "https://medlineplus.gov/lab-tests/complete-blood-count-cbc/",
  },
  wbc: {
    explanation: "White blood cells are part of the immune system and help fight infections and other diseases.",
    source: "MedlinePlus: Complete Blood Count",
    sourceUrl: "https://medlineplus.gov/lab-tests/complete-blood-count-cbc/",
  },
  platelets: {
    explanation: "Platelets help blood clot, which helps stop bleeding.",
    source: "MedlinePlus: Complete Blood Count",
    sourceUrl: "https://medlineplus.gov/lab-tests/complete-blood-count-cbc/",
  },
  glucose: {
    explanation: "Glucose is a type of sugar in the blood and an important energy source for the body.",
    source: "MedlinePlus: Blood Glucose Test",
    sourceUrl: "https://medlineplus.gov/lab-tests/blood-glucose-test/",
  },
  cholesterol: {
    explanation: "A total cholesterol test measures cholesterol in the blood, including HDL and LDL cholesterol.",
    source: "MedlinePlus: Cholesterol Levels",
    sourceUrl: "https://medlineplus.gov/lab-tests/cholesterol-levels/",
  },
  rbc: {
    explanation: "Red blood cells carry oxygen from the lungs to the rest of the body.",
    source: "MedlinePlus: Complete Blood Count",
    sourceUrl: "https://medlineplus.gov/lab-tests/complete-blood-count-cbc/",
  },
};

const CLASSIFICATION_STATUSES = new Set(["NORMAL", "REVIEW", "ATTENTION"]);
const DOCUMENT_TYPES = new Set([
  "asha_worker_note",
  "automated_sms",
  "discharge_summary",
  "er_triage_notes",
  "hospital_billing",
  "insurance_claim",
  "lab_report",
  "opd_slip",
  "phc_register",
  "prescription",
  "radiology_report",
  "referral_letter",
  "surgical_note",
  "telemedicine_transcript",
]);

function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function DocumentTypeCard({ documentType }) {
  const hasCategory = Boolean(
    documentType?.status === "predicted"
      && typeof documentType.category === "string"
      && DOCUMENT_TYPES.has(documentType.category),
  );
  const category = hasCategory
    ? documentType.category.replaceAll("_", " ")
    : "Category unavailable";
  const uncertainty = typeof documentType?.uncertainty === "string"
    ? documentType.uncertainty
    : "No document-type result was provided for this analysis.";

  return (
    <section className="document-type-card" aria-label="AI-generated document category">
      <span className="page-overline">AI-GENERATED DOCUMENT CATEGORY</span>
      <h2>{category}</h2>
      <p>{uncertainty}</p>
      <small>
        This English-only synthetic-data prototype has not been validated on real-world
        reports. A document category is not a diagnosis.
      </small>
    </section>
  );
}

function readStoredResult() {
  try {
    const stored = sessionStorage.getItem("medai_result");
    if (!stored) return { kind: "missing" };

    const result = JSON.parse(stored);
    if (!isRecord(result)) return { kind: "invalid" };
    if (result.success === false) return { kind: "unreadable", result };
    if (
      result.success !== true
      || !isRecord(result.medical_data)
    ) {
      return { kind: "invalid" };
    }

    return { kind: "analysis", result };
  } catch {
    return { kind: "invalid" };
  }
}

function EmptyResult({ overline, title, description, flags = [], documentType = null }) {
  return (
    <div className="results-page">
      <Link to="/upload" className="back-button">
        <ArrowLeft size={17} />
        Analyze Another Report
      </Link>

      <div className="results-header">
        <span className="page-overline">{overline}</span>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {documentType && <DocumentTypeCard documentType={documentType} />}
      {flags.length > 0 && (
        <ul className="empty-result-flags" aria-label="Analysis review notes">
          {flags.map((flag, index) => <li key={`${flag}-${index}`}>{flag}</li>)}
        </ul>
      )}
    </div>
  );
}

function Results() {
  const stored = readStoredResult();

  if (stored.kind === "missing") {
    return (
      <EmptyResult
        overline="NO REPORT"
        title="No Analysis Found"
        description="Please upload and analyze a medical report first."
      />
    );
  }

  if (stored.kind === "invalid") {
    return (
      <EmptyResult
        overline="RESULT UNAVAILABLE"
        title="Analysis Could Not Be Loaded"
        description="The saved result is incomplete or unreadable. Upload the report again to create a new analysis."
      />
    );
  }

  if (stored.kind === "unreadable") {
    return (
      <EmptyResult
        overline="REPORT UNREADABLE"
        title="No Readable Text Found"
        description={
          typeof stored.result.message === "string"
            ? stored.result.message
            : "MEDAI could not read text from this report. Try a clearer PDF or image."
        }
      />
    );
  }

  const { result } = stored;
  const rawDocumentType = isRecord(result.document_type)
    ? result.document_type
    : null;
  const documentType = {
    status: rawDocumentType?.status,
    category: rawDocumentType?.category,
    uncertainty: rawDocumentType?.uncertainty,
  };
  const extractedParameters = PARAMETERS.map((parameter) => ({
    ...parameter,
    value: Number.isFinite(result.medical_data[parameter.key])
      ? result.medical_data[parameter.key]
      : null,
  }));
  const availableCount = extractedParameters.filter(
    (parameter) => parameter.value !== null,
  ).length;
  const classification = isRecord(result.classification)
    ? result.classification
    : null;
  const flags = Array.isArray(classification?.flags)
    ? classification.flags.filter((flag) => typeof flag === "string")
    : [];

  if (availableCount === 0) {
    return (
      <EmptyResult
        overline="NO VALUES EXTRACTED"
        title="No Supported Values Found"
        description="Text was read, but MEDAI could not identify any supported values. Classification is unavailable; review the report and its units."
        flags={flags}
        documentType={documentType}
      />
    );
  }

  const isPartial = availableCount < PARAMETERS.length;
  const classificationStatus = typeof classification?.status === "string"
    ? classification.status.toUpperCase()
    : "";
  const hasClassification = Boolean(
    classification
      && CLASSIFICATION_STATUSES.has(classificationStatus)
      && Number.isFinite(classification.confidence)
      && classification.confidence >= 0
      && classification.confidence <= 1,
  );
  const displayStatus = isPartial
    ? "REVIEW"
    : hasClassification
      ? classificationStatus
      : "UNAVAILABLE";
  const showConfidence = !isPartial && hasClassification;
  const statusDescription = isPartial
    ? "Some supported values are missing. This is not a complete classification."
    : hasClassification
      ? "Prototype screening classification"
      : "Extraction completed, but no valid classification was provided.";
  const statusCardClass = isPartial
    ? "status-partial"
    : hasClassification
      ? "status-complete"
      : "status-incomplete";
  const overline = isPartial
    ? "PARTIAL EXTRACTION"
    : hasClassification
      ? "ANALYSIS COMPLETE"
      : "CLASSIFICATION UNAVAILABLE";

  return (
    <div className="results-page">
      <Link to="/upload" className="back-button">
        <ArrowLeft size={17} />
        Analyze Another Report
      </Link>

      <div className="results-header">
        <span className="page-overline">{overline}</span>
        <h1>Medical Report Results</h1>
        <p>
          {isPartial
            ? "Only the values shown below were extracted. Missing values remain unavailable."
            : "Review the values extracted from the uploaded report."}
        </p>
      </div>

      <div className={`result-status-card ${statusCardClass}`}>
        <div className="result-status-icon">
          <CheckCircle2 size={34} />
        </div>

        <div>
          <span className="result-label">
            {isPartial ? "EXTRACTION STATUS" : "OVERALL STATUS"}
          </span>
          <h2 data-status={displayStatus}>{displayStatus}</h2>
          <p>{statusDescription}</p>
        </div>

        {showConfidence && (
          <div className="confidence-box">
            <span>CONFIDENCE</span>
            <strong>{Math.round(classification.confidence * 100)}%</strong>
          </div>
        )}
      </div>

      <DocumentTypeCard documentType={documentType} />

      <div className="results-section">
        <div className="section-heading">
          <div>
            <span className="page-overline">EXTRACTED DATA</span>
            <h2>Medical Parameters</h2>
          </div>
          <FileText size={22} />
        </div>

        <div className="parameter-grid">
          {extractedParameters.map((parameter) => {
            const Icon = parameter.icon;
            return (
              <div className="parameter-card" key={parameter.key}>
                <div className="parameter-icon">
                  <Icon size={20} />
                </div>
                <span>{parameter.name}</span>
                <strong>{parameter.value ?? "N/A"}</strong>
                <small>{parameter.unit}</small>
                {parameter.value !== null && (
                  <div className="parameter-education">
                    <p>{PARAMETER_EDUCATION[parameter.key].explanation}</p>
                    <a
                      href={PARAMETER_EDUCATION[parameter.key].sourceUrl}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {PARAMETER_EDUCATION[parameter.key].source}
                    </a>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div className={`report-summary-card ${isPartial ? "summary-partial" : ""}`}>
        <div className="summary-icon">
          <CheckCircle2 size={22} />
        </div>
        <div>
          <span className="result-label">SCREENING SUMMARY</span>
          {isPartial ? (
            <>
              <h3>Interpretation Incomplete</h3>
              <p>
                Missing values are not treated as normal. Review the available
                extracted values and consult a qualified healthcare professional.
              </p>
              {flags.length > 0 && (
                <ul>
                  {flags.map((flag, index) => <li key={`${flag}-${index}`}>{flag}</li>)}
                </ul>
              )}
            </>
          ) : !hasClassification ? (
            <>
              <h3>Classification unavailable</h3>
              <p>
                Extracted values are shown, but no valid screening result was
                returned. Do not interpret this as a normal result.
              </p>
            </>
          ) : flags.length === 0 ? (
            <>
              <h3>No parameters flagged</h3>
              <p>
                The extracted values did not trigger any of the current
                prototype screening rules.
              </p>
            </>
          ) : (
            <>
              <h3>Prototype screening notes</h3>
              <ul>
                {flags.map((flag, index) => <li key={`${flag}-${index}`}>{flag}</li>)}
              </ul>
            </>
          )}
        </div>
      </div>

      <div className="medical-disclaimer">
        <strong>Important</strong>
        <p>
          MEDAI is an educational and informational prototype. This
          classification does not constitute a medical diagnosis or medical
          advice. Always consult a qualified healthcare professional for
          interpretation of medical reports.
        </p>
      </div>
    </div>
  );
}

export default Results;
