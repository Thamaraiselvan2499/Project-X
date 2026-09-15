export default function QuotationTable({ quotation, modelMode }) {
  if (!quotation) return null;

  return (
    <div className="quotation">
      <h2>Repair Estimate</h2>
      {modelMode === "stub" && (
        <p className="stub-banner">
          Demo mode — no trained model weights found, showing placeholder detections.
        </p>
      )}
      {quotation.line_items.length === 0 ? (
        <p>No damage detected.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Damage</th>
              <th>Severity</th>
              <th>Cost</th>
            </tr>
          </thead>
          <tbody>
            {quotation.line_items.map((item, i) => (
              <tr key={i} className={item.needs_review ? "needs-review" : ""}>
                <td>{item.damage_type.replace(/_/g, " ")}</td>
                <td>{item.severity}</td>
                <td>
                  {quotation.currency} {item.cost.toFixed(2)}
                  {item.needs_review && <span title="Low confidence — verify manually"> ⚠</span>}
                </td>
              </tr>
            ))}
            <tr>
              <td colSpan={2}>Service fee</td>
              <td>
                {quotation.currency} {quotation.service_fee.toFixed(2)}
              </td>
            </tr>
            <tr className="total-row">
              <td colSpan={2}>Total</td>
              <td>
                {quotation.currency} {quotation.total.toFixed(2)}
              </td>
            </tr>
          </tbody>
        </table>
      )}
      {quotation.has_items_needing_review && (
        <p className="review-note">
          ⚠ Some detections have low confidence and should be verified by a person before quoting a customer.
        </p>
      )}
    </div>
  );
}
