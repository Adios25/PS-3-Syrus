"use client";

import {
  CheckCircle2,
  CircleDashed,
  Clock3,
  FileText,
  GitPullRequestDraft,
  ShieldCheck,
  Sparkles,
  UserRound,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useStore } from "@/store/useStore";

function formatTimestamp(value?: string | null) {
  if (!value) {
    return "Current session";
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

export default function SessionPanel() {
  const {
    assignedTicket,
    checklist,
    completionEmail,
    generatedFaqs,
    inferenceNotes,
    mcpActions,
    messages,
    missingProfileFields,
    profile,
    progressPercent,
    sessionId,
  } = useStore();

  const flowSteps = [
    {
      title: "Capture developer context",
      done: missingProfileFields.length === 0,
      detail:
        missingProfileFields.length === 0
          ? `${profile.name || "Developer"} profile is complete.`
          : `Still needed: ${missingProfileFields.join(", ")}.`,
    },
    {
      title: "Generate onboarding plan",
      done: checklist.length > 0,
      detail: checklist.length
        ? `${checklist.length} checklist tasks are active.`
        : "Checklist is created after the required profile fields are captured.",
    },
    {
      title: "Assign first task",
      done: Boolean(assignedTicket),
      detail: assignedTicket
        ? `${assignedTicket.ticket_id} • ${assignedTicket.title}`
        : "Starter ticket is assigned from the dataset once the path is known.",
    },
    {
      title: "Track session activity",
      done: messages.length > 1 || mcpActions.length > 0 || generatedFaqs.length > 0,
      detail: `${messages.length} chat messages, ${mcpActions.length} actions, ${generatedFaqs.length} grounded FAQs.`,
    },
    {
      title: "Generate HR handoff",
      done: Boolean(completionEmail),
      detail: completionEmail
        ? `Report ${completionEmail.report_id || "generated"} is ready for HR review.`
        : "Available after all checklist items are complete.",
    },
  ];

  const activity = [
    sessionId
      ? {
          title: "Session started",
          detail: `Session ${sessionId.slice(0, 8)} is active and tracking onboarding flow state.`,
          time: "Current session",
          kind: "session",
        }
      : null,
    profile.matched_persona_name
      ? {
          title: "Persona matched",
          detail: `${profile.matched_persona_name} was selected as the closest onboarding profile.`,
          time: "Current session",
          kind: "profile",
        }
      : null,
    assignedTicket
      ? {
          title: "Starter ticket assigned",
          detail: `${assignedTicket.ticket_id} was attached to the onboarding path.`,
          time: "Current session",
          kind: "ticket",
        }
      : null,
    ...mcpActions.slice(-2).map((action) => ({
      title: action.tool_name,
      detail:
        typeof action.payload.message === "string"
          ? action.payload.message
          : "Action executed for the onboarding session.",
      time: "Current session",
      kind: "action",
    })),
    ...generatedFaqs.slice(-2).map((faq) => ({
      title: "Grounded FAQ captured",
      detail: faq.question,
      time: formatTimestamp(faq.created_at),
      kind: "faq",
    })),
    completionEmail
      ? {
          title: "HR report generated",
          detail: completionEmail.subject,
          time: formatTimestamp(completionEmail.generated_at),
          kind: "report",
        }
      : null,
  ].filter(Boolean) as Array<{
    title: string;
    detail: string;
    time: string;
    kind: "session" | "profile" | "ticket" | "action" | "faq" | "report";
  }>;

  const distinctSources = new Set(
    messages.flatMap((message) => message.sources?.map((source) => source.source_id) ?? []),
  );

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <CardTitle>Developer Flow</CardTitle>
              <CardDescription>
                A cleaner, session-based flow orchestrated by ODA.
              </CardDescription>
            </div>
            <Badge variant="outline">Automate / Sessions</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {flowSteps.map((step) => (
            <div
              key={step.title}
              className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3"
            >
              <div className="mt-0.5 shrink-0">
                {step.done ? (
                  <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                ) : (
                  <Clock3 className="h-5 w-5 text-slate-400" />
                )}
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-950">{step.title}</p>
                <p className="mt-1 text-sm leading-6 text-slate-600">{step.detail}</p>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-4">
          <CardTitle>Session Activity</CardTitle>
          <CardDescription>
            ODA tracks onboarding progress as sessions. This panel mirrors that progression.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-4">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Progress</p>
              <p className="mt-2 text-2xl font-semibold text-slate-950">{progressPercent}%</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-4">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Sources</p>
              <p className="mt-2 text-2xl font-semibold text-slate-950">{distinctSources.size}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-4">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Messages</p>
              <p className="mt-2 text-2xl font-semibold text-slate-950">{messages.length}</p>
            </div>
          </div>

          <Separator />

          <div className="space-y-4">
            {activity.length ? (
              activity.map((item, index) => (
                <div key={`${item.title}-${index}`} className="flex gap-3">
                  <div className="flex w-8 shrink-0 justify-center">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full border border-slate-200 bg-white">
                      {item.kind === "profile" ? <UserRound className="h-4 w-4 text-sky-700" /> : null}
                      {item.kind === "ticket" ? <GitPullRequestDraft className="h-4 w-4 text-indigo-700" /> : null}
                      {item.kind === "action" ? <Sparkles className="h-4 w-4 text-amber-700" /> : null}
                      {item.kind === "faq" ? <FileText className="h-4 w-4 text-teal-700" /> : null}
                      {item.kind === "report" ? <ShieldCheck className="h-4 w-4 text-emerald-700" /> : null}
                      {item.kind === "session" ? <CircleDashed className="h-4 w-4 text-slate-600" /> : null}
                    </div>
                  </div>
                  <div className="min-w-0 flex-1 pb-4">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-semibold text-slate-950">{item.title}</p>
                      <span className="text-xs uppercase tracking-[0.16em] text-slate-400">{item.time}</span>
                    </div>
                    <p className="mt-1 text-sm leading-6 text-slate-600">{item.detail}</p>
                  </div>
                </div>
              ))
            ) : (
              <div className="rounded-2xl border border-dashed border-slate-300 px-4 py-5 text-sm leading-6 text-slate-500">
                Session activity appears here as soon as the onboarding conversation starts.
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {inferenceNotes.length ? (
        <Card>
          <CardHeader className="pb-4">
            <CardTitle>Inference Notes</CardTitle>
            <CardDescription>Fallback reasoning applied when the dataset did not have an exact path match.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {inferenceNotes.slice(-2).map((note) => (
              <div key={note} className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                {note}
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
