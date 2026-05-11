import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { z } from "zod";
import { useRegister, useLogin } from "@/hooks/api";
import { apiErrorMessage } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

const schema = z.object({
  full_name: z.string().min(1).max(255),
  email: z.string().email(),
  password: z.string().min(8, "At least 8 characters"),
});

export const Route = createFileRoute("/register")({ component: RegisterPage });

function RegisterPage() {
  const navigate = useNavigate();
  const reg = useRegister();
  const login = useLogin();
  const [form, setForm] = useState({ full_name: "", email: "", password: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const p = schema.safeParse(form);
    if (!p.success) {
      const errs: Record<string, string> = {};
      p.error.issues.forEach((i) => (errs[i.path[0] as string] = i.message));
      setErrors(errs);
      return;
    }
    setErrors({});
    reg.mutate(p.data, {
      onSuccess: () => {
        toast.success("Account created");
        login.mutate({ email: p.data.email, password: p.data.password }, {
          onSuccess: () => navigate({ to: "/dashboard", replace: true }),
        });
      },
      onError: (e) => toast.error(apiErrorMessage(e)),
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-background">
      <div className="w-full max-w-sm space-y-6">
        <div>
          <h2 className="text-2xl font-semibold">Create account</h2>
          <p className="text-sm text-muted-foreground mt-1">Join the platform as a student.</p>
        </div>
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="full_name">Full name</Label>
            <Input id="full_name" value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
            {errors.full_name && <p className="text-xs text-destructive">{errors.full_name}</p>}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })} />
            {errors.email && <p className="text-xs text-destructive">{errors.email}</p>}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="password">Password</Label>
            <Input id="password" type="password" value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })} />
            {errors.password && <p className="text-xs text-destructive">{errors.password}</p>}
          </div>
          <Button type="submit" className="w-full" disabled={reg.isPending || login.isPending}>
            {reg.isPending ? "Creating…" : "Create account"}
          </Button>
        </form>
        <div className="text-sm text-center text-muted-foreground">
          Already have an account?{" "}
          <Link to="/login" className="text-primary font-medium hover:underline">Sign in</Link>
        </div>
      </div>
    </div>
  );
}
