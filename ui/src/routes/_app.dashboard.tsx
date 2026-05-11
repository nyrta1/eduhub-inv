import { createFileRoute, Link } from "@tanstack/react-router";
import { useAuthStore } from "@/store/auth-store";
import {
  useApplications,
  useCourses,
  useMyApplications,
  useMyGrades,
  useMyStudent,
  useStudents,
} from "@/hooks/api";
import { Card } from "@/components/ui/card";
import { StatusBadge } from "@/components/StatusBadge";
import {
  GraduationCap,
  FileText,
  BookOpen,
  ClipboardList,
  TrendingUp,
} from "lucide-react";

export const Route = createFileRoute("/_app/dashboard")({ component: Dashboard });

function StatCard({ icon: Icon, label, value, hint }: any) {
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between">
        <div className="text-xs uppercase tracking-wide text-muted-foreground">{label}</div>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </div>
      <div className="mt-3 text-2xl font-semibold">{value ?? "—"}</div>
      {hint && <div className="text-xs text-muted-foreground mt-1">{hint}</div>}
    </Card>
  );
}

function Dashboard() {
  const { user, hasAnyRole } = useAuthStore();
  const isStaff = hasAnyRole(["DEAN", "ADMIN"]);
  const isStudent = hasAnyRole(["STUDENT"]);

  const studentsQ = useStudents();
  const coursesQ = useCourses();
  const appsQ = useApplications();
  const myStudentQ = useMyStudent();
  const myAppsQ = useMyApplications();
  const myGradesQ = useMyGrades();

  const activeApps = (appsQ.data ?? []).filter(
    (a) => a.status === "PENDING" || a.status === "UNDER_REVIEW",
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Welcome, {user?.full_name?.split(" ")[0]}</h1>
        <p className="text-sm text-muted-foreground">
          Here's what's happening across your workspace today.
        </p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {isStaff && (
          <>
            <StatCard icon={GraduationCap} label="Students"
              value={studentsQ.data?.length} />
            <StatCard icon={FileText} label="Active applications"
              value={activeApps.length}
              hint={`${appsQ.data?.length ?? 0} total`} />
          </>
        )}
        <StatCard icon={BookOpen} label="Courses" value={coursesQ.data?.length} />
        {isStudent && (
          <>
            <StatCard icon={TrendingUp} label="GPA"
              value={myStudentQ.data?.gpa} />
            <StatCard icon={ClipboardList} label="My grades"
              value={myGradesQ.data?.length} />
          </>
        )}
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        <Card className="p-5">
          <div className="flex items-center justify-between mb-3">
            <div className="font-semibold">Recent applications</div>
            <Link to="/applications" className="text-xs text-primary hover:underline">
              View all
            </Link>
          </div>
          <div className="space-y-2">
            {(isStaff ? appsQ.data : myAppsQ.data)?.slice(0, 5).map((a) => (
              <div key={a.id} className="flex items-center justify-between text-sm py-2 border-b last:border-0">
                <div>
                  <div className="font-medium">{a.program_code}</div>
                  <div className="text-xs text-muted-foreground">Intake {a.intake_term}</div>
                </div>
                <StatusBadge status={a.status} />
              </div>
            ))}
            {(isStaff ? appsQ.data : myAppsQ.data)?.length === 0 && (
              <div className="text-sm text-muted-foreground py-4 text-center">
                No applications yet.
              </div>
            )}
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between mb-3">
            <div className="font-semibold">{isStudent ? "My recent grades" : "Active courses"}</div>
            <Link to={isStudent ? "/grades" : "/courses"}
              className="text-xs text-primary hover:underline">View all</Link>
          </div>
          <div className="space-y-2">
            {isStudent
              ? myGradesQ.data?.slice(0, 5).map((g) => (
                  <div key={g.id} className="flex items-center justify-between text-sm py-2 border-b last:border-0">
                    <div className="font-mono text-xs text-muted-foreground">{g.course_id.slice(0, 8)}</div>
                    <div className="font-semibold">{g.score} {g.letter_grade && <span className="text-xs text-muted-foreground ml-1">{g.letter_grade}</span>}</div>
                  </div>
                ))
              : coursesQ.data?.slice(0, 5).map((c) => (
                  <div key={c.id} className="flex items-center justify-between text-sm py-2 border-b last:border-0">
                    <div>
                      <div className="font-medium">{c.code}</div>
                      <div className="text-xs text-muted-foreground">{c.credits} credits</div>
                    </div>
                  </div>
                ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
