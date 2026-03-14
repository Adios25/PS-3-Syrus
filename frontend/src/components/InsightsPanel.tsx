"use client";

import { BookMarked, FolderGit2, MailCheck, ShieldCheck, Sparkles, WandSparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useStore } from "@/store/useStore";

function formatTimestamp(value: string | undefined | null) {
  if (!value) {
    return "Pending";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

export default function InsightsPanel() {
  const {
    assignedTicket,
    completionEmail,
    completionEmailPreview,
    generatedFaqs,
    inferenceNotes,
    mcpActions,
  } = useStore();

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <CardTitle className="flex items-center gap-2">
                <FolderGit2 className="h-5 w-5 text-teal-700" />
                Starter Ticket
              </CardTitle>
              <CardDescription>Direct mapping from `starter_tickets.md` for the detected onboarding path.</CardDescription>
            </div>
            <Badge variant={assignedTicket ? "secondary" : "outline"}>
              {assignedTicket ? "Assigned" : "Waiting"}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {assignedTicket ? (
            <>
              <div className="rounded-2xl border border-slate-200 bg-slate-50/80 p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="outline">{assignedTicket.ticket_id}</Badge>
                  <Badge variant="secondary">{assignedTicket.project}</Badge>
                  <Badge variant="outline">{assignedTicket.priority} priority</Badge>
                </div>
                <h4 className="mt-3 text-base font-semibold text-slate-950">{assignedTicket.title}</h4>
                <p className="mt-2 text-sm leading-6 text-slate-600">{assignedTicket.description}</p>
                <p className="mt-3 text-xs uppercase tracking-[0.18em] text-slate-500">
                  Repository: {assignedTicket.repository}
                </p>
              </div>

              <div className="space-y-2">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                  Acceptance Criteria
                </p>
                <div className="space-y-2">
                  {assignedTicket.acceptance_criteria.slice(0, 4).map((criterion) => (
                    <div
                      key={criterion}
                      className="rounded-2xl border border-slate-200/80 bg-white px-4 py-3 text-sm text-slate-700"
                    >
                      {criterion}
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="rounded-2xl border border-dashed border-slate-300 px-4 py-5 text-sm leading-6 text-slate-500">
              Share your role, level, team, and stack in chat to unlock the matching starter ticket.
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <CardTitle className="flex items-center gap-2">
                <WandSparkles className="h-5 w-5 text-cyan-700" />
                Session Signals
              </CardTitle>
              <CardDescription>Live workflow activity surfaced from the agent response payload.</CardDescription>
            </div>
            <Badge variant={mcpActions.length ? "secondary" : "outline"}>
              {mcpActions.length ? `${mcpActions.length} actions` : "Idle"}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Inference Notes</p>
            {inferenceNotes.length ? (
              <div className="space-y-2">
                {inferenceNotes.slice(-2).map((note) => (
                  <div key={note} className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                    {note}
                  </div>
                ))}
              </div>
            ) : (
              <div className="rounded-2xl border border-dashed border-slate-300 px-4 py-3 text-sm text-slate-500">
                No fallback or inference notes yet.
              </div>
            )}
          </div>

          <Separator />

          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">MCP Actions</p>
            {mcpActions.length ? (
              <div className="space-y-2">
                {mcpActions.slice(-4).map((action, index) => (
                  <div key={`${action.tool_name}-${index}`} className="rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-semibold text-slate-900">{action.tool_name}</p>
                      <Badge variant={action.status === "success" ? "success" : "warning"}>{action.status}</Badge>
                    </div>
                    <p className="mt-2 text-sm text-slate-600">
                      {typeof action.payload.message === "string" ? action.payload.message : "Action executed."}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="rounded-2xl border border-dashed border-slate-300 px-4 py-3 text-sm text-slate-500">
                Access provisioning and welcome actions will appear here after chat-triggered MCP steps.
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <CardTitle className="flex items-center gap-2">
                <BookMarked className="h-5 w-5 text-sky-700" />
                Generated FAQ Cache
              </CardTitle>
              <CardDescription>Grounded Q&A entries captured from session questions against the searchable docs.</CardDescription>
            </div>
            <Badge variant={generatedFaqs.length ? "secondary" : "outline"}>
              {generatedFaqs.length ? `${generatedFaqs.length} captured` : "Empty"}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {generatedFaqs.length ? (
            generatedFaqs.slice(-3).reverse().map((faq) => (
              <div key={`${faq.question}-${faq.created_at}`} className="rounded-2xl border border-slate-200 bg-white px-4 py-4">
                <p className="text-sm font-semibold text-slate-950">{faq.question}</p>
                <p className="mt-2 text-sm leading-6 text-slate-600">{faq.answer}</p>
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  {faq.source_ids.map((sourceId) => (
                    <Badge key={sourceId} variant="outline">
                      {sourceId}
                    </Badge>
                  ))}
                  <span className="text-xs uppercase tracking-[0.16em] text-slate-400">
                    {formatTimestamp(faq.created_at)}
                  </span>
                </div>
              </div>
            ))
          ) : (
            <div className="rounded-2xl border border-dashed border-slate-300 px-4 py-5 text-sm leading-6 text-slate-500">
              Ask setup, policy, architecture, or standards questions and the agent will store the grounded FAQ trail here.
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <CardTitle className="flex items-center gap-2">
                <MailCheck className="h-5 w-5 text-emerald-700" />
                HR Completion Report
              </CardTitle>
              <CardDescription>Template-backed summary generated from `email_templates.md` after all checklist items are done.</CardDescription>
            </div>
            <Badge variant={completionEmail ? "success" : "outline"}>
              {completionEmail ? "Generated" : "Pending"}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {completionEmail ? (
            <>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-2xl border border-slate-200 bg-slate-50/80 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Delivery</p>
                  <p className="mt-2 text-base font-semibold text-slate-950">{completionEmail.subject}</p>
                  <p className="mt-2 text-sm text-slate-600">To: {completionEmail.to.join(", ")}</p>
                  <p className="mt-1 text-sm text-slate-600">CC: {completionEmail.cc.join(", ")}</p>
                </div>

                <div className="rounded-2xl border border-slate-200 bg-slate-50/80 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Summary</p>
                  <div className="mt-2 space-y-1 text-sm text-slate-700">
                    <p>Status: {completionEmail.summary.status}</p>
                    <p>Completed: {completionEmail.checklist_summary.completed_percentage}%</p>
                    <p>Confidence: {completionEmail.confidence_score}%</p>
                    <p>Report ID: {completionEmail.report_id ?? "N/A"}</p>
                  </div>
                </div>
              </div>

              {completionEmail.first_task_status ? (
                <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-4">
                  <div className="flex items-center gap-2 text-emerald-900">
                    <ShieldCheck className="h-4 w-4" />
                    <p className="text-sm font-semibold">First task status: {completionEmail.first_task_status.status}</p>
                  </div>
                  <p className="mt-2 text-sm text-emerald-800">{completionEmail.first_task_status.ticket}</p>
                </div>
              ) : null}

              {completionEmailPreview ? (
                <div className="rounded-2xl border border-slate-200 bg-slate-950 p-4">
                  <div className="mb-3 flex items-center gap-2 text-slate-200">
                    <Sparkles className="h-4 w-4" />
                    <p className="text-xs font-semibold uppercase tracking-[0.18em]">Preview</p>
                  </div>
                  <pre className="overflow-x-auto whitespace-pre-wrap font-mono text-xs leading-6 text-slate-100">
                    {completionEmailPreview}
                  </pre>
                </div>
              ) : null}
            </>
          ) : (
            <div className="rounded-2xl border border-dashed border-slate-300 px-4 py-5 text-sm leading-6 text-slate-500">
              Finish every checklist item, then use the completion action to generate the structured HR handoff report.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
