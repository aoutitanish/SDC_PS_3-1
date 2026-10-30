import React, { useState } from 'react';
import { useChat } from '../../contexts/ChatContext';
import {
  MessageSquare,
  Plus,
  Trash2,
  Search,
  ChevronLeft,
  ChevronRight,
  History,
  Clock,
  Sparkles,
  Sprout
} from 'lucide-react';

interface ChatHistorySidebarProps {
  isOpen: boolean;
  onToggle: () => void;
}

export const ChatHistorySidebar: React.FC<ChatHistorySidebarProps> = ({
  isOpen,
  onToggle
}) => {
  const {
    sessions,
    activeSessionId,
    switchSession,
    deleteSession,
    startNewSession
  } = useChat();

  const [searchQuery, setSearchQuery] = useState('');

  const filteredSessions = sessions.filter(
    (s) =>
      s.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (s.lastMessageSnippet && s.lastMessageSnippet.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  if (!isOpen) {
    return (
      <button
        type="button"
        onClick={onToggle}
        className="fixed left-4 top-24 z-30 p-3 rounded-2xl bg-white/95 backdrop-blur border border-[#D0E5DA] shadow-depth text-[#0F281E] hover:text-[#059669] transition hover:scale-105 flex items-center gap-2 font-display text-xs font-bold"
        title="Open Chat History"
        aria-label="Open Chat History"
      >
        <History className="w-4 h-4 text-[#059669]" />
        <span className="hidden sm:inline">History</span>
        <ChevronRight className="w-3.5 h-3.5 text-[#526B60]" />
      </button>
    );
  }

  return (
    <aside className="w-full lg:w-72 shrink-0 bg-white rounded-3xl border border-[#E2ECE6] shadow-panel overflow-hidden flex flex-col transition-all duration-300 h-full max-h-[80vh]">
      
      {/* Header Bar */}
      <div className="p-4 bg-[#F8FAF9] border-b border-[#E2ECE6] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-[#E8F5EF] text-[#059669] flex items-center justify-center">
            <History className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-extrabold text-sm text-[#0F281E] font-display">
              Consultation History
            </h3>
            <span className="text-[10px] text-[#526B60] font-medium font-sans">
              {sessions.length} saved session{sessions.length === 1 ? '' : 's'}
            </span>
          </div>
        </div>

        <button
          type="button"
          onClick={onToggle}
          className="p-1.5 rounded-xl text-[#526B60] hover:text-[#0F281E] hover:bg-white transition"
          title="Collapse Sidebar"
          aria-label="Collapse History Sidebar"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
      </div>

      {/* Action: New Consultation Button */}
      <div className="p-3 border-b border-[#E2ECE6] bg-white">
        <button
          type="button"
          onClick={startNewSession}
          className="w-full py-2.5 px-4 rounded-2xl bg-[#059669] hover:bg-[#047857] text-white text-xs font-bold font-display shadow-sm shadow-[#059669]/25 transition hover:scale-[1.02] flex items-center justify-center gap-2"
        >
          <Plus className="w-4 h-4" />
          <span>New Consultation</span>
        </button>
      </div>

      {/* Search Bar */}
      <div className="p-3 border-b border-[#E2ECE6] bg-[#F8FAF9]">
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-[#526B60]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search past questions..."
            className="w-full pl-8 pr-3 py-1.5 rounded-xl bg-white border border-[#D0E5DA] text-xs text-[#0F281E] placeholder-[#526B60] focus:border-[#059669] focus:outline-none font-sans"
          />
        </div>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
        {filteredSessions.length > 0 ? (
          filteredSessions.map((session) => {
            const isActive = session.id === activeSessionId;
            return (
              <div
                key={session.id}
                onClick={() => switchSession(session.id)}
                className={`group relative p-3 rounded-2xl border transition-all cursor-pointer flex flex-col gap-1 ${
                  isActive
                    ? 'bg-[#F0FDF4] border-[#86EFAC] shadow-sm'
                    : 'bg-white hover:bg-[#F8FAF9] border-transparent hover:border-[#E2ECE6]'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-1.5 min-w-0">
                    <MessageSquare
                      className={`w-3.5 h-3.5 shrink-0 ${
                        isActive ? 'text-[#059669]' : 'text-[#526B60]'
                      }`}
                    />
                    <span
                      className={`text-xs font-bold truncate font-display ${
                        isActive ? 'text-[#0F281E]' : 'text-[#526B60]'
                      }`}
                    >
                      {session.title}
                    </span>
                  </div>

                  {/* Delete Button */}
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteSession(session.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 rounded-lg text-[#526B60] hover:text-rose-600 hover:bg-rose-50 transition shrink-0"
                    title="Delete Conversation"
                    aria-label="Delete Conversation"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>

                {/* Snippet preview */}
                {session.lastMessageSnippet && (
                  <p className="text-[11px] text-[#526B60] line-clamp-1 font-sans pl-5">
                    {session.lastMessageSnippet}
                  </p>
                )}

                {/* Footer details */}
                <div className="flex items-center justify-between pl-5 pt-0.5 text-[10px] text-[#526B60] font-medium">
                  <span className="flex items-center gap-1">
                    <Clock className="w-2.5 h-2.5" />
                    <span>{session.date}</span>
                  </span>
                  {isActive && (
                    <span className="text-[9px] font-extrabold px-1.5 py-0.2 rounded-md bg-[#DCFCE7] text-[#059669] font-display">
                      Active
                    </span>
                  )}
                </div>
              </div>
            );
          })
        ) : (
          <div className="p-6 text-center text-xs text-[#526B60] font-sans space-y-1">
            <p>No conversations found.</p>
            <p className="text-[10px]">Start a new consultation above.</p>
          </div>
        )}
      </div>

    </aside>
  );
};
