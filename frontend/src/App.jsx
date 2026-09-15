import { useState } from "react";

import AnnotatedImage from "./components/AnnotatedImage.jsx";
import QuotationTable from "./components/QuotationTable.jsx";
import UploadPanel from "./components/UploadPanel.jsx";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

export default function App() {
  const [imageUrl, setImageUrl] = useState(null);
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleFileSelected(file) {
    setIsLoading(true);
    setError(null);
    setResult(null);
    setImageUrl(URL.createObjectURL(file));

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_BASE_URL}/api/annotate`, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `Request failed (${response.status})`);
      }
      setResult(await response.json());
    } catch (err) {
      setError(err.message || "Something went wrong analyzing this image.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="app">
      <header>
        <h1>Car Damage Annotator</h1>
        <p>Upload a photo of a damaged vehicle to detect damage and get an instant repair estimate.</p>
      </header>

      <UploadPanel onFileSelected={handleFileSelected} isLoading={isLoading} error={error} />

      {imageUrl && result && (
        <div className="results">
          <AnnotatedImage
            imageUrl={imageUrl}
            detections={result.detections}
            imageWidth={result.image_width}
            imageHeight={result.image_height}
          />
          <QuotationTable quotation={result.quotation} modelMode={result.model_mode} />
        </div>
      )}
    </div>
  );
}
