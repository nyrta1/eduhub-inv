import { createFileRoute, Link } from "@tanstack/react-router";
import { ShieldX } from "lucide-react";

export const Route = createFileRoute("/unauthorized")({ component: Unauthorized });

function Unauthorized() {
  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-background">
      <div className="text-center max-w-md">
        <ShieldX className="h-12 w-12 mx-auto text-destructive" />
        <h1 className="mt-4 text-2xl font-semibold">Access denied</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          You don't have permission to view this resource. If you think this is a mistake,
          contact your administrator.
        </p>
        <Link to="/dashboard"
          className="mt-6 inline-flex rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium hover:bg-primary/90">
          Back to dashboard
        </Link>
      </div>
    </div>
  );
}
