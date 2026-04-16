const STEPS = [
  "Extracting resume text",
  "Generating embeddings",
  "Querying knowledge base",
  "Building context",
  "Running AI analysis",
];

export default function LoadingState() {
  return (
    <div className="w-full max-w-xl mx-auto">
      <div className="flex items-center gap-3 mb-4">
        <svg
          className="w-5 h-5 animate-spin text-blue-600"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-30"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-90"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.37 0 0 5.37 0 12h4z"
          />
        </svg>
        <div>
          <p className="text-base font-semibold text-slate-900">
            Analyzing resume
          </p>
          <p className="text-sm text-slate-600">
            This usually takes 15 to 30 seconds.
          </p>
        </div>
      </div>

      <div className="space-y-2">
        {STEPS.map((step, i) => (
          <div key={step} className="info-block flex items-center gap-3">
            <span className="w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-xs font-semibold inline-flex items-center justify-center">
              {i + 1}
            </span>
            <span className="text-sm text-slate-700">{step}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
