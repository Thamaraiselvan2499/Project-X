import { useState } from "react";

export default function LoginPage({ onLogin, isLoading, error }) {
  const [mobileNumber, setMobileNumber] = useState(localStorage.getItem("px_mobile_number") || "");
  const [carNumber, setCarNumber] = useState(localStorage.getItem("px_car_number") || "");

  function handleSubmit(event) {
    event.preventDefault();
    onLogin(mobileNumber.trim(), carNumber.trim().toUpperCase());
  }

  return (
    <div className="card">
      <h2>Log in</h2>
      <p className="muted">
        Enter your mobile number and car (registration) number. First time here? An account is created
        automatically — no OTP needed at this stage.
      </p>
      <form onSubmit={handleSubmit} className="form">
        <label>
          Mobile number
          <input
            type="tel"
            required
            pattern="[0-9]{6,15}"
            placeholder="9876543210"
            value={mobileNumber}
            onChange={(e) => setMobileNumber(e.target.value)}
          />
        </label>
        <label>
          Car number
          <input
            type="text"
            required
            placeholder="TN01AB1234"
            value={carNumber}
            onChange={(e) => setCarNumber(e.target.value)}
          />
        </label>
        {error && <p className="error-text">{error}</p>}
        <button type="submit" disabled={isLoading}>
          {isLoading ? "Logging in…" : "Continue"}
        </button>
      </form>
    </div>
  );
}
