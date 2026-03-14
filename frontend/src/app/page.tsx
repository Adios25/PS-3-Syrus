import React from "react";
import ChatInterface from "@/components/ChatInterface";
import Checklist from "@/components/Checklist";
import SessionPanel from "@/components/SessionPanel";
import { Badge } from "@/components/ui/badge";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Bot, Sparkles } from "lucide-react";

const capabilities = [
  {
    label: "Analyze",
    title: "Context-aware onboarding help",
    description: "Grounded answers for setup, architecture, policies, org structure, and onboarding FAQs.",
  },
  {
    label: "Code",
    title: "Starter ticket and first-task path",
    description: "The session assigns a first task and keeps the onboarding flow tied to actionable engineering work.",
  },
  {
    label: "Sessions",
    title: "Tracked flow execution",
    description: "Progress, actions, grounded FAQs, and final HR handoff are shown as session activity.",
  },
  {
    label: "Secure",
    title: "Compliance and onboarding completion",
    description: "Checklist completion and the HR handoff report remain explicit instead of buried in the chat.",
  },
];

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <div className="border-b border-slate-200 bg-white shadow-sm">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-6 md:px-8 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-100 text-indigo-600 shadow-sm">
              <Bot className="h-8 w-8" />
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-indigo-500 flex items-center gap-1">
                <Sparkles className="h-3 w-3" />
                Automated Onboarding
              </p>
              <h1 className="text-3xl font-bold tracking-tight text-slate-950">
                ODA (Onboarding Developer Agent)
              </h1>
              <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-600">
                A streamlined, intelligent workspace built around grounded chat and a role-specific onboarding plan.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-7xl space-y-6 px-4 py-6 md:px-8">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {capabilities.map((item) => (
            <Card key={item.label} className="border-slate-200 bg-white shadow-sm hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <Badge variant="outline" className="w-fit bg-slate-50 text-slate-600 border-slate-200">
                  {item.label}
                </Badge>
                <CardTitle className="text-base text-slate-800 font-semibold">{item.title}</CardTitle>
                <CardDescription className="text-slate-500">{item.description}</CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>

        <div className="flex flex-col gap-6">
          <ChatInterface />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Checklist />
            <SessionPanel />
          </div>
        </div>
      </div>
    </main>
  );
}
