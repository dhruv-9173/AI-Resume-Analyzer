import { useEffect, useState } from "react";
import { getScoreColor, getScoreLabel } from "../utils/helpers";

function ScoreRing({ score, size = 120, strokeWidth = 8, color }) {
  const [animated, setAnimated] = useState(0);
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (animated / 100) * circumference;

  useEffect(() => {
    const timer = setTimeout(() => setAnimated(score), 100);
    return () => clearTimeout(timer);
  }, [score]);

  return (
    <svg width={size} height={size} className="-rotate-90">
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="#e2e8f0"
        strokeWidth={strokeWidth}
      />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        style={{ transition: "stroke-dashoffset 0.9s ease" }}
      />
    </svg>
  );
}

function MiniScore({ label, score }) {
  const colors = getScoreColor(score);

  return (
    <div className="border border-slate-200 rounded-md p-3 bg-slate-50">
      <p className="text-xs text-slate-500 uppercase tracking-wide">{label}</p>
      <p className={`text-2xl font-semibold ${colors.text}`}>{score}</p>
    </div>
  );
}

export default function ScoreCard({ data }) {
  const overallColors = getScoreColor(data.overall_score);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">
            {data.candidate_name || "Resume Analysis"}
          </h2>
          <div className="flex flex-wrap items-center gap-2 mt-2">
            {data.target_role && (
              <span className="badge badge-info">Role: {data.target_role}</span>
            )}
            {data.years_of_experience && (
              <span className="badge badge-warning">
                Experience: {data.years_of_experience}
              </span>
            )}
          </div>
        </div>

        <span
          className={`badge ${overallColors.bg} ${overallColors.text} ${overallColors.border} text-sm px-3 py-1`}
        >
          Overall: {getScoreLabel(data.overall_score)}
        </span>
      </div>

      <div className="grid md:grid-cols-[220px,1fr] gap-6 items-center border border-slate-200 rounded-lg p-4">
        <div className="relative flex-shrink-0 w-fit mx-auto">
          <ScoreRing
            score={data.overall_score}
            size={140}
            strokeWidth={9}
            color={overallColors.stroke}
          />
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`text-3xl font-semibold ${overallColors.text}`}>
              {data.overall_score}
            </span>
            <span className="text-xs text-slate-500 mt-0.5">Overall Score</span>
          </div>
        </div>

        <div className="space-y-3">
          {Object.entries(data.section_feedback || {}).map(([key, section]) => {
            if (!section?.exists && section?.score === 0) return null;

            const colors = getScoreColor(section.score);
            const label = key.charAt(0).toUpperCase() + key.slice(1);
            return (
              <div key={key}>
                <div className="flex items-center justify-between mb-1 text-sm">
                  <span className="text-slate-700">{label}</span>
                  <span className={colors.text}>{section.score}</span>
                </div>
                <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div
                    className="h-full"
                    style={{
                      width: `${section.score}%`,
                      backgroundColor: colors.stroke,
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <MiniScore label="ATS Score" score={data.ats_score} />
        <MiniScore
          label="Skills Match"
          score={data.skills_gap?.match_percentage || 0}
        />
        <MiniScore
          label="Keywords"
          score={data.ats_report?.keyword_match_score || 0}
        />
        <MiniScore
          label="Experience"
          score={data.section_feedback?.experience?.score || 0}
        />
      </div>

      {data.summary_verdict && (
        <div className="info-block">
          <p className="text-sm font-semibold text-slate-900 mb-1">
            Summary Verdict
          </p>
          <p className="text-sm text-slate-700">{data.summary_verdict}</p>
        </div>
      )}

      {data.strengths?.length > 0 && (
        <div>
          <p className="text-sm font-semibold text-slate-900 mb-2">Strengths</p>
          <div className="flex flex-wrap gap-2">
            {data.strengths.map((s, i) => (
              <span key={i} className="badge badge-success">
                {s}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
