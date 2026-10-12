import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  CheckCircle2,
  FileText,
  ShieldCheck,
  Trash2,
  Upload,
} from "lucide-react";
import axios from "axios";
import "./UploadReport.css";
import { minimizeAnalysisForStorage } from "../utils/analysisStorage";
import { validateUploadFile } from "../utils/uploadValidation";

function UploadReport() {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [dropActive, setDropActive] = useState(false);

  const selectFile = (file) => {
    if (!file) return;

    setError("");
    setSuccess("");

    const validation = validateUploadFile(file);
    if (!validation.valid) {
      setError(validation.message);
      return;
    }

    setSelectedFile(file);
  };

  const handleFileChange = (event) => {
    selectFile(event.target.files?.[0]);
    event.target.value = "";
  };

  const isFileDrag = (event) => Array.from(event.dataTransfer?.types ?? []).includes("Files");

  const handleDragOver = (event) => {
    if (!isFileDrag(event)) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = "copy";
    setDropActive(true);
  };

  const handleDragLeave = (event) => {
    if (event.currentTarget.contains(event.relatedTarget)) return;
    setDropActive(false);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setDropActive(false);
    selectFile(event.dataTransfer.files?.[0]);
  };

  const removeFile = () => {
    setSelectedFile(null);
    setError("");
    setSuccess("");
  };

  const analyzeReport = async () => {
    if (!selectedFile) {
      setError(validateUploadFile(null).message);
      return;
    }

    setUploading(true);
    setError("");
    setSuccess("");

    try {
      sessionStorage.removeItem("medai_result");
    } catch {
      // Results will still be validated before display if storage is unavailable.
    }

    const openResults = (result) => {
      try {
        sessionStorage.setItem(
          "medai_result",
          JSON.stringify(minimizeAnalysisForStorage(result)),
        );
        navigate("/results");
      } catch {
        setError("The analysis finished, but its results could not be saved in this tab.");
      }
    };

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await axios.post(
        "http://127.0.0.1:8000/api/analyze",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        },
      );

      if (response.data?.success === true) {
        setSuccess("Report analyzed successfully.");
        openResults(response.data);
      } else if (response.data?.success === false) {
        openResults(response.data);
      } else {
        setError("The backend returned an incomplete analysis response. Please try again.");
      }
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;

      if (status === 503) {
        setError(
          "OCR is unavailable. Check that Tesseract and its English language data are configured, then retry.",
        );
      } else if (status === 504) {
        setError("OCR processing timed out. Try a clearer or shorter report.");
      } else if (status === 400 && typeof detail === "string" && /unreadable|could not be read/i.test(detail)) {
        setError("The report could not be read. Check that the file is valid and try a clearer copy.");
      } else if (typeof detail === "string") {
        setError(detail);
      } else {
        setError("Unable to connect to MEDAI backend. Make sure FastAPI is running.");
      }
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-page">
      <Link to="/" className="upload-back-link">
        <ArrowLeft size={16} />
        Back to Dashboard
      </Link>

      <header className="upload-header">
        <span className="page-eyebrow">REPORT ANALYSIS</span>
        <h1 className="page-title">Upload Medical Report</h1>
        <p className="page-subtitle">
          Add a supported PDF or image report to view any values and document
          categories MEDAI can identify.
        </p>
      </header>

      {!selectedFile ? (
        <label
          className={`upload-dropzone${dropActive ? " is-dragging" : ""}`}
          onDragEnter={handleDragOver}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <input
            className="upload-file-input"
            type="file"
            accept=".pdf,.png,.jpg,.jpeg"
            onChange={handleFileChange}
          />
          <span className="upload-dropzone-content">
            <span className="upload-icon"><Upload size={27} /></span>
            <strong>Drag and drop your report here</strong>
            <span className="upload-dropzone-support">or choose a file from your device</span>
            <span className="browse-button"><FileText size={17} /> Browse Files</span>
            <small id="upload-file-help">PDF, PNG, or JPG · Maximum size: 10 MB</small>
          </span>
        </label>
      ) : (
        <div className="selected-file-card">
          <div className="file-left">
            <div className="file-icon"><FileText size={25} /></div>
            <div className="selected-file-details">
              <div className="file-ready"><CheckCircle2 size={15} /> FILE READY</div>
              <h3>{selectedFile.name}</h3>
              <p>
                {(selectedFile.size / 1024).toFixed(1)} KB ·{" "}
                {selectedFile.type === "application/pdf" ? "PDF Document" : "Image"}
              </p>
            </div>
          </div>
          <button
            type="button"
            className="delete-file"
            onClick={removeFile}
            disabled={uploading}
            aria-label="Remove selected report"
          >
            <Trash2 size={19} />
          </button>
        </div>
      )}

      {error && <div className="upload-error" role="alert">{error}</div>}

      {success && (
        <div className="upload-success" role="status">
          <CheckCircle2 size={18} />
          {success}
        </div>
      )}

      {selectedFile && (
        <button
          type="button"
          className="analyze-button primary-button"
          onClick={analyzeReport}
          disabled={uploading}
          aria-busy={uploading}
        >
          <Upload size={17} />
          {uploading ? "Analyzing Report..." : "Analyze Report"}
        </button>
      )}

      <div className="upload-security surface-card">
        <ShieldCheck size={20} aria-hidden="true" />
        <div>
          <strong>Temporary report processing</strong>
          <p>
            MEDAI uses your report for this analysis. The browser keeps limited
            result information for the current session; no report history is available.
          </p>
        </div>
      </div>
    </div>
  );
}

export default UploadReport;
