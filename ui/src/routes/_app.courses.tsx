import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { useCourses, useCreateCourse } from "@/hooks/api";
import { useAuthStore } from "@/store/auth-store";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter,
} from "@/components/ui/dialog";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { PageLoader, EmptyState, ErrorState } from "@/components/States";
import { apiErrorMessage } from "@/lib/api";
import { toast } from "sonner";
import { Plus, Search } from "lucide-react";

export const Route = createFileRoute("/_app/courses")({ component: CoursesPage });

function CoursesPage() {
  const { hasAnyRole } = useAuthStore();
  const canCreate = hasAnyRole(["DEAN", "ADMIN"]);
  const { data, isLoading, error, refetch } = useCourses();
  const [q, setQ] = useState("");
  const filtered = (data ?? []).filter((c) => !q || c.code.toLowerCase().includes(q.toLowerCase()));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Courses</h1>
          <p className="text-sm text-muted-foreground">Browse and manage course catalog.</p>
        </div>
        {canCreate && <NewCourseDialog />}
      </div>

      <Card>
        <div className="p-3 border-b">
          <div className="relative max-w-xs">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input className="pl-8" placeholder="Search by code…"
              value={q} onChange={(e) => setQ(e.target.value)} />
          </div>
        </div>
        {isLoading ? <PageLoader /> :
         error ? <ErrorState message={apiErrorMessage(error)} onRetry={refetch} /> :
         filtered.length === 0 ? <EmptyState title="No courses" /> : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Code</TableHead>
                <TableHead>Credits</TableHead>
                <TableHead>Teacher</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((c) => (
                <TableRow key={c.id}>
                  <TableCell className="font-medium">{c.code}</TableCell>
                  <TableCell>{c.credits}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {c.teacher?.employee_id ?? c.teacher_id.slice(0, 8)}
                    {c.teacher?.department && <> · <span>{c.teacher.department}</span></>}
                  </TableCell>
                  <TableCell className="text-right">
                    <Link to="/courses/$courseId" params={{ courseId: c.id }}
                      className="text-sm text-primary hover:underline">Open</Link>
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

function NewCourseDialog() {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ code: "", credits: "", teacher_id: "" });
  const create = useCreateCourse();
  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    create.mutate(
      { code: form.code, credits: form.credits, teacher_id: form.teacher_id },
      {
        onSuccess: () => { toast.success("Course created"); setOpen(false); setForm({ code: "", credits: "", teacher_id: "" }); },
        onError: (e) => toast.error(apiErrorMessage(e)),
      },
    );
  };
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild><Button><Plus className="h-4 w-4 mr-1" /> New course</Button></DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>Create course</DialogTitle></DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-1.5">
            <Label>Course code</Label>
            <Input required value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} />
          </div>
          <div className="space-y-1.5">
            <Label>Credits</Label>
            <Input required type="number" step="0.5" value={form.credits}
              onChange={(e) => setForm({ ...form, credits: e.target.value })} />
          </div>
          <div className="space-y-1.5">
            <Label>Teacher ID (UUID)</Label>
            <Input required value={form.teacher_id} onChange={(e) => setForm({ ...form, teacher_id: e.target.value })} />
          </div>
          <DialogFooter>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? "Creating…" : "Create"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
