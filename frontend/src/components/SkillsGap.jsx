import { getScoreColor } from "../utils/helpers";

function SkillPill({ skill, type }) {
  const styles = {
    matched: "bg-emerald-50 text-emerald-700 border-emerald-200",
    missing: "bg-red-50 text-red-700 border-red-200",
    bonus: "bg-blue-50 text-blue-700 border-blue-200",
  };
  const icons = {
    matched: "Matched",
    missing: "Missing",
    bonus: "Bonus",
  };
  return (
    <span
      className={`inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-xs border ${styles[type]}`}
    >
      <span className="font-semibold">{icons[type]}</span>
      {skill}
    </span>
  );
}

function SkillGroup({ title, skills, type, description }) {
  if (!skills?.length) return null;
  return (
    <div className="border border-slate-200 rounded-lg p-4 bg-white">
      <div className="flex items-center justify-between mb-4">
        <div>
          <p className="font-semibold text-slate-900">{title}</p>
          <p className="text-xs text-slate-600 mt-0.5">{description}</p>
        </div>
        <span
          className={`badge ${
            type === "matched"
              ? "badge-success"
              : type === "missing"
              ? "badge-danger"
              : "badge-info"
          }`}
        >
          {skills.length} {skills.length === 1 ? "skill" : "skills"}
        </span>
      </div>
      <div className="flex flex-wrap gap-2">
        {skills.map((skill, i) => (
          <SkillPill key={i} skill={skill} type={type} />
        ))}
      </div>
    </div>
  );
}

export default function SkillsGap({ skillsGap }) {
  if (!skillsGap) return null;

  const {
    matched_skills = [],
    missing_skills = [],
    bonus_skills = [],
    match_percentage = 0,
  } = skillsGap;
  const colors = getScoreColor(match_percentage);
  const total = matched_skills.length + missing_skills.length;
  const matchWidth =
    total > 0 ? (matched_skills.length / total) * 100 : match_percentage;

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-slate-900">
          Skills Gap Analysis
        </h3>
        <p className="text-sm text-slate-600">
          Comparison of skills found in your resume and job description.
        </p>
      </div>

      <div className="border border-slate-200 rounded-lg p-4 bg-slate-50">
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm text-slate-700">Skills Match</span>
          <span className={`text-2xl font-semibold ${colors.text}`}>
            {match_percentage}%
          </span>
        </div>

        <div className="h-3 bg-slate-200 rounded-full overflow-hidden flex">
          <div
            className="h-full bg-emerald-500"
            style={{ width: `${matchWidth}%` }}
          />
          <div
            className="h-full bg-red-400"
            style={{ width: `${100 - matchWidth}%` }}
          />
        </div>

        <div className="flex flex-wrap items-center gap-4 mt-3 text-xs text-slate-600">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-emerald-500" />
            <span>{matched_skills.length} matched</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-400" />
            <span>{missing_skills.length} missing</span>
          </div>
          {bonus_skills.length > 0 && (
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-500" />
              <span>{bonus_skills.length} bonus</span>
            </div>
          )}
        </div>
      </div>

      <SkillGroup
        title="Matched Skills"
        skills={matched_skills}
        type="matched"
        description="Skills from the JD that you already have"
      />
      <SkillGroup
        title="Missing Skills"
        skills={missing_skills}
        type="missing"
        description="Skills required by the JD that aren't on your resume"
      />
      <SkillGroup
        title="Bonus Skills"
        skills={bonus_skills}
        type="bonus"
        description="Additional skills you have beyond the JD requirements"
      />
    </div>
  );
}
