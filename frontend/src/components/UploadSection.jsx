import { useState, useRef, useCallback } from "react";
import { formatFileSize } from "../utils/helpers";

const ACCEPTED = [".pdf", ".docx"];

export default function UploadSection({ onAnalyse, loading }) {
  const [resumeFile, setResumeFile] = useState(null);
  const [jobDescription, setJobDescription] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState("");
  const fileInputRef = useRef(null);

  const validateFile = (file) => {
    const name = file.name.toLowerCase();
    if (!name.endsWith(".pdf") && !name.endsWith(".docx")) {
      return "Only PDF and DOCX files are supported.";
    }
    if (file.size > 10 * 1024 * 1024) {
      return "File size must be under 10MB.";
    }
    return null;
  };

  const handleFile = useCallback((file) => {
    setError("");
    const err = validateFile(file);
    if (err) {
      setError(err);
      return;
    }
    setResumeFile(file);
  }, []);

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };
  const handleDragLeave = () => setDragOver(false);

  const handleSubmit = () => {
    if (!resumeFile) {
      setError("Please upload your resume first.");
      return;
    }
    onAnalyse(resumeFile, jobDescription);
  };

  const fileIcon = resumeFile?.name.toLowerCase().endsWith(".pdf") ? (
    <svg
      className="w-5 h-5 text-red-400"
      fill="currentColor"
      viewBox="0 0 24 24"
    >
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 1.5L18.5 9H13V3.5zM8 17h8v1H8v-1zm0-3h8v1H8v-1zm0-3h5v1H8v-1z" />
    </svg>
  ) : (
    <svg
      className="w-5 h-5 text-blue-400"
      fill="currentColor"
      viewBox="0 0 24 24"
    >
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 1.5L18.5 9H13V3.5z" />
    </svg>
  );

  return (
    <div className="w-full space-y-5">
      <div>
        <label className="field-label">
          Resume <span className="text-red-600">*</span>
        </label>

        <div
          onClick={() => !resumeFile && fileInputRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          className={`
            dashed-dropzone transition-colors cursor-pointer
            ${
              dragOver
                ? "border-blue-500 bg-blue-50"
                : resumeFile
                ? "border-emerald-500 bg-emerald-50 cursor-default"
                : "hover:border-slate-400"
            }
          `}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx"
            className="hidden"
            onChange={(e) =>
              e.target.files?.[0] && handleFile(e.target.files[0])
            }
          />

          {resumeFile ? (
            <div className="p-4 flex items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-md bg-white border border-slate-300 flex items-center justify-center">
                  {fileIcon}
                </div>
                <div>
                  <p className="font-medium text-slate-900">
                    {resumeFile.name}
                  </p>
                  <p className="text-sm text-slate-600">
                    {formatFileSize(resumeFile.size)}
                  </p>
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setResumeFile(null);
                  setError("");
                }}
                className="w-8 h-8 rounded-md flex items-center justify-center text-slate-500 hover:text-red-600 hover:bg-red-100 transition-colors"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
          ) : (
            <div className="p-8 text-center">
              <div className="w-12 h-12 rounded-md bg-white border border-slate-300 flex items-center justify-center mx-auto mb-3">
                <svg
                  className={`w-6 h-6 ${
                    dragOver ? "text-blue-600" : "text-slate-500"
                  }`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  />
                </svg>
              </div>
              <p className="font-medium text-slate-900 mb-1">
                {dragOver ? "Drop the file here" : "Drag and drop resume here"}
              </p>
              <p className="text-sm text-slate-600">
                or click to browse (PDF or DOCX, max 10MB)
              </p>
            </div>
          )}
        </div>
      </div>

      <div>
        <label className="field-label">
          Job Description{" "}
          <span className="text-xs text-slate-500">(optional)</span>
        </label>
        <textarea
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          placeholder="Paste the job description to get better skills and keyword matching."
          rows={6}
          className="input-control resize-none leading-6"
        />
        <p className="text-xs text-slate-500 mt-2">
          If left blank, the app runs a general resume analysis.
        </p>
      </div>

      {error && (
        <div className="info-block border-red-200 bg-red-50 text-red-700">
          <svg
            className="w-4 h-4 inline mr-2"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
          {error}
        </div>
      )}

      <button
        onClick={handleSubmit}
        disabled={loading || !resumeFile}
        className="w-full btn-primary"
      >
        {loading ? (
          <>
            <svg
              className="w-5 h-5 animate-spin"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            Analyzing...
          </>
        ) : (
          "Analyze Resume"
        )}
      </button>

      <p className="text-xs text-slate-500">
        Accepted file types: {ACCEPTED.join(", ")}.
      </p>
    </div>
  );
}
