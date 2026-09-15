import { useEffect, useState } from "react";

import { api } from "./api.js";
import CarDetailsPage from "./pages/CarDetailsPage.jsx";
import CarViewerPage from "./pages/CarViewerPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import ReportPage from "./pages/ReportPage.jsx";
import UploadPage from "./pages/UploadPage.jsx";

export default function App() {
  const [step, setStep] = useState("login"); // login | car-details | viewer | upload | report
  const [taxonomy, setTaxonomy] = useState(null);
  const [car, setCar] = useState(null);
  const [reportId, setReportId] = useState(null);
  const [report, setReport] = useState(null);
  const [pendingParts, setPendingParts] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getTaxonomy().then(setTaxonomy).catch((err) => setError(err.message));
  }, []);

  async function handleLogin(mobileNumber, carNumber) {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.login(mobileNumber, carNumber);
      localStorage.setItem("px_mobile_number", mobileNumber);
      localStorage.setItem("px_car_number", carNumber);
      setCar(response.car);
      setStep(response.car.is_new ? "car-details" : "viewer");
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleCarDetailsSubmit(details) {
    setIsLoading(true);
    setError(null);
    try {
      const updatedCar = await api.updateCar(car.car_number, details);
      setCar(updatedCar);
      setStep("viewer");
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }

  function handleTogglePart(part) {
    setPendingParts((prev) => (prev.includes(part) ? prev.filter((p) => p !== part) : [...prev, part]));
  }

  async function handleViewerContinue() {
    setError(null);
    try {
      let currentReportId = reportId;
      if (currentReportId == null) {
        const created = await api.createReport(car.car_number);
        currentReportId = created.report_id;
        setReportId(currentReportId);
      }
      setStep("upload");
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleUploadSubmit(files) {
    setIsLoading(true);
    setError(null);
    try {
      let latestReport = null;
      for (const part of pendingParts) {
        const response = await api.addReportItem(reportId, part, files[part]);
        latestReport = response.report;
      }
      setReport(latestReport);
      setPendingParts([]);
      setStep("report");
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }

  function handleAddMoreDamage() {
    setStep("viewer");
  }

  function handleStartOver() {
    setStep("login");
    setCar(null);
    setReportId(null);
    setReport(null);
    setPendingParts([]);
  }

  if (!taxonomy) {
    return (
      <div className="app">
        <header>
          <h1>Project X</h1>
        </header>
        <p className="muted">Loading…</p>
      </div>
    );
  }

  return (
    <div className="app">
      <header>
        <h1>Project X</h1>
        <p className="tagline">AI-powered car damage detection &amp; repair estimator</p>
      </header>

      {step === "login" && <LoginPage onLogin={handleLogin} isLoading={isLoading} error={error} />}

      {step === "car-details" && (
        <CarDetailsPage
          taxonomy={taxonomy}
          initialCar={car}
          onSubmit={handleCarDetailsSubmit}
          isLoading={isLoading}
          error={error}
        />
      )}

      {step === "viewer" && (
        <CarViewerPage
          bodyType={car.body_type || taxonomy.body_types[0]}
          selectedParts={pendingParts}
          onTogglePart={handleTogglePart}
          onContinue={handleViewerContinue}
        />
      )}

      {step === "upload" && (
        <UploadPage
          parts={pendingParts}
          onSubmit={handleUploadSubmit}
          isLoading={isLoading}
          error={error}
          onBack={() => setStep("viewer")}
        />
      )}

      {step === "report" && report && (
        <ReportPage report={report} car={car} onAddMoreDamage={handleAddMoreDamage} onStartOver={handleStartOver} />
      )}
    </div>
  );
}
