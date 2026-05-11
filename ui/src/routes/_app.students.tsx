import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { useStudents } from "@/hooks/api";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { PageLoader, EmptyState, ErrorState } from "@/components/States";
import { RoleGate } from "@/components/RoleGate";
import { apiErrorMessage } from "@/lib/api";
import { Search } from "lucide-react";

export const Route = createFileRoute("/_app/students")({ component: StudentsPage });

function StudentsPage() {
  return (
    <RoleGate roles={["TEACHER", "DEAN", "ADMIN"]}>
      <Inner />
    </RoleGate>
  );
}

function Inner() {
  const { data, isLoading, error, refetch } = useStudents();
  const [q, setQ] = useState("");
  const filtered = (data ?? []).filter(
    (s) =>
      !q ||
      s.student_number.toLowerCase().includes(q.toLowerCase()) ||
      (s.specialty ?? "").toLowerCase().includes(q.toLowerCase()) ||
      (s.academic_group ?? "").toLowerCase().includes(q.toLowerCase()),
  );
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Students</h1>
        <p className="text-sm text-muted-foreground">Directory of enrolled students.</p>
      </div>
      <Card>
        <div className="p-3 border-b">
          <div className="relative max-w-xs">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input className="pl-8" placeholder="Search students…"
              value={q} onChange={(e) => setQ(e.target.value)} />
          </div>
        </div>
        {isLoading ? <PageLoader /> :
         error ? <ErrorState message={apiErrorMessage(error)} onRetry={refetch} /> :
         filtered.length === 0 ? <EmptyState title="No students found" /> : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Student #</TableHead>
                <TableHead>Group</TableHead>
                <TableHead>Specialty</TableHead>
                <TableHead>Status</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((s) => (
                <TableRow key={s.id}>
                  <TableCell className="font-mono text-xs">{s.student_number}</TableCell>
                  <TableCell>{s.academic_group ?? "—"}</TableCell>
                  <TableCell>{s.specialty ?? "—"}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">{s.enrollment_status}</TableCell>
                  <TableCell className="text-right">
                    <Link to="/students/$studentId" params={{ studentId: s.id }}
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
