import React, { createContext, useContext, useState, useEffect } from 'react';
import { ChatMessage, LanguageCode, LocationData, RecommendationResponse } from '../types';
import { api } from '../services/api';
import { useLanguage } from './LanguageContext';
import { useFarm } from './FarmContext';
import { speechAudioController } from '../utils/speech';

export interface ChatSession {
  id: string;
  title: string;
  date: string;
  lastMessageSnippet?: string;
  messageCount?: number;
}

interface ChatContextType {
  messages: ChatMessage[];
  isStreaming: boolean;
  activeSessionId: string;
  sendMessage: (text: string, imageBase64?: string) => Promise<void>;
  clearChat: () => void;
  startNewSession: () => void;
  switchSession: (sessionId: string) => void;
  deleteSession: (sessionId: string) => void;
  sessions: ChatSession[];
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { language } = useLanguage();
  const { farm } = useFarm();

  const [activeSessionId, setActiveSessionId] = useState<string>(() => {
    return localStorage.getItem('krishi_active_session_id') || ('session_' + Date.now());
  });

  const getWelcomeMessage = (lang: LanguageCode): ChatMessage => ({
    id: 'welcome_' + Date.now(),
    sender: 'assistant',
    content: lang === 'te'
      ? "నమస్కారం! నేను కృషిమిత్ర AI, మీ వ్యవసాయ సహాయకుడిని. పంట సిఫార్సులు, నేల విశ్లేషణ, వాతావరణం, లేదా తెగుళ్ళ నివారణ గురించి ఏదైనా అడగండి."
      : lang === 'hi'
      ? "नमस्ते! मैं कृषिमित्र AI, आपका कृषि सहायक हूँ। फसल सिफारिश, मिट्टी परीक्षण, मौसम या कीट प्रबंधन के बारे में कोई भी प्रश्न पूछें।"
      : "Namaste! I am KrishiMitra AI, your intelligent farming assistant. Ask me anything about crop recommendations, soil health, weather advisories, irrigation, or agricultural schemes.",
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    language: lang,
    sources: []
  });

  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    const saved = localStorage.getItem('krishi_chat_' + activeSessionId);
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        console.error(e);
      }
    }
    return [getWelcomeMessage(language)];
  });

  const [isStreaming, setIsStreaming] = useState(false);

  const [sessions, setSessions] = useState<ChatSession[]>(() => {
    const saved = localStorage.getItem('krishi_chat_sessions');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        console.error(e);
      }
    }
    return [
      {
        id: activeSessionId,
        title: 'Crop & Soil Advisory',
        date: 'Today',
        lastMessageSnippet: 'Welcome to KrishiMitra AI',
        messageCount: 1
      }
    ];
  });

  // Persist active session id
  useEffect(() => {
    localStorage.setItem('krishi_active_session_id', activeSessionId);
  }, [activeSessionId]);

  // Persist messages for active session
  useEffect(() => {
    localStorage.setItem('krishi_chat_' + activeSessionId, JSON.stringify(messages));
    
    // Update session message count & snippet
    setSessions((prev) =>
      prev.map((s) => {
        if (s.id === activeSessionId) {
          const lastUser = messages.filter(m => m.sender === 'user').slice(-1)[0];
          return {
            ...s,
            messageCount: messages.length,
            lastMessageSnippet: lastUser ? lastUser.content.slice(0, 45) + '...' : s.lastMessageSnippet
          };
        }
        return s;
      })
    );
  }, [messages, activeSessionId]);

  // Persist sessions list
  useEffect(() => {
    localStorage.setItem('krishi_chat_sessions', JSON.stringify(sessions));
  }, [sessions]);

  const switchSession = (sessionId: string) => {
    if (sessionId === activeSessionId) return;
    setActiveSessionId(sessionId);
    const saved = localStorage.getItem('krishi_chat_' + sessionId);
    if (saved) {
      try {
        setMessages(JSON.parse(saved));
        return;
      } catch (e) {
        console.error(e);
      }
    }
    setMessages([getWelcomeMessage(language)]);
  };

  const deleteSession = (sessionId: string) => {
    localStorage.removeItem('krishi_chat_' + sessionId);
    api.clearChatHistory(sessionId).catch(console.error);
    const remaining = sessions.filter((s) => s.id !== sessionId);
    
    if (remaining.length === 0) {
      const newId = 'session_' + Date.now();
      const newSession: ChatSession = {
        id: newId,
        title: 'New Farming Conversation',
        date: 'Just now',
        messageCount: 1
      };
      setSessions([newSession]);
      setActiveSessionId(newId);
      setMessages([getWelcomeMessage(language)]);
    } else {
      setSessions(remaining);
      if (sessionId === activeSessionId) {
        switchSession(remaining[0].id);
      }
    }
  };

  const abortControllerRef = React.useRef<AbortController | null>(null);

  const startNewSession = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
    const newId = 'session_' + Date.now();
    const newSession: ChatSession = {
      id: newId,
      title: 'New Consultation',
      date: 'Just now',
      messageCount: 1
    };
    setSessions((prev) => [newSession, ...prev]);
    setActiveSessionId(newId);
    setMessages([getWelcomeMessage(language)]);
  };

  const clearChat = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
    api.clearChatHistory(activeSessionId).catch(console.error);
    const fresh = [getWelcomeMessage(language)];
    setMessages(fresh);
    localStorage.setItem('krishi_chat_' + activeSessionId, JSON.stringify(fresh));
  };

  const sendMessage = async (text: string, imageBase64?: string) => {
    if (!text.trim() && !imageBase64) return;

    // Immediately stop any active speech narration from previous answers
    speechAudioController.stop();

    // Cancel any previous in-flight request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    const userMsgId = 'msg_' + Date.now();
    const assistantMsgId = 'msg_' + (Date.now() + 1);
    const nowTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const userMsg: ChatMessage = {
      id: userMsgId,
      sender: 'user',
      content: text,
      timestamp: nowTime,
      language: language
    };

    const initialAssistantMsg: ChatMessage = {
      id: assistantMsgId,
      sender: 'assistant',
      content: '',
      timestamp: nowTime,
      language: language,
      isStreaming: true,
      sources: []
    };

    setMessages((prev) => [...prev, userMsg, initialAssistantMsg]);
    setIsStreaming(true);

    // Update session title on first meaningful user query
    setSessions((prev) =>
      prev.map((s) => {
        if (s.id === activeSessionId && (s.title === 'New Consultation' || s.title === 'New Farming Conversation' || s.title === 'Crop & Soil Advisory')) {
          return {
            ...s,
            title: text.length > 32 ? text.slice(0, 32) + '...' : text,
            lastMessageSnippet: text.slice(0, 45) + '...'
          };
        }
        return s;
      })
    );

    const detailLevel = localStorage.getItem('krishi_response_detail') || 'simple';
    let accumulatedContent = '';

    // Phase 5 Question-First: Do NOT automatically bundle saved farm profile or location into chat queries
    await api.streamChatMessage(
      text,
      language,
      undefined,
      undefined,
      activeSessionId,
      undefined,
      detailLevel,
      (token) => {
        accumulatedContent += token;
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId ? { ...m, content: accumulatedContent, isStreaming: true } : m
          )
        );
      },
      (meta) => {
        if (meta) {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMsgId
                ? {
                    ...m,
                    intent: meta.intent || m.intent,
                    confidence: meta.confidence || m.confidence,
                    sources: meta.sources || m.sources,
                    recommendation_data: meta.recommendation_data || m.recommendation_data,
                    comparison_data: meta.comparison_data || m.comparison_data,
                    simple_summary: meta.simple_summary || m.simple_summary,
                    detailed_analysis: meta.detailed_analysis || m.detailed_analysis,
                    follow_up: meta.follow_up || m.follow_up,
                    quick_replies: meta.quick_replies || m.quick_replies,
                    latency_metrics: meta.latency_metrics || m.latency_metrics
                  }
                : m
            )
          );
        }
      },
      () => {
        setIsStreaming(false);
        abortControllerRef.current = null;
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantMsgId ? { ...m, isStreaming: false } : m))
        );
      },
      (err) => {
        if (err?.name === 'AbortError') {
          return;
        }
        console.error('Chat stream error:', err);
        setIsStreaming(false);
        abortControllerRef.current = null;
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? {
                  ...m,
                  content: accumulatedContent || "Something went wrong while generating the answer. Please check your connection or retry.",
                  isStreaming: false
                }
              : m
          )
        );
      },
      controller.signal
    );
  };

  return (
    <ChatContext.Provider
      value={{
        messages,
        isStreaming,
        activeSessionId,
        sendMessage,
        clearChat,
        startNewSession,
        switchSession,
        deleteSession,
        sessions
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};
