import { useState } from "react";

function titleCase(s) {
  return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function UploadPage({ parts, onSubmit, isLoading, error, onBack }) {
  const [files, setFiles] = useState({});

  function handleFileChange(part, file) {
    setFiles((prev) => ({ ...prev, [part]: file }));
  }

  function handleSubmit(event) {
    event.preventDefault();
    onSubmit(files);
  }

  const allSelected = parts.every((part) => files[part]);

  return (
    <div className="card">
      <h2>Upload photos</h2>
      <p className="muted">Add one photo per part showing the damage clearly.</p>
      <form onSubmit={handleSubmit} className="form">
        {parts.map((part) => (
          <label key={part} className="upload-row">
            {titleCase(part)}
            <input
              type="file"
              accept="image/*"
              required
              onChange={(e) => handleFileChange(part, e.target.files?.[0] || null)}
            />
          </label>
        ))}
        {error && <p className="error-text">{error}</p>}
        <div className="button-row">
          <button type="button" className="secondary" onClick={onBack} disabled={isLoading}>
            Back
          </button>
          <button type="submit" disabled={isLoading || !allSelected}>
            {isLoading ? "Analyzing…" : "Analyze damage"}
          </button>
        </div>
      </form>
    </div>
  );
}
