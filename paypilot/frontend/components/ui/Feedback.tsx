export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-xl bg-mist-100 ${className}`} />;
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="panel p-8 text-center">
      <p className="text-sm text-danger-500">{message}</p>
      {onRetry ? (
        <button onClick={onRetry} className="mt-4 text-sm font-medium text-accent-600">
          Retry
        </button>
      ) : null}
    </div>
  );
}

export function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="panel p-10 text-center">
      <h3 className="font-display text-xl text-ink-900">{title}</h3>
      <p className="mt-2 text-sm text-mist-400">{body}</p>
    </div>
  );
}
