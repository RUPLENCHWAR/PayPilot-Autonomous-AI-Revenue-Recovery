"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import type { Customer, Opportunity, Transaction } from "@/lib/types";
import { ErrorState, Skeleton } from "@/components/ui/Feedback";
import { StatusBadge } from "@/components/ui/Status";
import { formatINR, formatPct, formatDate } from "@/lib/utils";

type Detail = { customer: Customer; transactions: Transaction[]; opportunities: Opportunity[] };

export default function CustomerDetailPage() {
  const params = useParams<{ id: string }>();
  const [data, setData] = useState<Detail | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .customer(Number(params.id))
      .then((d) => setData(d as Detail))
      .catch((err) => setError(err instanceof ApiError ? err.message : "Not found"));
  }, [params.id]);

  if (error) return <ErrorState message={error} />;
  if (!data) return <Skeleton className="h-96" />;
  const { customer: c, transactions, opportunities } = data;

  return (
    <div className="space-y-6">
      <div>
        <Link href="/customers" className="text-xs text-accent-600">All customers</Link>
        <h2 className="mt-2 font-display text-3xl">{c.name}</h2>
        <p className="text-sm text-mist-400">{c.email} · {c.phone}</p>
      </div>
      <section className="grid gap-4 md:grid-cols-4">
        <Stat label="Total paid" value={formatINR(c.total_paid)} />
        <Stat label="Successful" value={String(c.successful_payments)} />
        <Stat label="Failed / unpaid" value={String(c.failed_payments)} />
        <Stat label="Recovery score" value={formatPct(c.recovery_score)} />
      </section>
      <section className="panel p-5">
        <h3 className="font-medium">Recovery opportunities</h3>
        <ul className="mt-3 space-y-2">
          {opportunities.map((o) => (
            <li key={o.id} className="flex items-center justify-between text-sm">
              <Link className="hover:underline" href={`/recovery/${o.id}`}>{formatINR(o.amount)} · {o.recommended_action}</Link>
              <StatusBadge status={o.status} />
            </li>
          ))}
          {!opportunities.length ? <p className="text-sm text-mist-400">No open leakage for this customer.</p> : null}
        </ul>
      </section>
      <section className="panel overflow-hidden">
        <h3 className="px-5 py-4 font-medium">Transaction history</h3>
        <table className="w-full text-sm">
          <tbody>
            {transactions.map((tx) => (
              <tr key={tx.id} className="border-t border-ink-900/5">
                <td className="px-5 py-3">
                  <Link className="hover:underline" href={`/transactions/${tx.id}`}>{tx.external_transaction_id}</Link>
                </td>
                <td>{formatDate(tx.created_at)}</td>
                <td>{formatINR(tx.amount)}</td>
                <td className="pr-5"><StatusBadge status={tx.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="panel p-5">
      <p className="eyebrow">{label}</p>
      <p className="mt-2 font-display text-2xl">{value}</p>
    </div>
  );
}
