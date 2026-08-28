"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import type { Customer, Opportunity, Transaction } from "@/lib/types";
import { ErrorState, Skeleton } from "@/components/ui/Feedback";
import { StatusBadge } from "@/components/ui/Status";
import { formatINR, formatPct, formatDate } from "@/lib/utils";

type Detail = {
  transaction: Transaction;
  customer: Customer;
  history: Transaction[];
  opportunities: Opportunity[];
};

export default function TransactionDetailPage() {
  const params = useParams<{ id: string }>();
  const [data, setData] = useState<Detail | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .transaction(Number(params.id))
      .then((d) => setData(d as Detail))
      .catch((err) => setError(err instanceof ApiError ? err.message : "Not found"));
  }, [params.id]);

  if (error) return <ErrorState message={error} />;
  if (!data) return <Skeleton className="h-96" />;

  const { transaction: tx, customer, history, opportunities } = data;
  const opp = opportunities[0];

  return (
    <div className="space-y-6">
      <div>
        <Link href="/transactions" className="text-xs text-accent-600">All transactions</Link>
        <h2 className="mt-2 font-display text-3xl">{tx.external_transaction_id}</h2>
      </div>
      <section className="grid gap-4 lg:grid-cols-3">
        <div className="panel p-6 lg:col-span-2">
          <p className="font-display text-5xl">{formatINR(tx.amount)}</p>
          <div className="mt-4 flex gap-2">
            <StatusBadge status={tx.recovered ? "recovered" : tx.status} />
            <StatusBadge status={tx.payment_method} />
          </div>
          <dl className="mt-6 grid gap-4 sm:grid-cols-2 text-sm">
            <div><dt className="text-mist-400">Failure reason</dt><dd className="mt-1">{tx.failure_reason || "—"}</dd></div>
            <div><dt className="text-mist-400">Created</dt><dd className="mt-1">{formatDate(tx.created_at)}</dd></div>
            <div><dt className="text-mist-400">Recovery probability</dt><dd className="mt-1">{tx.recovery_probability != null ? formatPct(tx.recovery_probability) : "—"}</dd></div>
            <div><dt className="text-mist-400">Recommended action</dt><dd className="mt-1 capitalize">{tx.recommended_action?.replaceAll("_", " ") || "—"}</dd></div>
          </dl>
        </div>
        <div className="panel p-6">
          <p className="eyebrow">Customer</p>
          <Link href={`/customers/${customer.id}`} className="mt-2 block font-medium hover:underline">{customer.name}</Link>
          <p className="text-sm text-mist-400">{customer.email}</p>
          <p className="mt-4 text-sm">LTV {formatINR(customer.lifetime_value)}</p>
          <p className="text-sm">{customer.successful_payments} successful · {customer.failed_payments} failed</p>
        </div>
      </section>
      {opp ? (
        <section className="panel p-5">
          <p className="eyebrow">AI recovery</p>
          <p className="mt-2 text-sm">{opp.why_recover}</p>
          <p className="mt-2 text-sm">{opp.why_action}</p>
          <p className="mt-2 text-sm">Expected recovery {formatINR(opp.expected_recovery)}</p>
          <Link href={`/recovery/${opp.id}`} className="mt-3 inline-block text-sm text-accent-600">Open in Recovery Center</Link>
        </section>
      ) : null}
      <section className="panel overflow-hidden">
        <h3 className="px-5 py-4 font-medium">Payment history</h3>
        <table className="w-full text-sm">
          <tbody>
            {history.map((h) => (
              <tr key={h.id} className="border-t border-ink-900/5">
                <td className="px-5 py-3">{formatDate(h.created_at)}</td>
                <td>{formatINR(h.amount)}</td>
                <td><StatusBadge status={h.status} /></td>
                <td className="pr-5">{h.failure_reason || h.payment_method}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
