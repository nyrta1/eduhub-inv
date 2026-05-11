import { createFileRoute, useNavigate, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { z } from "zod";
import { useLogin } from "@/hooks/api";
import { useAuthStore } from "@/store/auth-store";
import { apiErrorMessage } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
});

export const Route = createFileRoute("/login")({
  validateSearch: (s) => ({ redirect: (s.redirect as string) || "/dashboard" }),
  component: LoginPage,
});

function LoginPage() {
  const navigate = useNavigate();
  const search = Route.useSearch();
  const login = useLogin();
  const { accessToken, hydrated } = useAuthStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (hydrated && accessToken) navigate({ to: search.redirect, replace: true });
  }, [hydrated, accessToken, navigate, search.redirect]);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = schema.safeParse({ email, password });
    if (!parsed.success) {
      const errs: Record<string, string> = {};
      parsed.error.issues.forEach((i) => (errs[i.path[0] as string] = i.message));
      setErrors(errs);
      return;
    }
    setErrors({});
    login.mutate(parsed.data, {
      onSuccess: () => {
        toast.success("Welcome back");
        navigate({ to: search.redirect, replace: true });
      },
      onError: (e) => toast.error(apiErrorMessage(e)),
    });
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-background">
      <div className="hidden lg:flex flex-col justify-between p-12 bg-gradient-to-br from-primary to-[oklch(0.4_0.2_290)] text-primary-foreground">
        <div className="font-semibold tracking-tight text-lg">Scholaris</div>
        <div>
          <h1 className="text-4xl font-semibold leading-tight">
            Run your academic operations with confidence.
          </h1>
          <p className="mt-4 text-primary-foreground/80 max-w-md">
            Enrollment applications, course management, and academic performance — unified
            in a single secure workspace.
          </p>
        </div>
        <div className="text-xs text-primary-foreground/70">© Scholaris University Platform</div>
      </div>

      <div className="flex items-center justify-center p-6">
        <div className="w-full max-w-sm space-y-6">
          <div>
            <h2 className="text-2xl font-semibold">Sign in</h2>
            <p className="text-sm text-muted-foreground mt-1">
              Use your university credentials.
            </p>
          </div>
          <form onSubmit={submit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" autoComplete="email"
                value={email} onChange={(e) => setEmail(e.target.value)} />
              {errors.email && <p className="text-xs text-destructive">{errors.email}</p>}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <Input id="password" type="password" autoComplete="current-password"
                value={password} onChange={(e) => setPassword(e.target.value)} />
              {errors.password && <p className="text-xs text-destructive">{errors.password}</p>}
            </div>
            <Button type="submit" className="w-full" disabled={login.isPending}>
              {login.isPending ? "Signing in…" : "Sign in"}
            </Button>
          </form>
          <div className="text-sm text-center text-muted-foreground">
            New to Scholaris?{" "}
            <Link to="/register" className="text-primary font-medium hover:underline">
              Create an account
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
