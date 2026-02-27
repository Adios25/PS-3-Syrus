import { create } from 'zustand';

const AGENT_BASE_URL = process.env.NEXT_PUBLIC_AGENT_URL || 'http://localhost:8001';

export interface SourceReference {
  source_id: string;
  title: string;
  section: string;
}

export interface Message {
  id: string;
  sender: 'user' | 'agent';
  content: string;
  timestamp: Date;
  sources?: SourceReference[];
}

export interface ChecklistItem {
  item_id: number;
  title: string;
  description: string;
  category: string;
  source_refs: string[];
  is_completed: boolean;
}

export interface Profile {
  name: string | null;
  email: string | null;
  team: string | null;
  role: string | null;
  experience_level: string | null;
  tech_stack: string[];
}

export interface CompletionEmailPayload {
  to: string;
  subject: string;
  employee: {
    name: string | null;
    email: string | null;
    role: string | null;
    team: string | null;
    experience_level: string | null;
    tech_stack: string[];
  };
  summary: {
    status: string;
    completed_items: string[];
    pending_items: string[];
    completion_timestamp_utc: string;
  };
  confidence_score: number;
}

interface AppState {
  sessionId: string | null;
  status: 'in_progress' | 'completed';
  profile: Profile;
  messages: Message[];
  checklist: ChecklistItem[];
  progressPercent: number;
  missingProfileFields: string[];
  completionEmail: CompletionEmailPayload | null;
  isTyping: boolean;
  isLoadingChecklist: boolean;
  error: string | null;
  sendMessage: (input: string) => Promise<void>;
  toggleChecklistItem: (itemId: number) => Promise<void>;
  finalizeOnboarding: () => Promise<void>;
}

async function readJson(response: Response) {
  const data = await response.json();
  if (!response.ok) {
    const detail = typeof data?.detail === 'string' ? data.detail : 'Request failed';
    throw new Error(detail);
  }
  return data;
}

function buildSourceFooter(sources: SourceReference[] | undefined): string {
  if (!sources?.length) {
    return '';
  }
  const formatted = sources.map((source) => `${source.source_id}`).join(', ');
  return `\n\nSources: ${formatted}`;
}

const defaultProfile: Profile = {
  name: null,
  email: null,
  team: null,
  role: null,
  experience_level: null,
  tech_stack: [],
};

export const useStore = create<AppState>((set, get) => ({
  sessionId: null,
  status: 'in_progress',
  profile: defaultProfile,
  messages: [
    {
      id: 'welcome',
      sender: 'agent',
      content:
        "Welcome to PS-03 onboarding. Start by telling me your name, role (Backend/Frontend/DevOps), experience level (Intern/Junior/Senior), and primary tech stack.",
      timestamp: new Date(),
    },
  ],
  checklist: [],
  progressPercent: 0,
  missingProfileFields: ['name', 'role', 'experience_level', 'tech_stack'],
  completionEmail: null,
  isTyping: false,
  isLoadingChecklist: false,
  error: null,

  sendMessage: async (input: string) => {
    const trimmed = input.trim();
    if (!trimmed) {
      return;
    }

    const userMessage: Message = {
      id: `u-${Date.now()}`,
      sender: 'user',
      content: trimmed,
      timestamp: new Date(),
    };

    set((state) => ({
      messages: [...state.messages, userMessage],
      isTyping: true,
      error: null,
    }));

    try {
      const response = await fetch(`${AGENT_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: trimmed,
          session_id: get().sessionId,
        }),
      });
      const data = await readJson(response);

      const agentMessage: Message = {
        id: `a-${Date.now()}`,
        sender: 'agent',
        content: `${data.message}${buildSourceFooter(data.sources)}`,
        timestamp: new Date(),
        sources: data.sources,
      };

      set((state) => ({
        sessionId: data.session_id,
        status: data.status,
        profile: data.profile ?? state.profile,
        checklist: data.checklist ?? state.checklist,
        progressPercent: data.progress_percent ?? state.progressPercent,
        missingProfileFields: data.missing_profile_fields ?? state.missingProfileFields,
        completionEmail: data.completion_email ?? state.completionEmail,
        isTyping: false,
        messages: [...state.messages, agentMessage],
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to contact onboarding agent';
      set((state) => ({
        isTyping: false,
        error: message,
        messages: [
          ...state.messages,
          {
            id: `e-${Date.now()}`,
            sender: 'agent',
            content: `I hit an error: ${message}`,
            timestamp: new Date(),
          },
        ],
      }));
    }
  },

  toggleChecklistItem: async (itemId: number) => {
    const state = get();
    if (!state.sessionId) {
      set({ error: 'Start onboarding in chat before updating checklist items.' });
      return;
    }

    const target = state.checklist.find((item) => item.item_id === itemId);
    if (!target) {
      set({ error: `Checklist item ${itemId} was not found.` });
      return;
    }

    set({ isLoadingChecklist: true, error: null });

    try {
      const response = await fetch(
        `${AGENT_BASE_URL}/onboarding/session/${state.sessionId}/checklist/${itemId}`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ is_completed: !target.is_completed }),
        },
      );
      const data = await readJson(response);
      set((current) => ({
        checklist: data.checklist ?? current.checklist,
        progressPercent: data.progress_percent ?? current.progressPercent,
        status: data.status ?? current.status,
        isLoadingChecklist: false,
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to update checklist item';
      set({ isLoadingChecklist: false, error: message });
    }
  },

  finalizeOnboarding: async () => {
    const state = get();
    if (!state.sessionId) {
      set({ error: 'Start onboarding in chat before finalizing.' });
      return;
    }

    set({ error: null, isTyping: true });

    try {
      const response = await fetch(`${AGENT_BASE_URL}/onboarding/session/${state.sessionId}/complete`, {
        method: 'POST',
      });
      const data = await readJson(response);

      set((current) => ({
        status: 'completed',
        completionEmail: data.completion_email,
        isTyping: false,
        messages: [
          ...current.messages,
          {
            id: `done-${Date.now()}`,
            sender: 'agent',
            content: 'Onboarding completed and HR notification generated successfully.',
            timestamp: new Date(),
          },
        ],
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to finalize onboarding';
      set({ isTyping: false, error: message });
    }
  },
}));
