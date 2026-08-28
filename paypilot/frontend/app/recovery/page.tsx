"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Opportunity } from "@/lib/types";
import { OpportunityCard } from "@/components/recovery/OpportunityCard";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";

export default function RecoveryPage() {
  const [items, setItems] = useState<Opportunity[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<number | null>(null);
  const [notice, setNotice] = useState("");
  const [loaded, setLoaded] = useState(false);

  async function load() {
    setError("");
    try {
      const data = (await api.opportunities()) as { items: Opportunity[] };
      setItems(data.items);
      setLoaded(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load opportunities");
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function run(id: number, fn: (id: number) => Promise<unknown>) {
    setBusy(id);
    setNotice("");
    try {
      const result = (await fn(id)) as { message?: string };
      setNotice(result.message || "Updated");
      await load();
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "Action failed");
    } finally {
      setBusy(null);
    }
  }

  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!loaded) {
    return (
      <div className="space-y-4">
        <Header />
        <Skeleton className="h-40" />
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <Header />
      {notice ? <p className="rounded-xl bg-mist-100 px-4 py-3 text-sm">{notice}</p> : null}
      {items.length === 0 ? (
        <EmptyState title="No recovery opportunities" body="The seed ledger has no unpaid recoverable payments." />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {items.map((opp) => (
            <OpportunityCard
              key={opp.id}
              opportunity={opp}
              busy={busy === opp.id}
              onAnalyze={(id) => run(id, api.analyze)}
              onRecover={(id) => run(id, api.execute)}
              onApprove={(id) => run(id, api.approve)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function Header() {
  return (
    <div>
      <p className="eyebrow">Recovery Center</p>
      <h2 className="mt-1 font-display text-3xl">Close the loop</h2>
      <p className="mt-2 max-w-2xl text-sm text-ink-700/70">
        Analyze runs the revenue + recovery agents and RecoveryGuard. Recover creates a Razorpay payment link in test mode, or a labelled demo link if credentials are absent.
      </p>
    </div>
  );
}
