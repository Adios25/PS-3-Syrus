import React from "react";
import ChatInterface from "@/components/ChatInterface";
import Checklist from "@/components/Checklist";

export default function Home() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_#f0f9ff,_#f8fafc_40%,_#eef2ff)] text-slate-900 p-6 md:p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        <header className="flex flex-col md:flex-row md:justify-between md:items-end gap-4 border-b border-slate-200 pb-4">
          <div>
            <p className="text-xs tracking-[0.25em] uppercase text-slate-500">Antigravity Engineering</p>
            <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-slate-900 mt-1">PS-03 Autonomous Developer Onboarding</h1>
            <p className="text-slate-600 mt-2 max-w-3xl text-sm md:text-base">
              Chat-based onboarding agent with personalized checklists, grounded knowledge retrieval, and structured HR completion reporting.
            </p>
          </div>

          <div className="text-sm font-medium text-emerald-700 bg-emerald-50 px-4 py-2 rounded-full border border-emerald-200 self-start md:self-auto">
            Environment: Local Demo
          </div>
        </header>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 items-start">
          <div className="xl:col-span-1">
            <Checklist />
          </div>

          <div className="xl:col-span-2">
            <ChatInterface />
          </div>
        </div>
      </div>
    </main>
  );
}
