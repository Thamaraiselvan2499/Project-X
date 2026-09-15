export default function UploadPanel({ onFileSelected, isLoading, error }) {
  function handleChange(event) {
    const file = event.target.files?.[0];
    if (file) onFileSelected(file);
  }

  return (
    <div className="upload-panel">
      <label className="upload-label">
        <input type="file" accept="image/*" onChange={handleChange} disabled={isLoading} />
        {isLoading ? "Analyzing image…" : "Choose a car photo to analyze"}
      </label>
      {error && <p className="error-text">{error}</p>}
    </div>
  );
}
