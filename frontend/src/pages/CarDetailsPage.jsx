import { useState } from "react";

function titleCase(s) {
  return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function CarDetailsPage({ taxonomy, initialCar, onSubmit, isLoading, error }) {
  const [carName, setCarName] = useState(initialCar?.car_name || "");
  const [brand, setBrand] = useState(initialCar?.brand || "");
  const [variant, setVariant] = useState(initialCar?.variant || "");
  const [bodyType, setBodyType] = useState(initialCar?.body_type || taxonomy.body_types[0] || "");
  const [damageTypeHint, setDamageTypeHint] = useState(initialCar?.damage_type_hint || "");

  function handleSubmit(event) {
    event.preventDefault();
    onSubmit({ car_name: carName, brand, variant, body_type: bodyType, damage_type_hint: damageTypeHint || null });
  }

  return (
    <div className="card">
      <h2>Car details</h2>
      <form onSubmit={handleSubmit} className="form">
        <label>
          Car name
          <input type="text" required placeholder="Brezza" value={carName} onChange={(e) => setCarName(e.target.value)} />
        </label>
        <label>
          Brand
          <input type="text" required placeholder="Maruti Suzuki" value={brand} onChange={(e) => setBrand(e.target.value)} />
        </label>
        <label>
          Variant
          <input type="text" required placeholder="ZXI" value={variant} onChange={(e) => setVariant(e.target.value)} />
        </label>
        <label>
          Body type
          <select value={bodyType} onChange={(e) => setBodyType(e.target.value)}>
            {taxonomy.body_types.map((bt) => (
              <option key={bt} value={bt}>
                {titleCase(bt)}
              </option>
            ))}
          </select>
        </label>
        <label>
          Damage type (your best guess — optional)
          <select value={damageTypeHint} onChange={(e) => setDamageTypeHint(e.target.value)}>
            <option value="">Not sure / multiple</option>
            {taxonomy.damage_classes.map((dc) => (
              <option key={dc} value={dc}>
                {titleCase(dc)}
              </option>
            ))}
          </select>
        </label>
        {error && <p className="error-text">{error}</p>}
        <button type="submit" disabled={isLoading}>
          {isLoading ? "Saving…" : "Continue"}
        </button>
      </form>
    </div>
  );
}
