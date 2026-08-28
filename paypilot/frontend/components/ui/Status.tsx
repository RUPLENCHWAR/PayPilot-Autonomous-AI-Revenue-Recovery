import { Badge } from "@/components/ui/Badge";

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, "neutral" | "good" | "warn" | "bad" | "info"> = {
    captured: "good",
    recovered: "good",
    approved: "info",
    executed: "info",
    pending: "warn",
    failed: "bad",
    abandoned: "warn",
    refunded: "neutral",
    rejected: "bad",
    paid: "good",
    created: "info",
  };
  return <Badge tone={map[status] || "neutral"}>{status.replaceAll("_", " ")}</Badge>;
}

export function PriorityBadge({ priority }: { priority: string }) {
  const tone = priority === "HIGH" ? "good" : priority === "MEDIUM" ? "warn" : "bad";
  return <Badge tone={tone}>{priority}</Badge>;
}

export function GuardBadge({ label }: { label: string }) {
  const tone = label.includes("AUTO") ? "good" : label.includes("HUMAN") ? "warn" : "bad";
  return <Badge tone={tone}>{label}</Badge>;
}
