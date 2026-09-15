const STEPS = [
  { icon: "📷", title: "Upload a photo", text: "Take or select a photo of the damaged vehicle." },
  { icon: "🔍", title: "AI detects damage", text: "Damage type and severity are identified automatically." },
  { icon: "🧾", title: "Get an instant estimate", text: "A repair quotation is generated in seconds." },
];

export default function HowItWorks() {
  return (
    <div className="how-it-works">
      {STEPS.map((step, i) => (
        <div className="how-it-works-step" key={step.title}>
          <span className="how-it-works-icon">{step.icon}</span>
          <div>
            <strong>
              {i + 1}. {step.title}
            </strong>
            <p>{step.text}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
