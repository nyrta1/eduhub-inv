import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useAssignRole } from "@/hooks/api";
import { RoleGate } from "@/components/RoleGate";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { apiErrorMessage } from "@/lib/api";
import { toast } from "sonner";
import type { Role } from "@/types/api";

export const Route = createFileRoute("/_app/admin")({ component: AdminPage });

function AdminPage() {
  return (
    <RoleGate roles={["ADMIN"]}>
      <Inner />
    </RoleGate>
  );
}

function Inner() {
  const assign = useAssignRole();
  const [userId, setUserId] = useState("");
  const [role, setRole] = useState<Role>("STUDENT");

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    assign.mutate({ userId, body: { role } }, {
      onSuccess: () => toast.success(`Role ${role} assigned`),
      onError: (e) => toast.error(apiErrorMessage(e)),
    });
  };

  return (
    <div className="space-y-6 max-w-xl">
      <div>
        <h1 className="text-2xl font-semibold">Admin</h1>
        <p className="text-sm text-muted-foreground">Assign roles to platform users.</p>
      </div>
      <Card className="p-5 space-y-4">
        <div className="font-semibold">Assign role</div>
        <form onSubmit={submit} className="space-y-3">
          <div className="space-y-1.5">
            <Label>User ID (UUID)</Label>
            <Input required value={userId} onChange={(e) => setUserId(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label>Role</Label>
            <Select value={role} onValueChange={(v) => setRole(v as Role)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {(["STUDENT","TEACHER","DEAN","ADMIN"] as Role[]).map((r) => (
                  <SelectItem key={r} value={r}>{r}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button type="submit" disabled={assign.isPending}>
            {assign.isPending ? "Assigning…" : "Assign role"}
          </Button>
        </form>
      </Card>
    </div>
  );
}
