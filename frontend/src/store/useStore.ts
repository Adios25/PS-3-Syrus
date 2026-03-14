import { create } from 'zustand';

const AGENT_BASE_URL = process.env.NEXT_PUBLIC_AGENT_URL || 'http://localhost:8001';

export interface SourceReference {
  source_id: string;
  title: string;
  section: string;
  source_file?: string;
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
  checklist_code?: string;
  title: string;
  description: string;
  category: string;
  owner?: string;
  deadline?: string;
  source_refs: string[];
  is_completed: boolean;
  completed_at?: string | null;
}

export interface Profile {
  name: string | null;
  email: string | null;
  team: string | null;
  role: string | null;
  experience_level: string | null;
  tech_stack: string[];
  employee_id?: string | null;
  department?: string | null;
  manager_name?: string | null;
  manager_email?: string | null;
  mentor_name?: string | null;
  mentor_email?: string | null;
  location?: string | null;
  start_date?: string | null;
  matched_persona_name?: string | null;
}

export interface CompletionEmailPayload {
  to: string[];
  cc: string[];
  from: string;
  subject: string;
  employee: {
    name: string | null;
    employee_id?: string | null;
    email: string | null;
    role: string | null;
    department?: string | null;
    team: string | null;
    manager_name?: string | null;
    manager_email?: string | null;
    mentor_name?: string | null;
    mentor_email?: string | null;
    start_date?: string | null;
    location?: string | null;
    tech_stack: string[];
  };
  summary: {
    status: string;
    completion_date: string;
    completion_timestamp_iso: string;
    total_duration_business_days: number;
  };
  checklist_summary: {
    total_tasks: number;
    completed_count: number;
    completed_percentage: number;
    skipped_count: number;
    pending_count: number;
  };
  completed_items: Array<{ code: string; title: string; completed_at?: string | null }>;
  pending_items: Array<{ code: string; title: string; reason: string }>;
  confidence_score: number;
  compliance_status?: Record<string, string>;
  access_provisioned?: Record<string, string>;
  first_task_status?: {
    ticket: string;
    status: string;
    pr_link: string;
  };
  source_template?: {
    document_id: string;
    template: string;
    template_loaded: boolean;
  };
  notes?: string;
  delivery_status?: string;
  report_id?: string;
  generated_at?: string;
}

export interface StarterTicket {
  ticket_id: string;
  title: string;
  project: string;
  issue_type: string;
  priority: string;
  story_points: string;
  repository: string;
  description: string;
  acceptance_criteria: string[];
  section: string;
}

export interface MCPAction {
  tool_name: string;
  status: string;
  payload: Record<string, string>;
}

export interface GeneratedFAQ {
  question: string;
  answer: string;
  source_ids: string[];
  created_at: string;
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
  completionEmailPreview: string | null;
  assignedTicket: StarterTicket | null;
  inferenceNotes: string[];
  mcpActions: MCPAction[];
  generatedFaqs: GeneratedFAQ[];
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

const defaultProfile: Profile = {
  name: null,
  email: null,
  team: null,
  role: null,
  experience_level: null,
  tech_stack: [],
  employee_id: null,
  department: null,
  manager_name: null,
  manager_email: null,
  mentor_name: null,
  mentor_email: null,
  location: null,
  start_date: null,
  matched_persona_name: null,
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
        "Welcome to ODA onboarding. Start by telling me your name, role (Backend/Frontend/DevOps), experience level (Intern/Junior/Senior), primary tech stack, and team/squad.",
      timestamp: new Date(),
    },
  ],
  checklist: [],
  progressPercent: 0,
  missingProfileFields: ['name', 'role', 'experience_level', 'tech_stack', 'team'],
  completionEmail: null,
  completionEmailPreview: null,
  assignedTicket: null,
  inferenceNotes: [],
  mcpActions: [],
  generatedFaqs: [],
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
        content: data.message,
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
        completionEmailPreview: data.email_preview ?? state.completionEmailPreview,
        assignedTicket: data.assigned_ticket ?? state.assignedTicket,
        inferenceNotes: data.inference_notes ?? state.inferenceNotes,
        mcpActions: data.mcp_actions ?? state.mcpActions,
        generatedFaqs: data.generated_faqs ?? state.generatedFaqs,
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
        assignedTicket: data.assigned_ticket ?? current.assignedTicket,
        inferenceNotes: data.inference_notes ?? current.inferenceNotes,
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
        completionEmailPreview: data.email_preview ?? current.completionEmailPreview,
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
