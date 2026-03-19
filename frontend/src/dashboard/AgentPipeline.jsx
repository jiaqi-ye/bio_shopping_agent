import { useState } from "react";
import ReasoningStepCard from "./ReasoningStepCard.jsx";

export default function AgentPipeline({ steps }) {
  const [openIndex, setOpenIndex] = useState(0);

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Agent Reasoning Pipeline</h2>
        <p className="muted">Expandable reasoning trace across the full procurement workflow.</p>
      </div>
      <div className="space-y-4">
        {steps.map((step, index) => (
          <ReasoningStepCard
            key={step.title}
            step={index + 1}
            title={step.title}
            summary={step.summary}
            details={step.details}
            isOpen={openIndex === index}
            onToggle={() => setOpenIndex(openIndex === index ? -1 : index)}
          />
        ))}
      </div>
    </div>
  );
}
