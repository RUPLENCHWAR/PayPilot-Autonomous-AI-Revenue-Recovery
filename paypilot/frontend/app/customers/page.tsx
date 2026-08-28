"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import type { Customer } from "@/lib/types";
import { ErrorState, Skeleton } from "@/components/ui/Feedback";
import { formatINR, formatPct } from "@/lib/utils";

export default function CustomersPage() {
  const [items, setItems] = useState<Customer[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .customers()
      .then((d) => setItems((d as { items: Customer[] }).items))
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed"));
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!items) return <Skeleton className="h-80" />;

  return (
    <div className="space-y-5">
      <div>
        <p className="eyebrow">Accounts</p>
        <h2 className="mt-1 font-display text-3xl">Customers</h2>
        <p className="mt-2 text-sm text-ink-700/70">Recovery decisions differ because payment history and lifetime value differ.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {items.map((c) => (
          <Link key={c.id} href={`/customers/${c.id}`} className="panel p-5 transition hover:-translate-y-0.5">
            <p className="font-medium">{c.name}</p>
            <p className="text-xs text-mist-400">{c.email}</p>
            <p className="mt-4 font-display text-2xl">{formatINR(c.lifetime_value)}</p>
            <p className="mt-2 text-sm text-ink-700/70">
              {c.successful_payments} paid · {c.failed_payments} unpaid · score {formatPct(c.recovery_score)}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}
