import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Upload, FileText, Trash2, ShieldCheck, CheckCircle2 } from "lucide-react";
import axios from "axios";
import "./UploadReport.css";

function UploadReport() {
  const navigate = useNavigate();

  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleFileChange = (event) => {
    const file = event.target.files[0];

    if (!file) return;

    setError("");
    setSuccess("");

    const allowedTypes = [
      "application/pdf",
      "image/png",
      "image/jpeg",
    ];

    if (!allowedTypes.includes(file.type)) {
      setError("Please upload a PDF, PNG, or JPG file.");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError("File size must be less than 10 MB.");
      return;
    }

    setSelectedFile(file);
  };

  const removeFile = () => {
    setSelectedFile(null);
    setError("");
    setSuccess("");
  };

  const analyzeReport = async () => {
    if (!selectedFile) {
      setError("Please select a medical report first.");
      return;
    }

    setUploading(true);
    setError("");
    setSuccess("");

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
        }
      );

      if (response.data.success) {
        setSuccess("Report analyzed successfully.");

        // Store analysis result temporarily
        sessionStorage.setItem(
          "medai_result",
          JSON.stringify(response.data)
        );

        // Open Results page
        navigate("/results");
      } else {
        setError(
          response.data.message || "Unable to analyze the report."
        );
      }
    } catch (err) {
      console.error(err);

      if (err.response?.data?.detail) {
        setError(
          typeof err.response.data.detail === "string"
            ? err.response.data.detail
            : "Backend validation error."
        );
      } else {
        setError(
          "Unable to connect to MEDAI backend. Make sure FastAPI is running."
        );
      }
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-page">

      <div className="upload-back">
        <button onClick={() => navigate("/")}>
          ← Back to Dashboard
        </button>
      </div>

      <div className="upload-header">
        <span>AI REPORT ANALYSIS</span>

        <h1>Upload Medical Report</h1>

        <p>
          Upload your medical report and let MEDAI extract and analyze
          important health information.
        </p>
      </div>

      {!selectedFile ? (
        <label className="upload-dropzone">
          <div className="upload-icon">
            <Upload size={32} />
          </div>

          <h2>Drop your medical report here</h2>

          <p>or browse files from your computer</p>

          <span className="browse-button">
            <FileText size={18} />
            Browse Files
          </span>

          <small>
            Supported formats: PDF, PNG, JPG · Maximum size: 10 MB
          </small>

          <input
            type="file"
            accept=".pdf,.png,.jpg,.jpeg"
            onChange={handleFileChange}
            hidden
          />
        </label>
      ) : (
        <div className="selected-file-card">

          <div className="file-left">

            <div className="file-icon">
              <FileText size={30} />
            </div>

            <div>
              <div className="file-ready">
                <CheckCircle2 size={15} />
                FILE READY
              </div>

              <h3>{selectedFile.name}</h3>

              <p>
                {(selectedFile.size / 1024).toFixed(1)} KB ·{" "}
                {selectedFile.type === "application/pdf"
                  ? "PDF Document"
                  : "Image"}
              </p>
            </div>

          </div>

          <button
            className="delete-file"
            onClick={removeFile}
          >
            <Trash2 size={19} />
          </button>

        </div>
      )}

      {error && (
        <div className="upload-error">
          {error}
        </div>
      )}

      {success && (
        <div className="upload-success">
          <CheckCircle2 size={18} />
          {success}
        </div>
      )}

      {selectedFile && (
        <button
          className="analyze-button"
          onClick={analyzeReport}
          disabled={uploading}
        >
          <Upload size={19} />

          {uploading ? "Analyzing Report..." : "Analyze Report"}
        </button>
      )}

      <div className="upload-security">

        <ShieldCheck size={24} />

        <div>
          <strong>Your report is protected</strong>

          <p>
            Your medical documents are processed securely and are only
            used for report analysis.
          </p>
        </div>

      </div>

    </div>
  );
}

export default UploadReport;