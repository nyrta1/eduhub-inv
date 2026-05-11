import { useEffect, useState } from "react";
import { Outlet, useNavigate, useRouterState } from "@tanstack/react-router";
import {
  LayoutDashboard,
  FileText,
  GraduationCap,
  BookOpen,
  ClipboardList,
  User,
  Shield,
  LogOut,
  Menu,
  X,
} from "lucide-react";
import { useAuthStore } from "@/store/auth-store";
import { useLogout, useMe } from "@/hooks/api";
import type { Role } from "@/types/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface NavItem {
  to: string;
  label: string;
  icon: any;
  roles?: Role[];
}

const NAV: NavItem[] = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/applications", label: "Applications", icon: FileText },
  { to: "/students", label: "Students", icon: GraduationCap, roles: ["TEACHER", "DEAN", "ADMIN"] },
  { to: "/courses", label: "Courses", icon: BookOpen },
  { to: "/grades", label: "Grades", icon: ClipboardList },
  { to: "/admin", label: "Admin", icon: Shield, roles: ["ADMIN"] },
  { to: "/profile", label: "Profile", icon: User },
];

export function AppLayout() {
  const navigate = useNavigate();
  const { accessToken, user, hydrated, hasAnyRole, setUser } = useAuthStore();
  const [ready, setReady] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const logout = useLogout();
  const meQuery = useMe(!!accessToken && !user);

  useEffect(() => {
    if (!hydrated) return;
    if (!accessToken) {
      navigate({ to: "/login", search: { redirect: pathname } as any });
    } else {
      setReady(true);
    }
  }, [hydrated, accessToken, navigate, pathname]);

  useEffect(() => {
    if (meQuery.data) setUser(meQuery.data);
  }, [meQuery.data, setUser]);

  if (!ready || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center text-muted-foreground text-sm">
        Loading workspace…
      </div>
    );
  }

  const visibleNav = NAV.filter(
    (n) => !n.roles || hasAnyRole(n.roles),
  );

  return (
    <div className="min-h-screen flex bg-background">
      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 w-64 border-r bg-sidebar text-sidebar-foreground transform transition-transform lg:static lg:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="h-16 px-6 flex items-center gap-2 border-b border-sidebar-border">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-primary to-[oklch(0.65_0.2_300)] flex items-center justify-center text-primary-foreground font-bold">
            S
          </div>
          <div>
            <div className="font-semibold text-sm leading-tight">Scholaris</div>
            <div className="text-xs text-muted-foreground">Academic ERP</div>
          </div>
        </div>
        <nav className="p-3 space-y-0.5">
          {visibleNav.map((item) => {
            const active =
              pathname === item.to || pathname.startsWith(item.to + "/");
            return (
              <button
                key={item.to}
                onClick={() => {
                  navigate({ to: item.to });
                  setMobileOpen(false);
                }}
                className={cn(
                  "w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
                  active
                    ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                    : "text-sidebar-foreground/80 hover:bg-sidebar-accent/60",
                )}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </button>
            );
          })}
        </nav>
        <div className="absolute bottom-0 inset-x-0 p-3 border-t border-sidebar-border">
          <div className="px-3 py-2 text-xs text-muted-foreground">
            Signed in as
          </div>
          <div className="px-3 pb-2">
            <div className="text-sm font-medium truncate">{user.full_name}</div>
            <div className="text-xs text-muted-foreground truncate">
              {user.email}
            </div>
            <div className="mt-1 flex flex-wrap gap-1">
              {user.roles.map((r) => (
                <span
                  key={r}
                  className="text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded bg-accent text-accent-foreground"
                >
                  {r}
                </span>
              ))}
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start"
            onClick={() => logout.mutate(undefined, { onSuccess: () => navigate({ to: "/login" }) })}
          >
            <LogOut className="h-4 w-4 mr-2" /> Sign out
          </Button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0 lg:ml-0">
        <header className="h-16 border-b bg-card/60 backdrop-blur sticky top-0 z-30 flex items-center px-4 lg:px-8 gap-4">
          <button
            className="lg:hidden p-2 rounded-md hover:bg-accent"
            onClick={() => setMobileOpen((v) => !v)}
            aria-label="Menu"
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
          <div className="text-sm text-muted-foreground">
            {pageTitle(pathname)}
          </div>
          <div className="ml-auto flex items-center gap-3">
            <div className="hidden sm:flex h-8 w-8 rounded-full bg-primary/10 text-primary items-center justify-center text-xs font-semibold">
              {user.full_name?.[0]?.toUpperCase() ?? "U"}
            </div>
          </div>
        </header>
        <main className="flex-1 p-4 lg:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

function pageTitle(path: string): string {
  if (path.startsWith("/dashboard")) return "Dashboard";
  if (path.startsWith("/applications")) return "Applications";
  if (path.startsWith("/students")) return "Students";
  if (path.startsWith("/courses")) return "Courses";
  if (path.startsWith("/grades")) return "Grades";
  if (path.startsWith("/admin")) return "Admin";
  if (path.startsWith("/profile")) return "Profile";
  return "";
}
