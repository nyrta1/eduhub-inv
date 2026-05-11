import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { useAuthStore } from "@/store/auth-store";
import { useChangePassword, useLogout, useLogoutAll } from "@/hooks/api";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { apiErrorMessage } from "@/lib/api";
import { toast } from "sonner";

export const Route = createFileRoute("/_app/profile")({ component: ProfilePage });

function ProfilePage() {
  const { user } = useAuthStore();
  const change = useChangePassword();
  const logout = useLogout();
  const logoutAll = useLogoutAll();
  const navigate = useNavigate();
  const [form, setForm] = useState({ current_password: "", new_password: "" });

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    change.mutate(form, {
      onSuccess: () => { toast.success("Password updated"); setForm({ current_password: "", new_password: "" }); },
      onError: (e) => toast.error(apiErrorMessage(e)),
    });
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-semibold">Profile</h1>
        <p className="text-sm text-muted-foreground">Manage your account and security.</p>
      </div>

      <Card className="p-5 space-y-2">
        <div className="font-semibold">Account</div>
        <div className="text-sm grid grid-cols-3 gap-2">
          <div className="text-muted-foreground">Name</div><div className="col-span-2">{user?.full_name}</div>
          <div className="text-muted-foreground">Email</div><div className="col-span-2">{user?.email}</div>
          <div className="text-muted-foreground">Roles</div>
          <div className="col-span-2 flex flex-wrap gap-1">
            {user?.roles.map((r) => (
              <span key={r} className="text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded bg-accent text-accent-foreground">{r}</span>
            ))}
          </div>
        </div>
      </Card>

      <Card className="p-5 space-y-4">
        <div className="font-semibold">Change password</div>
        <form onSubmit={submit} className="space-y-3">
          <div className="space-y-1.5"><Label>Current password</Label>
            <Input type="password" required value={form.current_password}
              onChange={(e) => setForm({ ...form, current_password: e.target.value })} /></div>
          <div className="space-y-1.5"><Label>New password</Label>
            <Input type="password" required value={form.new_password}
              onChange={(e) => setForm({ ...form, new_password: e.target.value })} /></div>
          <Button type="submit" disabled={change.isPending}>{change.isPending ? "Updating…" : "Update password"}</Button>
        </form>
      </Card>

      <Card className="p-5 space-y-3">
        <div className="font-semibold">Sessions</div>
        <div className="text-sm text-muted-foreground">Sign out from this or all devices.</div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => logout.mutate(undefined, { onSuccess: () => navigate({ to: "/login" }) })}>
            Sign out
          </Button>
          <Button variant="destructive" onClick={() => logoutAll.mutate(undefined, {
            onSuccess: () => { toast.success("Signed out everywhere"); navigate({ to: "/login" }); },
          })}>
            Sign out everywhere
          </Button>
        </div>
      </Card>
    </div>
  );
}
