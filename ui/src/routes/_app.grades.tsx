import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import {
  useCreateGrade, useGradesForCourse, useMyGrades, useUpdateGrade,
} from "@/hooks/api";
import { useAuthStore } from "@/store/auth-store";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter,
} from "@/components/ui/dialog";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { PageLoader, EmptyState, ErrorState } from "@/components/States";
import { apiErrorMessage } from "@/lib/api";
import { toast } from "sonner";
import type { GradeRead } from "@/types/api";
import { Plus, Pencil } from "lucide-react";

export const Route = createFileRoute("/_app/grades")({ component: GradesPage });

function GradesPage() {
  const { hasAnyRole } = useAuthStore();
  const isStaff = hasAnyRole(["TEACHER", "DEAN", "ADMIN"]);
  return isStaff ? <StaffGrades /> : <MyGrades />;
}

function MyGrades() {
  const { data, isLoading, error, refetch } = useMyGrades();
  const avg = data && data.length ? (data.reduce((s, g) => s + parseFloat(g.score || "0"), 0) / data.length).toFixed(2) : "—";
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">My grades</h1>
          <p className="text-sm text-muted-foreground">Performance across enrolled courses.</p>
        </div>
        <Card className="px-4 py-3 text-right">
          <div className="text-xs uppercase text-muted-foreground">Average</div>
          <div className="text-2xl font-semibold">{avg}</div>
        </Card>
      </div>
      <Card>
        {isLoading ? <PageLoader /> :
         error ? <ErrorState message={apiErrorMessage(error)} onRetry={refetch} /> :
         !data?.length ? <EmptyState title="No grades yet" /> : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Course</TableHead>
                <TableHead>Score</TableHead>
                <TableHead>Letter</TableHead>
                <TableHead>Recorded</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((g) => (
                <TableRow key={g.id}>
                  <TableCell className="font-mono text-xs">{g.course_id.slice(0, 8)}</TableCell>
                  <TableCell className="font-semibold">{g.score}</TableCell>
                  <TableCell>{g.letter_grade ?? "—"}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {new Date(g.recorded_at).toLocaleDateString()}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>
    </div>
  );
}

function StaffGrades() {
  const [courseId, setCourseId] = useState("");
  const [submittedId, setSubmittedId] = useState("");
  const grades = useGradesForCourse(submittedId);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Grades</h1>
          <p className="text-sm text-muted-foreground">Record and edit grades by course.</p>
        </div>
        <NewGradeDialog defaultCourseId={submittedId} />
      </div>

      <Card className="p-4 flex flex-wrap gap-3 items-end">
        <div className="flex-1 min-w-[240px] space-y-1.5">
          <Label>Course ID</Label>
          <Input value={courseId} onChange={(e) => setCourseId(e.target.value)} placeholder="UUID" />
        </div>
        <Button onClick={() => setSubmittedId(courseId)}>Load grades</Button>
      </Card>

      {submittedId && (
        <Card>
          {grades.isLoading ? <PageLoader /> :
           grades.error ? <ErrorState message={apiErrorMessage(grades.error)} onRetry={grades.refetch} /> :
           !grades.data?.length ? <EmptyState title="No grades for this course" /> : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Student</TableHead>
                  <TableHead>Score</TableHead>
                  <TableHead>Letter</TableHead>
                  <TableHead>Recorded</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {grades.data.map((g) => (
                  <TableRow key={g.id}>
                    <TableCell className="font-mono text-xs">{g.student_id.slice(0, 8)}</TableCell>
                    <TableCell className="font-semibold">{g.score}</TableCell>
                    <TableCell>{g.letter_grade ?? "—"}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{new Date(g.recorded_at).toLocaleDateString()}</TableCell>
                    <TableCell className="text-right"><EditGradeDialog grade={g} /></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </Card>
      )}
    </div>
  );
}

function NewGradeDialog({ defaultCourseId }: { defaultCourseId?: string }) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ student_id: "", course_id: defaultCourseId ?? "", score: "", letter_grade: "" });
  const create = useCreateGrade();
  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    create.mutate(
      { student_id: form.student_id, course_id: form.course_id, score: form.score, letter_grade: form.letter_grade || null },
      {
        onSuccess: () => { toast.success("Grade recorded"); setOpen(false); },
        onError: (e) => toast.error(apiErrorMessage(e)),
      },
    );
  };
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild><Button><Plus className="h-4 w-4 mr-1" /> New grade</Button></DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>Record grade</DialogTitle></DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-1.5"><Label>Student ID</Label>
            <Input required value={form.student_id} onChange={(e) => setForm({ ...form, student_id: e.target.value })} /></div>
          <div className="space-y-1.5"><Label>Course ID</Label>
            <Input required value={form.course_id} onChange={(e) => setForm({ ...form, course_id: e.target.value })} /></div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5"><Label>Score (0-100)</Label>
              <Input required type="number" min={0} max={100} step={0.01} value={form.score} onChange={(e) => setForm({ ...form, score: e.target.value })} /></div>
            <div className="space-y-1.5"><Label>Letter</Label>
              <Input value={form.letter_grade} onChange={(e) => setForm({ ...form, letter_grade: e.target.value })} /></div>
          </div>
          <DialogFooter>
            <Button type="submit" disabled={create.isPending}>{create.isPending ? "Saving…" : "Save"}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function EditGradeDialog({ grade }: { grade: GradeRead }) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ score: grade.score, letter_grade: grade.letter_grade ?? "", reason: "" });
  const update = useUpdateGrade();
  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    update.mutate({ id: grade.id, body: { score: form.score, letter_grade: form.letter_grade || null, reason: form.reason || null } }, {
      onSuccess: () => { toast.success("Grade updated"); setOpen(false); },
      onError: (e) => toast.error(apiErrorMessage(e)),
    });
  };
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild><Button variant="ghost" size="sm"><Pencil className="h-3.5 w-3.5" /></Button></DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>Edit grade</DialogTitle></DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5"><Label>Score</Label>
              <Input required type="number" min={0} max={100} step={0.01} value={form.score} onChange={(e) => setForm({ ...form, score: e.target.value })} /></div>
            <div className="space-y-1.5"><Label>Letter</Label>
              <Input value={form.letter_grade} onChange={(e) => setForm({ ...form, letter_grade: e.target.value })} /></div>
          </div>
          <div className="space-y-1.5"><Label>Reason (audit)</Label>
            <Textarea rows={3} value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} /></div>
          <DialogFooter>
            <Button type="submit" disabled={update.isPending}>{update.isPending ? "Saving…" : "Save"}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
