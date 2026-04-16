import { getScoreColor } from "../utils/helpers";

function CheckItem({ text, passed }) {
  return (
    <div
      className={`flex items-start gap-3 p-3 rounded-md border text-sm ${
        passed
          ? "bg-emerald-50 border-emerald-200 text-emerald-700"
          : "bg-red-50 border-red-200 text-red-700"
      }`}
    >
      <div
        className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
          passed ? "bg-emerald-100" : "bg-red-100"
        }`}
      >
        {passed ? (
          <svg
            className="w-3 h-3 text-emerald-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={3}
              d="M5 13l4 4L19 7"
            />
          </svg>
        ) : (
          <svg
            className="w-3 h-3 text-red-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={3}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        )}
      </div>
      <span className="leading-relaxed">{text}</span>
    </div>
  );
}

function WarningItem({ text }) {
  return (
    <div className="flex items-start gap-3 p-3 rounded-md border bg-yellow-50 border-yellow-200 text-yellow-700 text-sm">
      <div className="w-5 h-5 rounded-full bg-yellow-100 flex items-center justify-center flex-shrink-0 mt-0.5">
        <svg
          className="w-3 h-3 text-yellow-600"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path
            fillRule="evenodd"
            d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
            clipRule="evenodd"
          />
        </svg>
      </div>
      <span className="leading-relaxed">{text}</span>
    </div>
  );
}

export default function ATSReport({ atsReport, atsScore }) {
  if (!atsReport) return null;

  const {
    passed_checks = [],
    failed_checks = [],
    warnings = [],
    keyword_match_score = 0,
    top_missing_keywords = [],
  } = atsReport;
  const colors = getScoreColor(atsScore);
  const totalChecks = passed_checks.length + failed_checks.length;
  const passRate =
    totalChecks > 0
      ? Math.round((passed_checks.length / totalChecks) * 100)
      : 0;

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-slate-900">
          ATS Compatibility Report
        </h3>
        <p className="text-sm text-slate-600">
          Resume quality checks for applicant tracking systems.
        </p>
      </div>

      <div className="border border-slate-200 rounded-lg p-4 bg-slate-50">
        <div className="flex items-center justify-between mb-5">
          <div>
            <p className="text-sm text-slate-600">ATS Score</p>
            <p className={`text-4xl font-semibold mt-1 ${colors.text}`}>
              {atsScore}
            </p>
          </div>
          <div className="text-right text-sm text-slate-600 space-y-1">
            <p>{passed_checks.length} passed</p>
            <p>{failed_checks.length} failed</p>
            {warnings.length > 0 && <p>{warnings.length} warnings</p>}
          </div>
        </div>

        <div className="h-2.5 bg-slate-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-emerald-500 rounded-full"
            style={{ width: `${passRate}%` }}
          />
        </div>
        <p className="text-xs text-slate-600 mt-2">{passRate}% checks passed</p>
      </div>

      <div className="border border-slate-200 rounded-lg p-4 bg-white">
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="font-semibold text-slate-900">Keyword Match</p>
            <p className="text-xs text-slate-600 mt-0.5">
              How well resume keywords match the job description.
            </p>
          </div>
          <span
            className={`text-2xl font-semibold ${
              getScoreColor(keyword_match_score).text
            }`}
          >
            {keyword_match_score}%
          </span>
        </div>

        {top_missing_keywords.length > 0 && (
          <div>
            <p className="text-sm font-semibold text-slate-900 mb-2">
              Top Missing Keywords
            </p>
            <div className="flex flex-wrap gap-2">
              {top_missing_keywords.map((kw, i) => (
                <span key={i} className="badge badge-danger">
                  {kw}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {failed_checks.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-semibold text-slate-900">Failed Checks</p>
          {failed_checks.map((check, i) => (
            <CheckItem key={i} text={check} passed={false} />
          ))}
        </div>
      )}

      {warnings.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-semibold text-slate-900">Warnings</p>
          {warnings.map((warn, i) => (
            <WarningItem key={i} text={warn} />
          ))}
        </div>
      )}

      {passed_checks.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-semibold text-slate-900">Passed Checks</p>
          {passed_checks.map((check, i) => (
            <CheckItem key={i} text={check} passed={true} />
          ))}
        </div>
      )}
    </div>
  );
}
