export const getScoreColor = (score) => {
  if (score >= 80)
    return {
      text: "text-emerald-400",
      stroke: "#10B981",
      bg: "bg-emerald-500/10",
      border: "border-emerald-500/20",
    };
  if (score >= 60)
    return {
      text: "text-yellow-400",
      stroke: "#FBBF24",
      bg: "bg-yellow-500/10",
      border: "border-yellow-500/20",
    };
  return {
    text: "text-red-400",
    stroke: "#F87171",
    bg: "bg-red-500/10",
    border: "border-red-500/20",
  };
};

export const getScoreLabel = (score) => {
  if (score >= 90) return "Excellent";
  if (score >= 80) return "Great";
  if (score >= 70) return "Good";
  if (score >= 60) return "Fair";
  if (score >= 40) return "Needs Work";
  return "Poor";
};

export const getPriorityColor = (priority) => {
  switch (priority?.toLowerCase()) {
    case "high":
      return "badge-danger";
    case "medium":
      return "badge-warning";
    case "low":
      return "badge-info";
    default:
      return "badge-info";
  }
};

export const formatFileSize = (bytes) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};
