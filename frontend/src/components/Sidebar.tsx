import logoUrl from "../assets/logo.svg";

type Conversation = {
  id: string;
  title: string;
  updatedAt: string;
  messages: { content: string }[];
};

type SidebarProps = {
  conversations: Conversation[];
  activeId: string;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onRename: (id: string) => void;
  onDelete: (id: string) => void;
};

export default function Sidebar({
  conversations,
  activeId,
  onSelect,
  onNewChat,
  onRename,
  onDelete
}: SidebarProps) {
  return (
    <aside className="w-[260px] border-r border-slate-200 bg-white h-full flex flex-col">
      <div className="p-4 border-b border-slate-200">
        <div className="mb-4 flex items-center gap-3">
          <img src={logoUrl} alt="BioShopping Agent" className="h-12 w-12" />
          <div>
            <p className="text-sm font-semibold text-slate-900">BioShopping Agent</p>
            <p className="text-xs text-slate-500">Lab Procurement</p>
          </div>
        </div>
        <button
          type="button"
          onClick={onNewChat}
          className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-white"
        >
          + New chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-2">
        {conversations.map((conversation) => {
          const isActive = conversation.id === activeId;
          return (
            <div
              key={conversation.id}
              className={`group rounded-xl border px-3 py-2 transition ${
                isActive
                  ? "border-slate-300 bg-slate-50"
                  : "border-transparent hover:border-slate-200 hover:bg-slate-50"
              }`}
            >
              <button
                type="button"
                onClick={() => onSelect(conversation.id)}
                className="w-full text-left"
              >
                <p className="text-sm font-semibold text-slate-800 truncate">
                  {conversation.title}
                </p>
                <p className="text-xs text-slate-500 truncate">
                  {conversation.messages.at(-1)?.content || "No messages yet"}
                </p>
              </button>
              <div className="mt-2 flex items-center gap-2 opacity-0 transition group-hover:opacity-100">
                <button
                  type="button"
                  onClick={() => onRename(conversation.id)}
                  className="text-xs text-slate-500 hover:text-slate-800"
                >
                  Rename
                </button>
                <span className="text-slate-300">|</span>
                <button
                  type="button"
                  onClick={() => onDelete(conversation.id)}
                  className="text-xs text-rose-500 hover:text-rose-600"
                >
                  Delete
                </button>
              </div>
            </div>
          );
        })}
      </div>

      <div className="border-t border-slate-200 p-4 text-xs text-slate-500">
        AI Procurement Assistant
      </div>
    </aside>
  );
}
