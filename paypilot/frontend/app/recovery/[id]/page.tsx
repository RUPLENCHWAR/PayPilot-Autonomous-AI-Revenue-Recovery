"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import type { AgentAction, Customer, Opportunity, PaymentLink, RecoveryAnalysis, Transaction } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { ErrorState, Skeleton } from "@/components/ui/Feedback";
import { GuardBadge, PriorityBadge, StatusBadge } from "@/components/ui/Status";
import { formatINR, formatPct, formatDate } from "@/lib/utils";

type Detail = {
  opportunity: Opportunity;
  payment_links: PaymentLink[];
  actions: AgentAction[];
  transaction: Transaction;
  customer: Customer;
};

export default function RecoveryDetailPage() {
  const params = useParams<{ id: string }>();
  const id = Number(params.id);
  const [data, setData] = useState<Detail | null>(null);
  const [analysis, setAnalysis] = useState<RecoveryAnalysis | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setData((await api.opportunity(id)) as Detail);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Not found");
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  async function act(fn: () => Promise<unknown>) {
    setBusy(true);
    setNotice("");
    try {
      const result = (await fn()) as { message?: string; analysis?: RecoveryAnalysis; demo_mode?: boolean };
      if (result.analysis) setAnalysis(result.analysis);
      setNotice(result.message || "Updated");
      await load();
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!data) return <Skeleton className="h-96" />;

  const { opportunity: o, customer, transaction, payment_links, actions } = data;
  const latestLink = [...payment_links].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  )[0];
  const demo = latestLink?.mode === "demo";

  return (
    <div className="space-y-6">
      <div>
        <Link href="/recovery" className="text-xs text-accent-600">Back to Recovery Center</Link>
        <h2 className="mt-2 font-display text-3xl">{customer.name}</h2>
        <p className="text-sm text-mist-400">{customer.email} · {transaction.external_transaction_id}</p>
      </div>
      {notice ? <p className="rounded-xl bg-mist-100 px-4 py-3 text-sm">{notice}</p> : null}

      <section className="grid gap-4 lg:grid-cols-3">
        <div className="panel p-6 lg:col-span-2">
          <p className="eyebrow">Opportunity</p>
          <p className="mt-2 font-display text-5xl">{formatINR(o.amount)}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            <PriorityBadge priority={o.priority} />
            <StatusBadge status={o.status} />
            <StatusBadge status={o.recommended_action} />
            {analysis?.guard ? <GuardBadge label={analysis.guard.policy_label} /> : null}
          </div>
          <dl className="mt-6 grid gap-4 sm:grid-cols-3 text-sm">
            <div><dt className="text-mist-400">Recovery probability</dt><dd className="mt-1 font-medium">{formatPct(o.recovery_probability)}</dd></div>
            <div><dt className="text-mist-400">Expected recovery</dt><dd className="mt-1 font-medium">{formatINR(o.expected_recovery)}</dd></div>
            <div><dt className="text-mist-400">Failure</dt><dd className="mt-1 font-medium">{o.failure_reason}</dd></div>
            <div><dt className="text-mist-400">Strategy</dt><dd className="mt-1 font-medium capitalize">{o.recovery_strategy?.replaceAll("_", " ")}</dd></div>
            <div><dt className="text-mist-400">Expected net</dt><dd className="mt-1 font-medium">{formatINR(o.expected_net_recovery)}</dd></div>
          </dl>
        </div>
        <div className="panel p-6 space-y-3">
          <p className="eyebrow">Actions</p>
          <Button className="w-full" disabled={busy} onClick={() => act(() => api.analyze(o.id))}>Analyze</Button>
          <Button className="w-full" disabled={busy} onClick={() => act(() => api.execute(o.id))}>Recover</Button>
          <Button className="w-full" variant="secondary" disabled={busy} onClick={() => act(() => api.approve(o.id))}>Approve & execute</Button>
          {latestLink && demo ? (
            <>
              <p className="text-xs text-warn-500">Demo Mode — No real payment was created.</p>
              <Button className="w-full" variant="secondary" disabled={busy} onClick={() => act(() => api.simulateSuccess(o.id))}>Simulate Success</Button>
              <Button className="w-full" variant="ghost" disabled={busy} onClick={() => act(() => api.simulateFailure(o.id))}>Simulate Failure</Button>
            </>
          ) : null}
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-4">
        <Explain title="Why this customer?" body={o.why_customer} />
        <Explain title="Why recover?" body={o.why_recover} />
        <Explain title="Why this action?" body={o.why_action} />
      </section>

      <section className="panel p-5"><p className="eyebrow">Why not the alternatives?</p><div className="mt-4 grid gap-3 md:grid-cols-3"><div className="rounded-xl bg-mist-50 p-4"><b>Retry</b><p className="mt-2 text-sm text-ink-700/70">Not preferred when the current strategy has higher expected value or retry risk is elevated.</p></div><div className="rounded-xl bg-mist-50 p-4"><b>Payment link</b><p className="mt-2 text-sm text-ink-700/70">Preferred for strong customers with recoverable failures and clear payment intent.</p></div><div className="rounded-xl bg-mist-50 p-4"><b>Human review</b><p className="mt-2 text-sm text-ink-700/70">Required when value, risk, or policy exceeds the autonomous boundary.</p></div></div></section>

      {analysis ? (
        <section className="panel p-5">
          <p className="eyebrow">AI analysis</p>
          <p className="mt-2 text-sm">{analysis.reason}</p>
          <p className="mt-2 text-xs text-mist-400">Source: {analysis.ai_source === "openai" ? "OpenAI" : "Local recovery engine"} · Risk {analysis.risk_level}</p>
          <p className="mt-3 text-sm italic text-ink-700/80">{analysis.customer_message}</p>
          {analysis.guard ? (
            <ul className="mt-3 list-disc pl-5 text-sm text-ink-700/80">
              {analysis.guard.reasons.map((r) => <li key={r}>{r}</li>)}
            </ul>
          ) : null}
        </section>
      ) : null}

      {latestLink ? (
        <section className="panel p-5">
          <p className="eyebrow">Payment link</p>
          <p className="mt-2 text-sm break-all">{latestLink.short_url}</p>
          <p className="mt-1 text-xs text-mist-400">
            {latestLink.mode === "demo" ? "Demo Mode — No real payment was created." : "Razorpay Test Mode — not a live settlement."}
            · {latestLink.reference_id} · {latestLink.status}
          </p>
        </section>
      ) : null}

      <section className="panel p-5">
        <p className="eyebrow">Agent trace</p>
        <ul className="mt-4 space-y-3">
          {actions.map((a) => (
            <li key={a.id} className="text-sm">
              <span className="font-medium">{a.agent_name}</span> · {a.decision.replaceAll("_", " ")}
              <p className="text-xs text-mist-400">{formatDate(a.created_at)} · {a.reason}</p>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

function Explain({ title, body }: { title: string; body?: string | null }) {
  return (
    <div className="panel p-5">
      <p className="eyebrow">{title}</p>
      <p className="mt-3 text-sm leading-6 text-ink-700/80">{body || "Run Analyze to generate a structured explanation from the current ledger."}</p>
    </div>
  );
}
