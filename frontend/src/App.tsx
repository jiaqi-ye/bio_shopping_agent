import { useEffect, useMemo, useState } from "react";
import Sidebar from "./components/Sidebar.tsx";
import ChatWindow from "./components/ChatWindow.tsx";
import InputBox from "./components/InputBox.tsx";
import LoginModal from "./components/LoginModal.tsx";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  isError?: boolean;
  sources?: SourceRef[];
  comparison?: ComparisonPayload;
};

type Conversation = {
  id: string;
  title: string;
  updatedAt: string;
  messages: Message[];
};

type SourceRef = {
  source?: string;
  url?: string;
  page?: number;
  section?: string;
  score?: number;
};


type ComparisonPayload = {
  comparison_mode: boolean;
  comparison_items: {
    strain: string;
    vendor: string;
    price?: string | null;
    mutation_gene?: string | null;
    key_use?: string | null;
  }[];
  comparison_fields: string[];
};

type UserProfile = {
  user_id: string;
  username: string;
  shipping_address: string;
  current_mouse_count: number;
  cage_capacity: number;
};

type ChatResponsePayload = {
  reply?: string;
  message?: string;
  detail?: string;
  content?: string;
  email?: string;
  data?: { email?: string };
  sources?: SourceRef[];
  comparison?: ComparisonPayload;
};

const createConversation = (): Conversation => {
  const now = new Date().toISOString();
  return {
    id: `conv-${Date.now()}`,
    title: "New chat",
    updatedAt: now,
    messages: []
  };
};

const initialConversations: Conversation[] = [createConversation()];

export default function App() {
  const [conversations, setConversations] = useState<Conversation[]>(initialConversations);
  const [activeId, setActiveId] = useState<string>(initialConversations[0]?.id ?? "");
  const [draft, setDraft] = useState<string>("");
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [showLogin, setShowLogin] = useState<boolean>(false);
  const [isSending, setIsSending] = useState<boolean>(false);

  const apiBase = (import.meta.env.VITE_API_BASE ?? "").replace(/\/$/, "");
  const apiUrl = apiBase ? `${apiBase}/api/chat` : "/api/chat";
  const loginUrl = apiBase ? `${apiBase}/api/login` : "/api/login";
  const profileUrl = apiBase ? `${apiBase}/api/profile` : "/api/profile";
  const sessionIdKey = "lab_user_id";

  useEffect(() => {
    const existing = window.localStorage.getItem(sessionIdKey);
    if (!existing) {
      setShowLogin(true);
      return;
    }
    fetch(`${profileUrl}/${existing}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((payload) => {
        if (!payload) {
          setShowLogin(true);
          return;
        }
        setUserProfile(payload as UserProfile);
        setShowLogin(false);
      })
      .catch(() => {
        setShowLogin(true);
      });
  }, [profileUrl]);

  const sortedConversations = useMemo(() => {
    return [...conversations].sort(
      (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
    );
  }, [conversations]);

  const activeConversation = conversations.find((conversation) => conversation.id === activeId);

  const updateConversation = (id: string, updater: (conversation: Conversation) => Conversation) => {
    setConversations((prev) =>
      prev.map((conversation) =>
        conversation.id === id ? updater(conversation) : conversation
      )
    );
  };

  const handleNewChat = () => {
    const fresh = createConversation();
    setConversations((prev) => [fresh, ...prev]);
    setActiveId(fresh.id);
    setDraft("");
  };

  const handleRename = (id: string) => {
    const target = conversations.find((conversation) => conversation.id === id);
    const nextName = window.prompt("Rename conversation", target?.title ?? "New chat");
    if (!nextName) return;
    updateConversation(id, (conversation) => ({
      ...conversation,
      title: nextName.trim() || conversation.title
    }));
  };

  const handleDelete = (id: string) => {
    const confirmed = window.confirm("Delete this conversation?");
    if (!confirmed) return;
    setConversations((prev) => prev.filter((conversation) => conversation.id !== id));
    if (activeId === id) {
      const next = conversations.find((conversation) => conversation.id !== id);
      setActiveId(next?.id ?? "");
    }
  };

  const appendMessage = (id: string, message: Message) => {
    updateConversation(id, (conversation) => {
      const title =
        conversation.title === "New chat" && message.role === "user"
          ? message.content.slice(0, 40)
          : conversation.title;
      return {
        ...conversation,
        title,
        updatedAt: new Date().toISOString(),
        messages: [...conversation.messages, message]
      };
    });
  };

  const handleQuickAction = (value: string) => {
    setDraft(value);
  };


  const handleLogin = async (payload: Omit<UserProfile, "user_id">) => {
    const response = await fetch(loginUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!response.ok) {
      throw new Error("Login failed");
    }
    const data = (await response.json()) as UserProfile;
    window.localStorage.setItem(sessionIdKey, data.user_id);
    setUserProfile(data);
    setShowLogin(false);
  };

  const handleSend = async () => {
    const trimmed = draft.trim();
    if (!trimmed || isSending) return;

    let conversationId = activeId;
    if (!conversationId) {
      const fresh = createConversation();
      setConversations((prev) => [fresh, ...prev]);
      conversationId = fresh.id;
      setActiveId(fresh.id);
    }

    setDraft("");
    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: "user",
      content: trimmed
    };
    appendMessage(conversationId, userMessage);

    setIsSending(true);
    try {
      const response = await fetch(apiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: trimmed, conversation_id: conversationId, user_id: userProfile?.user_id })
      });

      let payload: ChatResponsePayload | null = null;
      try {
        payload = await response.json();
      } catch (error) {
        payload = null;
      }

      if (!response.ok) {
        const detail = payload?.message || payload?.detail || `Request failed (${response.status})`;
        throw new Error(detail);
      }

      const reply = payload?.message || payload?.reply || payload?.content || "No response returned.";
      const emailText = payload?.email || payload?.data?.email;
      const email = emailText ? `\n\nOrder email draft:\n${emailText}` : "";

      appendMessage(conversationId, {
        id: `msg-${Date.now()}-assistant`,
        role: "assistant",
        content: `${reply}${email}`,
        sources: payload?.sources,
        comparison: payload?.data?.comparison_mode
          ? {
              comparison_mode: true,
              comparison_items: payload?.data?.comparison_items ?? [],
              comparison_fields: payload?.data?.comparison_fields ?? []
            }
          : undefined
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unexpected error";
      appendMessage(conversationId, {
        id: `msg-${Date.now()}-error`,
        role: "assistant",
        content: `Sorry, I could not reach the chat service. ${message}`,
        isError: true
      });
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <div className="flex h-screen">
        <LoginModal open={showLogin} onSubmit={handleLogin} />
        <Sidebar
          conversations={sortedConversations}
          activeId={activeId}
          onSelect={setActiveId}
          onNewChat={handleNewChat}
          onRename={handleRename}
          onDelete={handleDelete}
        />

        <main className="flex-1 flex flex-col bg-slate-100">
          <div className="flex-1 overflow-hidden">
            <ChatWindow conversation={activeConversation} isSending={isSending} onQuickAction={handleQuickAction} userProfile={userProfile} />
          </div>
          <InputBox
            value={draft}
            onChange={setDraft}
            onSend={handleSend}
            disabled={isSending || !userProfile}
          />
        </main>
      </div>
    </div>
  );
}
