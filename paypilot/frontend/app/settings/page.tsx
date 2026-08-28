"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { AppSettings } from "@/lib/types";
import { ErrorState, Skeleton } from "@/components/ui/Feedback";
import { formatINR } from "@/lib/utils";

export default function SettingsPage() {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [error, setError] = useState("");
  const [limit, setLimit] = useState(10000);
  const [enabled, setEnabled] = useState(true);
  const [saved, setSaved] = useState("");

  useEffect(() => {
    api
      .settings()
      .then((d) => { const x = d as AppSettings; setSettings(x); setLimit(x.autonomous_amount_limit); })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed"));
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!settings) return <Skeleton className="h-64" />;

  return (
    <div className="space-y-6">
      <div>
        <p className="eyebrow">Configuration</p>
        <h2 className="mt-1 font-display text-3xl">Settings</h2>
        <p className="mt-2 max-w-2xl text-sm text-ink-700/70">
          Secrets never leave the backend. This page only shows mode flags returned by the API.
        </p>
      </div>
      <section className="panel p-5">
        <p className="eyebrow">RecoveryGuard</p>
        <h3 className="mt-1 text-lg font-medium">Autonomous recovery policy</h3>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <label className="text-sm">Maximum autonomous amount<input className="mt-2 w-full rounded-xl border p-3" type="number" min={1000} max={100000} value={limit} onChange={e => setLimit(Number(e.target.value))}/></label>
          <label className="flex items-center gap-3 text-sm"><input type="checkbox" checked={enabled} onChange={e=>setEnabled(e.target.checked)}/> Autonomous recovery enabled</label>
        </div>
        <button className="mt-4 rounded-xl bg-ink-950 px-4 py-2 text-sm font-medium text-white" onClick={async()=>{ const x=await api.updateAutonomy(limit,enabled) as {autonomous_amount_limit:number}; setLimit(x.autonomous_amount_limit); setSaved("Policy saved"); setTimeout(()=>setSaved(""),2000); }}>Save policy</button>
        {saved ? <span className="ml-3 text-sm text-gain-500">{saved}</span> : null}
      </section>
      <section className="grid gap-4 md:grid-cols-2">
        <Row label="Razorpay mode" value={settings.razorpay_mode === "demo" ? "DEMO MODE" : "RAZORPAY TEST MODE"} />
        <Row label="Razorpay credentials present" value={settings.razorpay_configured ? "Yes (test keys on server)" : "No — using demo links"} />
        <Row label="AI mode" value={settings.openai_configured ? "OpenAI" : "Local recovery engine"} />
        <Row label="Webhook signature" value={settings.webhook_configured ? "Configured" : "Not configured"} />
        <Row label="Autonomous amount limit" value={formatINR(settings.autonomous_amount_limit)} />
        <Row label="Frontend origin" value={settings.frontend_url} />
      </section>
      <section className="panel p-5 text-sm leading-6 text-ink-700/80">
        <p className="font-medium">RecoveryGuard policy</p>
        <ul className="mt-2 list-disc pl-5">
          <li>Amounts ≤ configured autonomous limit with low risk may execute automatically.</li>
          <li>Amounts above the configured autonomous limit require human approval.</li>
          <li>High-risk actions always require approval.</li>
          <li>Refunds never execute autonomously.</li>
          <li>Demo simulation cannot mark real Razorpay payments as paid.</li>
        </ul>
      </section>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="panel p-5">
      <p className="eyebrow">{label}</p>
      <p className="mt-2 font-medium">{value}</p>
    </div>
  );
}
