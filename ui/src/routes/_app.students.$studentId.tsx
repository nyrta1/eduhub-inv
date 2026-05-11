import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { useStudent, useUpdateStudent, useGradesForStudent } from "@/hooks/api";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { PageLoader, ErrorState } from "@/components/States";
import { apiErrorMessage } from "@/lib/api";
import { toast } from "sonner";
import { ArrowLeft } from "lucide-react";

export const Route = createFileRoute("/_app/students/$studentId")({ component: StudentDetail });

function StudentDetail() {
  const { studentId } = Route.useParams();
  const { data, isLoading, error, refetch } = useStudent(studentId);
  const grades = useGradesForStudent(studentId);
  const update = useUpdateStudent();
  const [form, setForm] = useState({ academic_group: "", specialty: "", academic_status: "", enrollment_status: "" });

  useEffect(() => {
    if (data?.student) {
      setForm({
        academic_group: data.student.academic_group ?? "",
        specialty: data.student.specialty ?? "",
        academic_status: data.student.academic_status ?? "",
        enrollment_status: data.student.enrollment_status ?? "",
      });
    }
  }, [data]);

  if (isLoading) return <PageLoader />;
  if (error) return <ErrorState message={apiErrorMessage(error)} onRetry={refetch} />;
  if (!data) return null;

  const save = () => {
    update.mutate({ id: studentId, body: form }, {
      onSuccess: () => toast.success("Profile updated"),
      onError: (e) => toast.error(apiErrorMessage(e)),
    });
  };

  return (
    <div className="space-y-6">
      <Link to="/students" className="text-sm text-muted-foreground hover:text-foreground inline-flex items-center gap-1">
        <ArrowLeft className="h-4 w-4" /> Students
      </Link>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{data.student.student_number}</h1>
          <p className="text-sm text-muted-foreground">Enrolled since {data.student.enrollment_date ?? "—"}</p>
        </div>
        <Card className="px-4 py-3 text-right">
          <div className="text-xs uppercase text-muted-foreground">GPA</div>
          <div className="text-2xl font-semibold">{data.gpa}</div>
        </Card>
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        <Card className="p-5 space-y-3">
          <div className="font-semibold">Profile</div>
          {([
            ["academic_group", "Group"],
            ["specialty", "Specialty"],
            ["academic_status", "Academic status"],
            ["enrollment_status", "Enrollment status"],
          ] as const).map(([k, label]) => (
            <div key={k} className="space-y-1.5">
              <Label>{label}</Label>
              <Input value={(form as any)[k]} onChange={(e) => setForm({ ...form, [k]: e.target.value })} />
            </div>
          ))}
          <Button onClick={save} disabled={update.isPending}>
            {update.isPending ? "Saving…" : "Save changes"}
          </Button>
        </Card>

        <Card className="p-5">
          <div className="font-semibold mb-3">Grades</div>
          <div className="space-y-2">
            {grades.data?.length ? grades.data.map((g) => (
              <div key={g.id} className="flex items-center justify-between text-sm py-2 border-b last:border-0">
                <div className="font-mono text-xs text-muted-foreground">{g.course_id.slice(0, 8)}</div>
                <div className="font-semibold">{g.score} {g.letter_grade && <span className="text-xs text-muted-foreground ml-1">{g.letter_grade}</span>}</div>
              </div>
            )) : <div className="text-sm text-muted-foreground py-4 text-center">No grades recorded.</div>}
          </div>
        </Card>
      </div>
    </div>
  );
}
