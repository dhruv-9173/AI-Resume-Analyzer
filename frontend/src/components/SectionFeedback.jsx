import { useState } from "react";
import { getScoreColor, getScoreLabel } from "../utils/helpers";

function SectionCard({ sectionKey, section, index }) {
  const [open, setOpen] = useState(index < 2);
  const colors = getScoreColor(section.score);
  const label = sectionKey.charAt(0).toUpperCase() + sectionKey.slice(1);

  if (!section) return null;

  return (
    <div className="border border-slate-200 rounded-lg overflow-hidden bg-white">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-4 text-left hover:bg-slate-50"
      >
        <div>
          <p className="font-semibold text-slate-900">{label}</p>
          <p className="text-xs text-slate-500 mt-0.5">
            {section.exists === false
              ? "Section not found"
              : getScoreLabel(section.score)}
          </p>
        </div>

        <div className="flex items-center gap-4">
          <span className={`text-sm font-semibold ${colors.text}`}>
            {section.score}/100
          </span>
          <svg
            className={`w-4 h-4 text-slate-500 transition-transform duration-200 ${
              open ? "rotate-180" : ""
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </div>
      </button>

      <div className="h-0.5 bg-slate-200 mx-4">
        <div
          className="h-full"
          style={{
            width: open ? `${section.score}%` : "0%",
            background: colors.stroke,
            transition: "width 0.4s ease",
          }}
        />
      </div>

      {open && (
        <div className="p-4 space-y-3">
          <p className="text-sm text-slate-700 leading-6">{section.feedback}</p>

          {section.improvements?.length > 0 && (
            <div>
              <p className="text-sm font-semibold text-slate-900 mb-2">
                Improvements
              </p>
              <ul className="list-disc list-inside space-y-1 text-sm text-slate-700">
                {section.improvements.map((imp, i) => (
                  <li key={i}>{imp}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function SectionFeedback({ sectionFeedback }) {
  if (!sectionFeedback) return null;

  const sections = Object.entries(sectionFeedback);

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-slate-900">
          Section Feedback
        </h3>
        <p className="text-sm text-slate-600">
          Click a section to view detailed feedback and improvements.
        </p>
      </div>

      {sections.map(([key, section], i) => (
        <SectionCard key={key} sectionKey={key} section={section} index={i} />
      ))}
    </div>
  );
}
