import { useEffect, useMemo, useRef } from "react";
import MessageBubble from "./MessageBubble.tsx";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  isError?: boolean;
  sources?: { source?: string; url?: string; page?: number }[];
};

type Conversation = {
  id: string;
  title: string;
  updatedAt: string;
  messages: Message[];
};

type ChatWindowProps = {
  conversation?: Conversation;
  isSending: boolean;
  onQuickAction?: (value: string) => void;
  userProfile?: { username: string };
};

export default function ChatWindow({ conversation, isSending, onQuickAction, userProfile }: ChatWindowProps) {
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversation?.messages?.length, isSending]);

  const header = useMemo(() => {
    if (!conversation) return { title: "Select a chat", subtitle: "" };
    const lastUpdated = conversation.updatedAt
      ? new Date(conversation.updatedAt).toLocaleString()
      : "";
    return {
      title: conversation.title,
      subtitle: lastUpdated ? `Updated ${lastUpdated}` : ""
    };
  }, [conversation]);

  return (
    <section className="h-full flex flex-col">
      <div className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-3xl px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-slate-900">{header.title}</h1>
            {header.subtitle ? (
              <p className="text-xs text-slate-500">{header.subtitle}</p>
            ) : null}
          </div>
          {userProfile?.username ? (
            <div className="h-9 w-9 rounded-full bg-slate-900 text-white text-xs font-semibold flex items-center justify-center">
              {userProfile.username.slice(0, 2).toUpperCase()}
            </div>
          ) : null}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl px-6 py-8 space-y-6">
          {!conversation && (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-6 py-10 text-center">
              <p className="text-sm text-slate-500">
                Pick a conversation on the left or start a new chat.
              </p>
            </div>
          )}
          {conversation && conversation.messages.length === 0 && (
            <div className="rounded-2xl border border-slate-200 bg-white px-6 py-8 space-y-4">
              <div>
                <p className="text-sm font-semibold text-slate-800">Welcome to the Lab Procurement Assistant</p>
                <p className="text-sm text-slate-500">
                  I can help you compare mouse strains and antibodies, draft RFQs, and plan sourcing with lead times and budgets.
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                {[
                  { label: "Common lab mice", value: "Show common lab mice options." },
                  { label: "Vendor-exclusive mice", value: "Compare vendor-exclusive mouse strains." },
                  { label: "RFQ / order email template", value: "Draft an RFQ/order email template for mice." },
                  { label: "Beginner guidance on mouse selection", value: "Provide beginner guidance on mouse strain selection." },
                ].map((option) => (
                  <button
                    key={option.label}
                    type="button"
                    onClick={() => onQuickAction?.(option.value)}
                    className="rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100"
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {conversation?.messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}

          {isSending && (
            <div className="flex justify-start">
              <div className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm text-slate-500">
                Thinking...
              </div>
            </div>
          )}
          <div ref={endRef} />
        </div>
      </div>
    </section>
  );
}
