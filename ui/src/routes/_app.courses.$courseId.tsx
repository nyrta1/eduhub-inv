import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import {
  useCourse, useEnrollStudent, useGradesForCourse, useUpdateCourse,
} from "@/hooks/api";
import { useAuthStore } from "@/store/auth-store";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter,
} from "@/components/ui/dialog";
import { PageLoader, ErrorState } from "@/components/States";
import { apiErrorMessage } from "@/lib/api";
import { toast } from "sonner";
import { ArrowLeft, UserPlus } from "lucide-react";

export const Route = createFileRoute("/_app/courses/$courseId")({ component: CourseDetail });

function CourseDetail() {
  const { courseId } = Route.useParams();
  const { hasAnyRole } = useAuthStore();
  const canManage = hasAnyRole(["DEAN", "ADMIN", "TEACHER"]);
  const { data, isLoading, error, refetch } = useCourse(courseId);
  const grades = useGradesForCourse(courseId);
  const update = useUpdateCourse();
  const [credits, setCredits] = useState("");
  const [teacherId, setTeacherId] = useState("");

  if (isLoading) return <PageLoader />;
  if (error) return <ErrorState message={apiErrorMessage(error)} onRetry={refetch} />;
  if (!data) return null;

  const save = () => {
    const body: any = {};
    if (credits) body.credits = credits;
    if (teacherId) body.teacher_id = teacherId;
    if (Object.keys(body).length === 0) return;
    update.mutate({ id: courseId, body }, {
      onSuccess: () => { toast.success("Course updated"); setCredits(""); setTeacherId(""); refetch(); },
      onError: (e) => toast.error(apiErrorMessage(e)),
    });
  };

  return (
    <div className="space-y-6">
      <Link to="/courses" className="text-sm text-muted-foreground hover:text-foreground inline-flex items-center gap-1">
        <ArrowLeft className="h-4 w-4" /> Courses
      </Link>

      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">{data.code}</h1>
          <p className="text-sm text-muted-foreground">{data.credits} credits</p>
        </div>
        {canManage && <EnrollDialog courseId={courseId} />}
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        {canManage && (
          <Card className="p-5 space-y-3">
            <div className="font-semibold">Edit course</div>
            <div className="space-y-1.5">
              <Label>Credits</Label>
              <Input type="number" step="0.5" placeholder={String(data.credits)} value={credits}
                onChange={(e) => setCredits(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>Teacher ID</Label>
              <Input placeholder={data.teacher_id} value={teacherId}
                onChange={(e) => setTeacherId(e.target.value)} />
            </div>
            <Button onClick={save} disabled={update.isPending}>
              {update.isPending ? "Saving…" : "Save changes"}
            </Button>
          </Card>
        )}

        <Card className="p-5">
          <div className="font-semibold mb-3">Grades in this course</div>
          <div className="space-y-2">
            {grades.data?.length ? grades.data.map((g) => (
              <div key={g.id} className="flex items-center justify-between text-sm py-2 border-b last:border-0">
                <div className="font-mono text-xs text-muted-foreground">{g.student_id.slice(0, 8)}</div>
                <div className="font-semibold">{g.score} {g.letter_grade && <span className="text-xs text-muted-foreground ml-1">{g.letter_grade}</span>}</div>
              </div>
            )) : <div className="text-sm text-muted-foreground py-4 text-center">No grades recorded yet.</div>}
          </div>
        </Card>
      </div>
    </div>
  );
}

function EnrollDialog({ courseId }: { courseId: string }) {
  const [open, setOpen] = useState(false);
  const [studentId, setStudentId] = useState("");
  const enroll = useEnrollStudent();
  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    enroll.mutate({ courseId, body: { student_id: studentId } }, {
      onSuccess: () => { toast.success("Student enrolled"); setOpen(false); setStudentId(""); },
      onError: (e) => toast.error(apiErrorMessage(e)),
    });
  };
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline"><UserPlus className="h-4 w-4 mr-1" /> Enroll student</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>Enroll student</DialogTitle></DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-1.5">
            <Label>Student ID (UUID)</Label>
            <Input required value={studentId} onChange={(e) => setStudentId(e.target.value)} />
          </div>
          <DialogFooter>
            <Button type="submit" disabled={enroll.isPending}>
              {enroll.isPending ? "Enrolling…" : "Enroll"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
