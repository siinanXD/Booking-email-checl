/** Einheitliche Farben für Admin-Diagramme. */
export const ADMIN_CHART = {
  indigo: "#4f46e5",
  emerald: "#10b981",
  amber: "#f59e0b",
  slate: "#94a3b8",
  rose: "#f43f5e",
  violet: "#8b5cf6",
} as const;

export const ACTIVITY_COLORS: Record<string, string> = {
  active: ADMIN_CHART.emerald,
  idle: ADMIN_CHART.amber,
  never: ADMIN_CHART.slate,
};

export const ACTIVITY_LABELS: Record<string, string> = {
  active: "Aktiv (7 Tage)",
  idle: "Inaktiv",
  never: "Noch nie",
};

export const STATUS_COLORS: Record<string, string> = {
  active: ADMIN_CHART.emerald,
  pending: ADMIN_CHART.amber,
  rejected: ADMIN_CHART.rose,
  suspended: ADMIN_CHART.slate,
};

export const STATUS_LABELS: Record<string, string> = {
  active: "Freigeschaltet",
  pending: "Ausstehend",
  rejected: "Abgelehnt",
  suspended: "Gesperrt",
};
