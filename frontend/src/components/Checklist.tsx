"use client";

import React from 'react';
import { CheckCircle2, Circle, ClipboardList, Inbox, Mail, Sparkles, UserRound } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { useStore } from '../store/useStore';
import { StatusBadge } from './workflow/StatusBadge';
import { EmptyState } from './common/EmptyState';

export default function Checklist() {
  const {
    checklist,
    toggleChecklistItem,
    progressPercent,
    status,
    profile,
    isLoadingChecklist,
    finalizeOnboarding,
    completionEmail,
    assignedTicket,
    inferenceNotes,
    completionEmailPreview,
  } = useStore();

  const completedCount = checklist.filter((item) => item.is_completed).length;
  const allTasksComplete = checklist.length > 0 && checklist.every((item) => item.is_completed);
  const canFinalize = allTasksComplete && !completionEmail;
  const nextPending = checklist.find((item) => !item.is_completed);
  const statusVariant = completionEmail ? 'success' : allTasksComplete ? 'warning' : 'secondary';
  const statusLabel = completionEmail ? 'Completed' : allTasksComplete ? 'Ready for HR Handoff' : status === 'completed' ? 'Checklist Done' : 'Active';

  return (
    <Card className="h-full">
      <CardHeader className="space-y-4 pb-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardTitle className="flex items-center gap-2">
              <ClipboardList className="h-5 w-5 text-slate-700" />
              Onboarding Plan
            </CardTitle>
            <CardDescription>
              Role-specific onboarding path and essential integration tasks.
            </CardDescription>
          </div>
          <Badge variant={statusVariant}>
            {statusLabel}
          </Badge>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <div className="flex items-center gap-2 text-sm text-slate-800">
            <UserRound className="h-4 w-4 text-slate-500" />
            <span className="font-medium">
              {profile.name || 'Name pending'} • {profile.role || 'Role pending'} • {profile.experience_level || 'Level pending'}
            </span>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            <Badge variant="outline">Team: {profile.team || 'Pending'}</Badge>
            <Badge variant="outline">
              Stack: {profile.tech_stack.length ? profile.tech_stack.join(', ') : 'Pending'}
            </Badge>
            {profile.matched_persona_name ? (
              <Badge variant="secondary">{profile.matched_persona_name}</Badge>
            ) : null}
          </div>
          {(profile.manager_name || profile.mentor_name) ? (
            <p className="mt-3 text-sm text-slate-600">
              Manager: {profile.manager_name || 'N/A'} | Mentor: {profile.mentor_name || 'N/A'}
            </p>
          ) : null}
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-medium text-slate-700">
              {completedCount}/{checklist.length} tasks complete
            </p>
            <p className="text-sm font-semibold text-slate-900">{progressPercent}%</p>
          </div>
          <Progress value={progressPercent} />
          <div className="flex flex-wrap gap-2">
            {nextPending ? (
              <Badge variant="warning">Next: {nextPending.checklist_code}</Badge>
            ) : (
              <Badge variant="success">All tasks completed</Badge>
            )}
            {assignedTicket ? <Badge variant="outline">{assignedTicket.ticket_id}</Badge> : null}
          </div>
        </div>

        {inferenceNotes.length > 0 ? (
          <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            {inferenceNotes[inferenceNotes.length - 1]}
          </div>
        ) : null}
      </CardHeader>

      <CardContent className="space-y-4">
        <Separator />

        <div className="max-h-[420px] space-y-3 overflow-y-auto pr-1">
          {Array.from(checklist).sort((a, b) => {
            if (a.is_completed === b.is_completed) return 0;
            return a.is_completed ? 1 : -1;
          }).map((item) => (
            <button
              key={item.item_id}
              type="button"
              onClick={() => toggleChecklistItem(item.item_id)}
              disabled={isLoadingChecklist}
              className={`w-full rounded-2xl border p-4 text-left transition ${item.is_completed
                  ? 'border-slate-200 bg-slate-50/80'
                  : 'border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm'
                }`}
            >
              <div className="flex items-start gap-4">
                <div className="mt-0.5 shrink-0">
                  {item.is_completed ? (
                    <CheckCircle2 className="h-6 w-6 text-emerald-500" />
                  ) : (
                    <Circle className="h-6 w-6 text-slate-300" />
                  )}
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant={item.is_completed ? 'success' : 'outline'}>
                      {item.checklist_code || `#${item.item_id}`}
                    </Badge>
                    <Badge variant="secondary">{item.category}</Badge>
                    <Badge variant="outline">{item.deadline}</Badge>
                    {/* FLOW-FE-001: StatusBadge showing workflow-level status */}
                    <StatusBadge status={item.is_completed ? 'active' : 'draft'} />
                  </div>

                  <p className={`mt-3 text-sm font-semibold leading-6 ${item.is_completed ? 'text-slate-500 line-through' : 'text-slate-950'}`}>
                    {item.title}
                  </p>

                  <p className="mt-2 text-sm leading-6 text-slate-600">{item.description}</p>

                  <div className="mt-3 flex flex-wrap items-center gap-2 text-xs uppercase tracking-[0.16em] text-slate-400">
                    <span>Owner: {item.owner || 'Employee'}</span>
                    <span>•</span>
                    <span>Sources: {item.source_refs.join(', ')}</span>
                  </div>
                </div>
              </div>
            </button>
          ))}

          {/* FLOW-FE-002: EmptyState when no checklist items are loaded yet */}
          {!checklist.length ? (
            <EmptyState
              icon={<Inbox className="h-6 w-6" />}
              title="No checklist items yet"
              description="The checklist appears after the onboarding profile is captured in chat."
            />
          ) : null}
        </div>

        {canFinalize ? (
          <Button type="button" variant="success" className="w-full" onClick={finalizeOnboarding}>
            <Sparkles className="h-4 w-4" />
            Generate HR Handoff
          </Button>
        ) : null}

        {completionEmail ? (
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
            <div className="flex items-center gap-2 text-emerald-900">
              <Mail className="h-4 w-4" />
              <p className="text-sm font-semibold">HR completion report generated</p>
            </div>
            <div className="mt-3 grid gap-2 text-sm text-emerald-900 sm:grid-cols-2">
              <p>Completed items: {completionEmail.completed_items.length}</p>
              <p>Pending items: {completionEmail.pending_items.length}</p>
              <p>Confidence score: {completionEmail.confidence_score}%</p>
              <p>Delivery status: {completionEmail.delivery_status || 'sent'}</p>
              {completionEmail.to?.length ? (
                <p className="sm:col-span-2">Sent to: {completionEmail.to.join(', ')}</p>
              ) : null}
            </div>
            {completionEmailPreview ? (
              <p className="mt-3 text-xs uppercase tracking-[0.18em] text-emerald-700">
                Full preview available in the HR report panel below.
              </p>
            ) : null}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
