import { ReactNode } from "react";
import { useAuthStore } from "@/store/auth-store";
import type { Role } from "@/types/api";
import { Card } from "@/components/ui/card";
import { ShieldAlert } from "lucide-react";

export function RoleGate({
  roles,
  children,
  fallback,
}: {
  roles: Role[];
  children: ReactNode;
  fallback?: ReactNode;
}) {
  const hasAnyRole = useAuthStore((s) => s.hasAnyRole);
  if (!hasAnyRole(roles)) {
    return (
      fallback ?? (
        <Card className="p-8 text-center">
          <ShieldAlert className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
          <div className="font-semibold">Restricted area</div>
          <div className="text-sm text-muted-foreground mt-1">
            You do not have permission to view this section.
          </div>
        </Card>
      )
    );
  }
  return <>{children}</>;
}
