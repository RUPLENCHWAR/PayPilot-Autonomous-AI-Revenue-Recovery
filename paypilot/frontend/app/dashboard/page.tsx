"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  BarChart,
  Bar,
} from "recharts";
import { api, ApiError } from "@/lib/api";
import type { DashboardResponse } from "@/lib/types";
import { formatINR, formatPct } from "@/lib/utils";
import { ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PriorityBadge, StatusBadge } from "@/components/ui/Status";
import { Button } from "@/components/ui/Button";

export default function DashboardPage() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [error, setError] = useState("");
  const [scanning, setScanning] = useState(false);
  async function scan(){ setScanning(true); try { await api.scan(); load(); } finally { setScanning(false); } }

  const load = useCallback(() => {
    setError("");
    api
      .dashboard()
      .then((d) => setData(d as DashboardResponse))
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load dashboard"));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!data) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-40" />
        <div className="grid gap-4 md:grid-cols-3">
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
        </div>
      </div>
    );
  }

  const m = data.metrics;

  return (
    <div className="space-y-6">
      <div>
        <p className="eyebrow">Revenue intelligence</p>
        <h2 className="mt-1 font-display text-3xl">Autonomous recovery desk</h2>
        <p className="mt-2 max-w-2xl text-sm text-ink-700/70">
          Metrics are calculated live from the ledger. Recoverable revenue is probability-weighted expected recovery, not the sum of every failed payment.
        </p>
      <div className="mt-4 flex items-center gap-3"><Button onClick={scan} disabled={scanning}>{scanning ? "Scanning ledger…" : "Run AI Revenue Scan"}</Button><Link href="/simulator" className="text-sm text-accent-600">Recovery Simulator →</Link></div>
      </div>

      <section className="grid gap-4 lg:grid-cols-3">
        <div className="panel relative overflow-hidden p-6 lg:col-span-2">
          <p className="eyebrow">Revenue at risk</p>
          <p className="mt-3 font-display text-5xl tracking-tight">{formatINR(m.revenue_at_risk)}</p>
          <p className="mt-3 text-sm text-ink-700/70">Unpaid failed, abandoned, and pending payments still eligible for recovery.</p>
        </div>
        <div className="panel p-6">
          <p className="eyebrow">AI recoverable</p>
          <p className="mt-3 font-display text-4xl text-gain-500">{formatINR(m.recoverable_revenue)}</p>
          <p className="mt-4 text-sm text-ink-700/70">
            Recovery confidence {formatPct(m.recovery_confidence)}
          </p>
          <p className="mt-1 text-xs text-mist-400">Weighted by demo scoring model × open opportunity amounts.</p>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Metric label="Captured revenue" value={formatINR(m.total_revenue)} hint="Sum of captured payments" />
        <Metric label="Actual recovered" value={formatINR(m.recovered_revenue)} hint="Only after successful recovery" />
        <Metric label="Recovery rate" value={formatPct(m.recovery_rate)} hint="Recovered / eligible opportunity amount" />
        <Metric label="Expected net recovery" value={formatINR(data.opportunities.reduce((sum,o)=>sum+o.expected_net_recovery,0))} hint="Expected recovery less estimated outreach cost" />
        <Metric label="Opportunities" value={String(m.opportunity_count)} hint={`${m.pending_approvals} likely need human approval`} />
      </section>

      <section className="grid gap-4 xl:grid-cols-3">
        <div className="panel p-5 xl:col-span-2">
          <p className="eyebrow">14-day movement</p>
          <h3 className="mt-1 font-medium">Captured vs unpaid leakage</h3>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e8eef6" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v: number) => formatINR(v)} />
                <Area type="monotone" dataKey="captured" stroke="#1f63c4" fill="#2f7de120" />
                <Area type="monotone" dataKey="failed" stroke="#c44a4a" fill="#e06b6b20" />
                <Area type="monotone" dataKey="recovered" stroke="#1f9d6e" fill="#3dbe8c20" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="panel p-5">
          <p className="eyebrow">Failure mix</p>
          <h3 className="mt-1 font-medium">Why payments are unpaid</h3>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.failure_breakdown} layout="vertical">
                <XAxis type="number" hide />
                <YAxis type="category" dataKey="reason" width={110} tick={{ fontSize: 10 }} />
                <Tooltip formatter={(v: number) => formatINR(v)} />
                <Bar dataKey="amount" fill="#2f7de1" radius={4} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="panel p-5">
          <div className="flex items-center justify-between">
            <h3 className="font-medium">Top recoverable customers</h3>
            <Link href="/customers" className="text-xs text-accent-600">View all</Link>
          </div>
          <ul className="mt-4 space-y-3">
            {data.top_customers.map((c) => (
              <li key={c.id} className="flex items-center justify-between rounded-xl bg-mist-50 px-3 py-3">
                <div>
                  <Link href={`/customers/${c.id}`} className="font-medium hover:underline">{c.name}</Link>
                  <p className="text-xs text-mist-400">Score {formatPct(c.recovery_score)}</p>
                </div>
                <div className="text-right text-sm">
                  <p>{formatINR(c.expected_recovery)}</p>
                  <p className="text-xs text-mist-400">expected</p>
                </div>
              </li>
            ))}
          </ul>
        </div>
        <div className="panel p-5">
          <div className="flex items-center justify-between">
            <h3 className="font-medium">Recent agent actions</h3>
            <Link href="/agents" className="text-xs text-accent-600">Timeline</Link>
          </div>
          <ul className="mt-4 space-y-3">
            {data.recent_actions.map((a) => (
              <li key={a.id} className="border-b border-ink-900/5 pb-3 last:border-0">
                <p className="text-sm font-medium">{a.agent_name} · {a.decision.replaceAll("_", " ")}</p>
                <p className="text-xs text-mist-400">{a.reason}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="panel overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4">
          <h3 className="font-medium">Open recovery opportunities</h3>
          <Link href="/recovery" className="text-xs text-accent-600">Recovery Center</Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-mist-50 text-left text-xs uppercase tracking-wide text-mist-400">
              <tr>
                <th className="px-5 py-3">Customer</th>
                <th>Amount</th>
                <th>Expected</th>
                <th>Priority</th>
                <th>Action</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {data.opportunities.map((o) => (
                <tr key={o.id} className="border-t border-ink-900/5">
                  <td className="px-5 py-3">
                    <Link href={`/recovery/${o.id}`} className="hover:underline">{o.customer_name}</Link>
                  </td>
                  <td>{formatINR(o.amount)}</td>
                  <td>{formatINR(o.expected_recovery)}</td>
                  <td><PriorityBadge priority={o.priority} /></td>
                  <td className="capitalize">{o.recommended_action.replaceAll("_", " ")}</td>
                  <td className="py-3"><StatusBadge status={o.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function Metric({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <div className="panel p-5">
      <p className="eyebrow">{label}</p>
      <p className="mt-2 font-display text-3xl">{value}</p>
      <p className="mt-2 text-xs text-mist-400">{hint}</p>
    </div>
  );
}
