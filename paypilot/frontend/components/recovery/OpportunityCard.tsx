"use client";

import Link from "next/link";
import { formatINR, formatPct } from "@/lib/utils";
import type { Opportunity } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { GuardBadge, PriorityBadge, StatusBadge } from "@/components/ui/Status";

export function OpportunityCard({
  opportunity,
  onAnalyze,
  onRecover,
  onApprove,
  busy,
}: {
  opportunity: Opportunity;
  onAnalyze?: (id: number) => void;
  onRecover?: (id: number) => void;
  onApprove?: (id: number) => void;
  busy?: boolean;
}) {
  const needsHuman = (opportunity.amount > 10000 || opportunity.risk_level === "high" || opportunity.recommended_action === "manual_review") && opportunity.status === "pending";
  return (
    <article className="panel flex flex-col p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <Link href={`/customers/${opportunity.customer_id}`} className="font-medium hover:underline">
            {opportunity.customer_name}
          </Link>
          <p className="text-xs text-mist-400">{opportunity.customer_email}</p>
        </div>
        <PriorityBadge priority={opportunity.priority} />
      </div>
      <p className="mt-4 font-display text-3xl">{formatINR(opportunity.amount)}</p>
      <p className="mt-1 text-sm text-gain-500">Expected recovery {formatINR(opportunity.expected_recovery)} · {formatPct(opportunity.recovery_probability)}</p>
      <div className="mt-4 flex flex-wrap gap-2">
        <StatusBadge status={opportunity.status} />
        <StatusBadge status={opportunity.recommended_action} />
        {needsHuman ? <GuardBadge label="HUMAN APPROVAL REQUIRED" /> : opportunity.status === "pending" ? <GuardBadge label="AUTO APPROVED eligible" /> : null}
      </div>
      <p className="mt-4 text-sm text-ink-700/80">{opportunity.why_recover || opportunity.reason}</p>
      <p className="mt-2 text-xs text-mist-400">Failure: {opportunity.failure_reason || "n/a"} · {opportunity.payment_method}</p>
      <p className="mt-1 text-[11px] uppercase tracking-wide text-mist-400">
        {opportunity.ai_source === "openai" ? "OpenAI recommendation" : "Local recovery engine"}
      </p>
      <div className="mt-5 flex flex-wrap gap-2">
        <Button variant="secondary" disabled={busy} onClick={() => onAnalyze?.(opportunity.id)}>Analyze</Button>
        {needsHuman ? (
          <Button disabled={busy} onClick={() => onApprove?.(opportunity.id)}>Request Approval</Button>
        ) : opportunity.status === "pending" || opportunity.status === "approved" ? (
          <Button disabled={busy} onClick={() => onRecover?.(opportunity.id)}>Recover</Button>
        ) : null}
        <Link href={`/recovery/${opportunity.id}`} className="inline-flex items-center text-sm text-accent-600">Details</Link>
      </div>
    </article>
  );
}
