"use client";

import React from 'react';
import { CheckCircle2, Circle, Mail, UserRound } from 'lucide-react';
import { useStore } from '../store/useStore';

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
  } = useStore();

  const completedCount = checklist.filter((item) => item.is_completed).length;
  const canFinalize = checklist.length > 0 && checklist.every((item) => item.is_completed) && status !== 'completed';

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 h-full">
      <div className="mb-6 space-y-4">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Personalized Onboarding Checklist</h2>
          <p className="text-slate-500 text-sm mt-1">
            Profile-aware onboarding path with completion tracking for HR handoff.
          </p>
        </div>

        <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
          <div className="flex items-center gap-2 text-sm text-slate-700 mb-2">
            <UserRound size={16} />
            <span>{profile.name || 'Name pending'} | {profile.role || 'Role pending'} | {profile.experience_level || 'Level pending'}</span>
          </div>
          <p className="text-xs text-slate-500">
            Team: {profile.team || 'N/A'} | Stack: {profile.tech_stack.length ? profile.tech_stack.join(', ') : 'N/A'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
            <div className="h-full bg-sky-600 transition-all duration-500 ease-out rounded-full" style={{ width: `${progressPercent}%` }} />
          </div>
          <span className="text-sm font-medium text-slate-700">{progressPercent}%</span>
        </div>

        <p className="text-xs text-slate-500">
          {completedCount}/{checklist.length} tasks complete | Status: {status === 'completed' ? 'Completed' : 'In Progress'}
        </p>
      </div>

      <div className="space-y-3 max-h-[340px] overflow-y-auto pr-1">
        {checklist.map((item) => (
          <button
            key={item.item_id}
            type="button"
            onClick={() => toggleChecklistItem(item.item_id)}
            disabled={isLoadingChecklist}
            className={`w-full text-left flex items-start gap-4 p-4 rounded-xl border transition-all ${
              item.is_completed
                ? 'bg-slate-50 border-slate-200 opacity-80'
                : 'bg-white border-sky-100 hover:border-sky-300 hover:shadow-sm'
            }`}
          >
            <div className="flex-shrink-0 mt-0.5">
              {item.is_completed ? (
                <CheckCircle2 className="text-emerald-500" size={22} />
              ) : (
                <Circle className="text-slate-300" size={22} />
              )}
            </div>
            <div>
              <div className={`font-medium ${item.is_completed ? 'line-through text-slate-500' : 'text-slate-900'}`}>
                #{item.item_id} {item.title}
              </div>
              <p className={`text-sm mt-1 ${item.is_completed ? 'text-slate-400' : 'text-slate-500'}`}>{item.description}</p>
              <p className="text-xs text-slate-400 mt-1">Sources: {item.source_refs.join(', ')}</p>
            </div>
          </button>
        ))}

        {!checklist.length && (
          <div className="text-sm text-slate-500 border border-dashed border-slate-300 rounded-xl p-4">
            Checklist will appear once your profile is captured in chat.
          </div>
        )}
      </div>

      {canFinalize && (
        <button
          type="button"
          onClick={finalizeOnboarding}
          className="mt-5 w-full bg-emerald-600 text-white rounded-xl py-2.5 text-sm font-medium hover:bg-emerald-700 transition"
        >
          Finalize Onboarding and Notify HR
        </button>
      )}

      {completionEmail && (
        <div className="mt-5 border border-emerald-200 bg-emerald-50 rounded-xl p-4 space-y-2 text-sm">
          <div className="flex items-center gap-2 text-emerald-800 font-medium">
            <Mail size={16} />
            <span>HR Completion Email Generated</span>
          </div>
          <p className="text-emerald-900">To: {completionEmail.to}</p>
          <p className="text-emerald-900">Subject: {completionEmail.subject}</p>
          <p className="text-emerald-900">Completed Items: {completionEmail.summary.completed_items.length}</p>
          <p className="text-emerald-900">Pending Items: {completionEmail.summary.pending_items.length}</p>
          <p className="text-emerald-900">Confidence Score: {completionEmail.confidence_score}</p>
        </div>
      )}
    </div>
  );
}
