import { Loader2 } from "lucide-react";

export function PageLoader({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center py-16 text-muted-foreground gap-2 text-sm">
      <Loader2 className="h-4 w-4 animate-spin" /> {label}
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="border border-dashed rounded-xl p-10 text-center bg-card">
      <div className="font-semibold">{title}</div>
      {description && (
        <div className="text-sm text-muted-foreground mt-1">{description}</div>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="border border-destructive/30 bg-destructive/5 rounded-xl p-6 text-center">
      <div className="font-semibold text-destructive">Something went wrong</div>
      <div className="text-sm text-muted-foreground mt-1">{message}</div>
      {onRetry && (
        <button
          className="mt-3 text-sm underline text-primary"
          onClick={onRetry}
        >
          Try again
        </button>
      )}
    </div>
  );
}
