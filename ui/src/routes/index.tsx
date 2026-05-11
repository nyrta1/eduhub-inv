import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";
import { useAuthStore } from "@/store/auth-store";

export const Route = createFileRoute("/")({
  component: Index,
});

function Index() {
  const navigate = useNavigate();
  const { hydrated, accessToken } = useAuthStore();
  useEffect(() => {
    if (!hydrated) return;
    navigate({ to: accessToken ? "/dashboard" : "/login", replace: true });
  }, [hydrated, accessToken, navigate]);
  return (
    <div className="min-h-screen flex items-center justify-center text-muted-foreground text-sm">
      Loading…
    </div>
  );
}
