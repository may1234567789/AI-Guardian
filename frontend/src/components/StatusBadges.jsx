import { AlertCircle, CheckCircle2, XCircle } from "lucide-react";

export function DecisionBadge({ value }) {
  const decision = (value || "UNKNOWN").toUpperCase();
  return <span className={`badge decision-${decision.toLowerCase()}`}>{decision}</span>;
}

export function RiskBadge({ value }) {
  const risk = (value || "UNKNOWN").toUpperCase();
  return <span className={`badge risk-${risk.toLowerCase()}`}>{risk}</span>;
}

export function ConnectionBadge({ status }) {
  const isReady = status === "ok";
  const isDegraded = status === "degraded";
  const Icon = isReady ? CheckCircle2 : isDegraded ? AlertCircle : XCircle;
  const label = isReady ? "API connected" : isDegraded ? "API degraded" : "API offline";
  return <span className={`connection ${isReady ? "online" : isDegraded ? "warning" : "offline"}`}><Icon size={14} />{label}</span>;
}
