export default function Recommendations({ recommendations }) {
  if (!recommendations?.length) return null;

  const high = recommendations.filter((r) => r.priority === "high");
  const medium = recommendations.filter((r) => r.priority === "medium");
  const low = recommendations.filter((r) => r.priority === "low");

  const groups = [
    {
      label: "High Priority",
      items: high,
      color: "text-red-700",
      bg: "bg-red-50",
      border: "border-red-200",
      badge: "badge-danger",
    },
    {
      label: "Medium Priority",
      items: medium,
      color: "text-yellow-700",
      bg: "bg-yellow-50",
      border: "border-yellow-200",
      badge: "badge-warning",
    },
    {
      label: "Nice to Have",
      items: low,
      color: "text-blue-700",
      bg: "bg-blue-50",
      border: "border-blue-200",
      badge: "badge-info",
    },
  ];

  return (
    <div>
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-slate-900">
          Top Recommendations
        </h3>
        <p className="text-sm text-slate-600">
          Actionable improvements ordered by priority.
        </p>
      </div>

      <div className="space-y-4">
        {groups.map(({ label, items, color, bg, border, badge }) => {
          if (!items.length) return null;
          return (
            <div
              key={label}
              className={`border rounded-lg p-4 ${border} ${bg}`}
            >
              <div className="flex items-center gap-2 mb-4">
                <p className={`text-sm font-semibold ${color}`}>{label}</p>
                <span className={`badge ${badge}`}>{items.length}</span>
              </div>
              <div className="space-y-3">
                {items.map((rec, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-3 border border-slate-200 bg-white rounded-md p-3"
                  >
                    <div
                      className={`w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0 mt-0.5 ${bg} border ${border}`}
                    >
                      <span className={`text-xs font-semibold ${color}`}>
                        {i + 1}
                      </span>
                    </div>
                    <div>
                      {rec.category && (
                        <span className="text-xs text-slate-500 uppercase tracking-wide">
                          {rec.category} ·{" "}
                        </span>
                      )}
                      <span className="text-sm text-slate-700 leading-relaxed">
                        {rec.recommendation}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
