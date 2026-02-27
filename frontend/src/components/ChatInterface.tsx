"use client";

import React, { useState, useRef, useEffect } from 'react';
import { AlertCircle, Bot, Send } from 'lucide-react';
import { useStore } from '../store/useStore';

const quickPrompts = [
  'My name is Alex Carter. I am a backend junior working with Python.',
  'Show my checklist status.',
  'How do I set up the local environment?',
  'Mark task #1 done',
  'Finish onboarding',
];

export default function ChatInterface() {
  const { messages, sendMessage, isTyping, error, missingProfileFields, status } = useStore();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

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
    <div className="flex flex-col h-[680px] border border-slate-200 rounded-2xl bg-white shadow-sm overflow-hidden">
      <div className="bg-slate-900 p-4 text-white flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Bot size={22} />
          <div>
            <h2 className="font-semibold text-lg">PS-03 Onboarding Agent</h2>
            <p className="text-slate-300 text-xs">Chat-driven onboarding with source-grounded answers</p>
          </div>
        </div>
        <div className="text-xs uppercase tracking-wide text-slate-200">
          {status === 'completed' ? 'Completed' : 'In Progress'}
        </div>
      </div>

      <div className="px-4 py-3 border-b border-slate-200 bg-slate-50">
        <div className="flex flex-wrap gap-2">
          {quickPrompts.map((prompt) => (
            <button
              key={prompt}
              type="button"
              onClick={() => setInput(prompt)}
              className="text-xs px-3 py-1.5 rounded-full border border-slate-300 hover:border-slate-500 hover:bg-white transition"
            >
              {prompt.length > 42 ? `${prompt.slice(0, 42)}...` : prompt}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/40">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                msg.sender === 'user'
                  ? 'bg-sky-600 text-white rounded-br-none'
                  : 'bg-white text-slate-800 border border-slate-200 shadow-sm rounded-bl-none'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-white border border-slate-200 text-slate-400 rounded-2xl px-4 py-2 text-sm shadow-sm rounded-bl-none">
              Agent is thinking...
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="px-4 py-2 border-t border-slate-200 bg-white text-xs text-slate-500">
        Missing onboarding profile fields: {missingProfileFields.length ? missingProfileFields.join(', ') : 'none'}
      </div>

      {error && (
        <div className="px-4 py-2 border-t border-rose-200 bg-rose-50 text-rose-700 text-sm flex items-center gap-2">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={submit} className="p-3 border-t bg-white flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask onboarding questions or share your profile details..."
          className="flex-1 px-4 py-2 border border-slate-300 rounded-full focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent"
        />
        <button
          type="submit"
          disabled={!input.trim() || isTyping}
          className="bg-sky-600 text-white p-2 rounded-full hover:bg-sky-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Send size={20} />
        </button>
      </form>
    </div>
  );
}
