"use client";

import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { AgentAction } from "@/lib/types";
import { ErrorState, Skeleton } from "@/components/ui/Feedback";
import { formatDate } from "@/lib/utils";

type Activity = {
  items: AgentAction[];
  summary: {
    revenue_analysed: number;
    opportunities: number;
    recommendations: number;
    auto_approved: number;
    needs_approval: number;
    payment_links: number;
  };
};

export default function AgentsPage() {
  const [data, setData] = useState<Activity | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    api
      .activity()
      .then((d) => setData(d as Activity))
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed"));
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 8000);
    return () => clearInterval(t);
  }, [load]);

  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!data) return <Skeleton className="h-80" />;
  const s = data.summary;

  return (
    <div className="space-y-6">
      <div>
        <p className="eyebrow">Agents</p>
        <h2 className="mt-1 font-display text-3xl">Activity timeline</h2>
        <p className="mt-2 text-sm text-ink-700/70">These counters come from stored AgentAction and ledger records, not placeholders.</p>
      </div>
      <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        <Pulse title="Revenue Agent" body={`Analysed ${s.revenue_analysed} transactions`} />
        <Pulse title="Recovery Agent" body={`Identified ${s.opportunities} opportunities`} />
        <Pulse title="Recovery Agent" body={`${s.recommendations} recommendation events`} />
        <Pulse title="RecoveryGuard" body={`Approved ${s.auto_approved} low-risk actions`} />
        <Pulse title="RecoveryGuard" warn body={`${s.needs_approval} actions require human approval`} />
        <Pulse title="Razorpay Agent" body={`Created ${s.payment_links} payment links`} />
      </section>
      <section className="panel p-5">
        <ul className="space-y-4">
          {data.items.map((a) => (
            <li key={a.id} className="border-b border-ink-900/5 pb-4 last:border-0">
              <p className="text-sm">
                <span className="font-medium">{a.agent_name}</span>
                <span className="text-mist-400"> · {a.action} · {a.decision.replaceAll("_", " ")}</span>
              </p>
              <p className="mt-1 text-sm text-ink-700/80">{a.reason}</p>
              <p className="mt-1 text-xs text-mist-400">{formatDate(a.created_at)}</p>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

function Pulse({ title, body, warn }: { title: string; body: string; warn?: boolean }) {
  return (
    <div className="panel p-4">
      <p className="text-xs uppercase tracking-wide text-mist-400">{title}</p>
      <p className={`mt-2 text-sm font-medium ${warn ? "text-warn-500" : "text-gain-500"}`}>{warn ? "⚠ " : "✓ "}{body}</p>
    </div>
  );
}
