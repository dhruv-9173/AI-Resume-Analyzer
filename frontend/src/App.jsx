import { useState } from "react";
import UploadSection from "./components/UploadSection";
import ScoreCard from "./components/ScoreCard";
import SectionFeedback from "./components/SectionFeedback";
import SkillsGap from "./components/SkillsGap";
import ATSReport from "./components/ATSReport";
import Recommendations from "./components/Recommendations";
import LoadingState from "./components/LoadingState";
import { analyseResume } from "./utils/api";

const TABS = [
  { id: "overview", label: "Overview" },
  { id: "sections", label: "Sections" },
  { id: "skills", label: "Skills Gap" },
  { id: "ats", label: "ATS Report" },
  { id: "suggestions", label: "Suggestions" },
];

export default function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("overview");

  const handleAnalyse = async (file, jobDescription) => {
    setLoading(true);
    setError("");
    setResult(null);
    setActiveTab("overview");

    try {
      const data = await analyseResume(file, jobDescription);
      setResult(data);
    } catch (err) {
      const msg =
        err?.response?.data?.detail ||
        err.message ||
        "Something went wrong. Please try again.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setError("");
    setActiveTab("overview");
  };

  return (
    <div className="min-h-screen">
      <header className="bg-slate-800 text-white border-b border-slate-700">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-semibold">AI Resume Analyzer</h1>
            <p className="text-xs text-slate-300">
              RAG Powered ATS and resume feedback tool
            </p>
          </div>

          <div className="flex items-center gap-3">
            {result && (
              <button onClick={handleReset} className="btn-secondary text-sm">
                New Analysis
              </button>
            )}
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-slate-200 hover:text-white underline-offset-2 hover:underline"
            >
              API Docs
            </a>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8 space-y-6">
        {!result && !loading && (
          <section className="panel p-6">
            <h2 className="text-lg font-semibold text-slate-900 mb-2">
              Upload your resume for analysis
            </h2>
            <p className="text-sm text-slate-600 mb-5">
              This tool evaluates ATS compatibility, section quality, and
              missing skills based on the job description.
            </p>
            <UploadSection onAnalyse={handleAnalyse} loading={loading} />
          </section>
        )}

        {loading && (
          <section className="panel p-6">
            <LoadingState />
          </section>
        )}

        {error && !loading && (
          <section className="panel p-6 border-red-200 bg-red-50">
            <h3 className="text-base font-semibold text-red-700 mb-2">
              Analysis failed
            </h3>
            <p className="text-sm text-red-600 mb-4">{error}</p>
            <button onClick={handleReset} className="btn-primary">
              Try Again
            </button>
          </section>
        )}

        {result && !loading && (
          <section className="panel p-6">
            <div className="border-b border-slate-200 mb-6">
              <div className="flex flex-wrap gap-2 pb-3">
                {TABS.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={
                      activeTab === tab.id
                        ? "tab-button tab-button-active"
                        : "tab-button"
                    }
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            <div key={activeTab}>
              {activeTab === "overview" && <ScoreCard data={result} />}
              {activeTab === "sections" && (
                <SectionFeedback sectionFeedback={result.section_feedback} />
              )}
              {activeTab === "skills" && (
                <SkillsGap skillsGap={result.skills_gap} />
              )}
              {activeTab === "ats" && (
                <ATSReport
                  atsReport={result.ats_report}
                  atsScore={result.ats_score}
                />
              )}
              {activeTab === "suggestions" && (
                <Recommendations recommendations={result.top_recommendations} />
              )}
            </div>

            {result.metadata && (
              <div className="mt-6 pt-4 border-t border-slate-200 text-sm text-slate-600 flex flex-wrap gap-4">
                <span>File: {result.metadata.filename}</span>
                <span>RAG chunks: {result.metadata.rag_chunks_used}</span>
                <span>Model: {result.metadata.model_used}</span>
                {result.metadata.job_description_provided && (
                  <span className="badge badge-success">
                    Job description provided
                  </span>
                )}
              </div>
            )}
          </section>
        )}
      </main>

      <footer className="text-center text-sm text-slate-500 py-6 border-t border-slate-200">
        Built with FastAPI and React
      </footer>
    </div>
  );
}
