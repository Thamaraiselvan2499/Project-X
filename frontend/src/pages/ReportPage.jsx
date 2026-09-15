function titleCase(s) {
  return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function ReportPage({ report, car, onAddMoreDamage, onStartOver }) {
  return (
    <div className="card">
      <h2>Repair estimate</h2>
      {car && (
        <p className="muted">
          {car.car_name} ({car.brand} {car.variant}) — {car.car_number}
        </p>
      )}

      {report.items.length === 0 ? (
        <p>No damage recorded yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Part</th>
              <th>Damage</th>
              <th>Severity</th>
              <th>Cost</th>
            </tr>
          </thead>
          <tbody>
            {report.items.map((item) => (
              <tr key={item.id} className={item.needs_review ? "needs-review" : ""}>
                <td>{titleCase(item.part)}</td>
                <td>{item.damage_type ? titleCase(item.damage_type) : "No damage found"}</td>
                <td>{item.severity ? titleCase(item.severity) : "—"}</td>
                <td>
                  {report.currency} {item.cost.toFixed(2)}
                  {item.needs_review && <span title="Low confidence — verify manually"> ⚠</span>}
                </td>
              </tr>
            ))}
            <tr>
              <td colSpan={3}>Service fee</td>
              <td>
                {report.currency} {report.service_fee.toFixed(2)}
              </td>
            </tr>
            <tr className="total-row">
              <td colSpan={3}>Total</td>
              <td>
                {report.currency} {report.total.toFixed(2)}
              </td>
            </tr>
          </tbody>
        </table>
      )}

      {report.has_items_needing_review && (
        <p className="review-note">
          ⚠ Some detections have low confidence and should be verified by a person before quoting the customer.
        </p>
      )}

      <div className="button-row">
        <button type="button" className="secondary" onClick={onAddMoreDamage}>
          Add another damaged part
        </button>
        <button type="button" onClick={onStartOver}>
          Finish
        </button>
      </div>
    </div>
  );
}
