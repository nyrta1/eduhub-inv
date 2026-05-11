import { cn } from "@/lib/utils";

const STYLES: Record<string, string> = {
  PENDING: "bg-warning/15 text-[oklch(0.45_0.15_75)]",
  UNDER_REVIEW: "bg-info/15 text-[oklch(0.4_0.15_230)]",
  APPROVED: "bg-success/15 text-[oklch(0.4_0.15_155)]",
  REJECTED: "bg-destructive/15 text-destructive",
  ENROLLED: "bg-primary/15 text-primary",
};

export function StatusBadge({ status }: { status: string }) {
  const cls = STYLES[status] ?? "bg-muted text-muted-foreground";
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium",
        cls,
      )}
    >
      {status.replace(/_/g, " ")}
    </span>
  );
}
