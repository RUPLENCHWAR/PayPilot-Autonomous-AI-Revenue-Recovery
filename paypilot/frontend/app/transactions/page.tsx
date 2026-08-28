"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import type { Transaction } from "@/lib/types";
import { ErrorState, Skeleton } from "@/components/ui/Feedback";
import { StatusBadge } from "@/components/ui/Status";
import { formatINR, formatPct, formatDate } from "@/lib/utils";

export default function TransactionsPage() {
  const [items, setItems] = useState<Transaction[] | null>(null);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");

  const load = useCallback((next = status) => {
    setError("");
    const q = next ? `?status=${next}` : "";
    api
      .transactions(q)
      .then((data) => setItems((data as { items: Transaction[] }).items))
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load"));
  }, [status]);

  useEffect(() => {
    load();
  }, [load]);

  if (error) return <ErrorState message={error} onRetry={() => load()} />;
  if (!items) return <Skeleton className="h-80" />;

  return (
    <div className="space-y-5">
      <div>
        <p className="eyebrow">Ledger</p>
        <h2 className="mt-1 font-display text-3xl">Transactions</h2>
      </div>
      <div className="flex flex-wrap gap-2">
        {["", "captured", "failed", "abandoned", "pending", "refunded"].map((s) => (
          <button
            key={s || "all"}
            onClick={() => setStatus(s)}
            className={`rounded-full px-3 py-1 text-xs font-semibold ${status === s ? "bg-ink-900 text-white" : "bg-mist-100 text-ink-700"}`}
          >
            {s || "all"}
          </button>
        ))}
      </div>
      <div className="panel overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-mist-50 text-left text-xs uppercase tracking-wide text-mist-400">
            <tr>
              <th className="px-5 py-3">ID</th>
              <th>Customer</th>
              <th>Amount</th>
              <th>Status</th>
              <th>Method</th>
              <th>Failure</th>
              <th>P(recover)</th>
              <th>When</th>
            </tr>
          </thead>
          <tbody>
            {items.map((tx) => (
              <tr key={tx.id} className="border-t border-ink-900/5">
                <td className="px-5 py-3">
                  <Link className="hover:underline" href={`/transactions/${tx.id}`}>{tx.external_transaction_id}</Link>
                </td>
                <td>{tx.customer_name}</td>
                <td>{formatINR(tx.amount)}</td>
                <td className="py-3"><StatusBadge status={tx.recovered ? "recovered" : tx.status} /></td>
                <td className="uppercase">{tx.payment_method}</td>
                <td>{tx.failure_reason || "—"}</td>
                <td>{tx.recovery_probability != null ? formatPct(tx.recovery_probability) : "—"}</td>
                <td className="pr-5 text-xs text-mist-400">{formatDate(tx.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
