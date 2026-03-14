"use client";

import React, { useState, useRef } from 'react';
import { AlertCircle, ArrowUp, Bot, CircleDashed, Sparkles, UserRound } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';
import { useStore } from '../store/useStore';

const quickPrompts = [
  'My name is Alex Carter. I joined as a backend intern working on Node.js in Squad Beta.',
  'Show my checklist status.',
  'How do I set up the local environment?',
  'Mark C-01 done',
  'Finish onboarding',
];

function formatMessageTime(date: Date) {
  return new Intl.DateTimeFormat('en', {
    hour: 'numeric',
    minute: '2-digit',
  }).format(date);
}

export default function ChatInterface() {
  const { checklist, completionEmail, messages, sendMessage, isTyping, error, missingProfileFields, profile, sessionId, status } = useStore();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const allTasksComplete = checklist.length > 0 && checklist.every((item) => item.is_completed);
  const statusLabel = completionEmail ? 'Completed' : allTasksComplete ? 'Ready for HR Handoff' : status === 'completed' ? 'Checklist Done' : 'In Progress';
  const statusVariant = completionEmail ? 'success' : allTasksComplete ? 'warning' : 'outline';

  // Removed auto-scroll useEffect so the chat component no longer forcibly pulls the page down.

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isTyping) {
      return;
    }
    const message = input;
    setInput('');
    await sendMessage(message);
  };

  return (
    <Card className="flex h-[860px] flex-col overflow-hidden">
      <CardHeader className="border-b border-slate-200 bg-white pb-4">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="secondary">Agentic Chat</Badge>
              <Badge variant="outline">Grounded answers</Badge>
              <Badge variant={statusVariant}>{statusLabel}</Badge>
            </div>
            <CardTitle className="mt-3 flex items-center gap-2 text-xl">
              <Bot className="h-5 w-5 text-slate-700" />
              Onboarding Workspace
            </CardTitle>
            <CardDescription className="mt-1 max-w-2xl">
              Ask onboarding questions, capture the developer profile, and drive the session forward with explicit source references.
            </CardDescription>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Session</p>
            <p className="mt-2 font-medium">{sessionId ? sessionId.slice(0, 8) : 'Not started'}</p>
            <p className="mt-1 text-slate-500">
              {profile.name || 'Name pending'} • {profile.role || 'Role pending'} • {profile.team || 'Team pending'}
            </p>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex min-h-0 flex-1 flex-col px-0 pb-0">
        <div className="border-b border-slate-200 px-6 py-4">
          <div className="flex flex-wrap gap-2">
            {quickPrompts.map((prompt) => (
              <Button
                key={prompt}
                variant="outline"
                size="sm"
                onClick={() => setInput(prompt)}
                className="max-w-full justify-start rounded-full text-left"
              >
                <Sparkles className="h-3.5 w-3.5 shrink-0 text-slate-500" />
                <span className="truncate">{prompt}</span>
              </Button>
            ))}
          </div>
        </div>

        <div className="border-b border-slate-200 bg-slate-50 px-6 py-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={missingProfileFields.length ? 'warning' : 'success'}>
              {missingProfileFields.length ? 'Profile incomplete' : 'Profile complete'}
            </Badge>
            {missingProfileFields.length ? (
              missingProfileFields.map((field) => (
                <Badge key={field} variant="outline">
                  {field}
                </Badge>
              ))
            ) : (
              <span className="text-sm text-slate-600">All required onboarding fields are captured.</span>
            )}
          </div>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto bg-slate-50 px-6 py-5">
          <div className="space-y-5">
            {messages.map((msg) => (
              <div key={msg.id} className={cn('flex', msg.sender === 'user' ? 'justify-end' : 'justify-start')}>
                <div className={cn('max-w-[88%] space-y-2', msg.sender === 'user' ? 'items-end text-right' : 'items-start')}>
                  <div
                    className={cn(
                      'flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.18em]',
                      msg.sender === 'user' ? 'justify-end text-slate-500' : 'text-slate-500',
                    )}
                  >
                    {msg.sender === 'user' ? <UserRound className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5" />}
                    <span>{msg.sender === 'user' ? 'You' : 'Agent'}</span>
                    <span suppressHydrationWarning>{formatMessageTime(msg.timestamp)}</span>
                  </div>

                  <div
                    className={cn(
                      'rounded-[24px] border px-5 py-4 text-sm leading-7 shadow-sm',
                      msg.sender === 'user'
                        ? 'rounded-br-md border-slate-900 bg-slate-900 text-white'
                        : 'rounded-bl-md border-slate-200 bg-white text-slate-800',
                    )}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  </div>

                  {msg.sender === 'agent' && msg.sources?.length ? (
                    <div className="space-y-2 rounded-[24px] border border-sky-200/80 bg-sky-50/80 px-4 py-3">
                      <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-800">
                        <CircleDashed className="h-3.5 w-3.5" />
                        Reference Docs
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {msg.sources.map((source) => (
                          <div key={`${msg.id}-${source.source_id}-${source.section}`} className="rounded-full border border-sky-200 bg-white px-3 py-1.5 text-xs text-slate-700">
                            <span className="font-semibold text-sky-800">{source.source_id}</span> • {source.section}
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : null}
                </div>
              </div>
            ))}

            {isTyping ? (
              <div className="flex justify-start">
                <div className="max-w-[70%] rounded-[24px] rounded-bl-md border border-slate-200 bg-white px-5 py-4 text-sm text-slate-500 shadow-sm">
                  Agent is analyzing the onboarding context and preparing the next step.
                </div>
              </div>
            ) : null}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {error ? (
          <div className="border-t border-rose-200 bg-rose-50 px-6 py-3 text-sm text-rose-700">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              <span>{error}</span>
            </div>
          </div>
        ) : null}

        <div className="space-y-4 px-6 py-5">
          <Separator />
          <form onSubmit={submit} className="flex flex-col gap-3 sm:flex-row">
            <Input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Ask a grounded onboarding question or share role, level, stack, and team details..."
              className="flex-1"
            />
            <Button type="submit" disabled={!input.trim() || isTyping} className="sm:min-w-[140px]">
              <ArrowUp className="h-4 w-4" />
              Send
            </Button>
          </form>
        </div>
      </CardContent>
    </Card>
  );
}
