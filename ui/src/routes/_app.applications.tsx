import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import {
  useApplications,
  useCreateApplication,
  useMyApplications,
  useReviewApplication,
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
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { StatusBadge } from "@/components/StatusBadge";
import { PageLoader, EmptyState, ErrorState } from "@/components/States";
import { apiErrorMessage } from "@/lib/api";
import { toast } from "sonner";
import type { ApplicationRead, ApplicationStatus } from "@/types/api";
import { Plus } from "lucide-react";

export const Route = createFileRoute("/_app/applications")({ component: Applications });

function Applications() {
  const { hasAnyRole } = useAuthStore();
  const isReviewer = hasAnyRole(["DEAN", "ADMIN"]);
  const allQ = useApplications();
  const myQ = useMyApplications();
  const data = isReviewer ? allQ.data : myQ.data;
  const isLoading = isReviewer ? allQ.isLoading : myQ.isLoading;
  const error = isReviewer ? allQ.error : myQ.error;
  const refetch = isReviewer ? allQ.refetch : myQ.refetch;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Applications</h1>
          <p className="text-sm text-muted-foreground">
            {isReviewer ? "Review submitted enrollment applications." : "Track your enrollment applications."}
          </p>
        </div>
        <NewApplicationDialog />
      </div>

      <Card>
        {isLoading ? (
          <PageLoader />
        ) : error ? (
          <ErrorState message={apiErrorMessage(error)} onRetry={refetch} />
        ) : !data || data.length === 0 ? (
          <EmptyState title="No applications" description="Submit a new application to get started." />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Program</TableHead>
                <TableHead>Intake</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Submitted</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((a) => (
                <TableRow key={a.id}>
                  <TableCell className="font-medium">{a.program_code}</TableCell>
                  <TableCell>{a.intake_term}</TableCell>
                  <TableCell><StatusBadge status={a.status} /></TableCell>
                  <TableCell className="text-muted-foreground text-sm">
                    {new Date(a.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell className="text-right">
                    {isReviewer ? <ReviewDialog app={a} /> : <ViewStatement app={a} />}
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

function NewApplicationDialog() {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ program_code: "", intake_term: "", statement: "" });
  const create = useCreateApplication();
  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    create.mutate(
      { program_code: form.program_code, intake_term: form.intake_term, statement: form.statement || null },
      {
        onSuccess: () => { toast.success("Application submitted"); setOpen(false); setForm({ program_code: "", intake_term: "", statement: "" }); },
        onError: (e) => toast.error(apiErrorMessage(e)),
      },
    );
  };
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button><Plus className="h-4 w-4 mr-1" /> New application</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>Submit enrollment application</DialogTitle></DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="program_code">Program code</Label>
            <Input id="program_code" required value={form.program_code}
              onChange={(e) => setForm({ ...form, program_code: e.target.value })} placeholder="e.g. CS-BSc" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="intake_term">Intake term</Label>
            <Input id="intake_term" required value={form.intake_term}
              onChange={(e) => setForm({ ...form, intake_term: e.target.value })} placeholder="e.g. Fall 2026" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="statement">Personal statement</Label>
            <Textarea id="statement" rows={5} value={form.statement}
              onChange={(e) => setForm({ ...form, statement: e.target.value })} />
          </div>
          <DialogFooter>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? "Submitting…" : "Submit"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function ReviewDialog({ app }: { app: ApplicationRead }) {
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState<ApplicationStatus>(app.status as ApplicationStatus);
  const [notes, setNotes] = useState(app.decision_notes ?? "");
  const review = useReviewApplication();

  const submit = () => {
    review.mutate(
      { id: app.id, body: { status, notes: notes || null } },
      {
        onSuccess: () => { toast.success("Application updated"); setOpen(false); },
        onError: (e) => toast.error(apiErrorMessage(e)),
      },
    );
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="sm">Review</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>Review application</DialogTitle></DialogHeader>
        <div className="space-y-3 text-sm">
          <div>
            <div className="text-xs text-muted-foreground">Program</div>
            <div className="font-medium">{app.program_code} — {app.intake_term}</div>
          </div>
          {app.statement && (
            <div>
              <div className="text-xs text-muted-foreground mb-1">Statement</div>
              <div className="rounded-md border p-3 bg-muted/30 max-h-40 overflow-auto whitespace-pre-wrap">{app.statement}</div>
            </div>
          )}
          <div className="space-y-1.5">
            <Label>Status</Label>
            <Select value={status} onValueChange={(v) => setStatus(v as ApplicationStatus)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {(["PENDING","UNDER_REVIEW","APPROVED","REJECTED","ENROLLED"] as ApplicationStatus[]).map(s => (
                  <SelectItem key={s} value={s}>{s.replace("_"," ")}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Decision notes</Label>
            <Textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={4} />
          </div>
        </div>
        <DialogFooter>
          <Button onClick={submit} disabled={review.isPending}>
            {review.isPending ? "Saving…" : "Save decision"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function ViewStatement({ app }: { app: ApplicationRead }) {
  const [open, setOpen] = useState(false);
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild><Button variant="ghost" size="sm">View</Button></DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>Application details</DialogTitle></DialogHeader>
        <div className="space-y-3 text-sm">
          <div><span className="text-muted-foreground">Program: </span>{app.program_code}</div>
          <div><span className="text-muted-foreground">Intake: </span>{app.intake_term}</div>
          <div><span className="text-muted-foreground">Status: </span><StatusBadge status={app.status} /></div>
          {app.statement && (
            <div>
              <div className="text-xs text-muted-foreground mb-1">Statement</div>
              <div className="rounded-md border p-3 bg-muted/30 whitespace-pre-wrap">{app.statement}</div>
            </div>
          )}
          {app.decision_notes && (
            <div>
              <div className="text-xs text-muted-foreground mb-1">Decision notes</div>
              <div className="rounded-md border p-3 bg-muted/30">{app.decision_notes}</div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
