import React, { useState } from 'react';
import { ChatMessage as ChatMessageType } from '../../types';
import { Sprout, User, Copy, Check, BookOpen, Sparkles, Loader2, CheckCircle2, BarChart3, Volume2 } from 'lucide-react';
import { SpeechAudioPlayer } from './SpeechAudioPlayer';
import { SourcesModal } from './SourcesModal';
import { AgronomicDetailsDrawer } from '../modals/AgronomicDetailsDrawer';
import { StructuredResponseRenderer } from './StructuredResponseRenderer';
import { CropSummary } from '../../data/dashboardMock';

interface ChatMessageProps {
  message: ChatMessageType;
  onSelectCrop?: (crop: CropSummary | string) => void;
  onExplainScore?: (cropName: string, score: number, conf: string) => void;
  onQuickReply?: (reply: string) => void;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  onSelectCrop,
  onExplainScore,
  onQuickReply
}) => {
  const [copied, setCopied] = useState(false);
  const [isSourcesOpen, setIsSourcesOpen] = useState(false);
  const [isAnalysisOpen, setIsAnalysisOpen] = useState(false);
  const isUser = message.sender === 'user';

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Determine if this is a recommendation or analytical answer that has detailed analysis
  const hasAnalysisData =
    message.detailed_analysis ||
    message.recommendation_data ||
    message.content.includes('Crop Recommendation') ||
    message.content.includes('పంట సిఫార్సు') ||
    message.content.includes('फसल सिफारिश') ||
    message.content.includes('Explanation') ||
    message.content.includes('Comparison');

  return (
    <div className={`flex items-start gap-3 my-4 ${isUser ? 'flex-row-reverse' : 'flex-row'} animate-in fade-in`}>
      
      {/* Avatar Icon */}
      <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-sm ${
        isUser
          ? 'bg-[#0F281E] text-white'
          : 'bg-[#00A859] text-white shadow-md'
      }`}>
        {isUser ? <User className="w-4 h-4" /> : <Sprout className="w-4 h-4" />}
      </div>

      {/* Message Bubble Container */}
      <div className="w-full max-w-[92%] sm:max-w-[85%] space-y-2">
        
        <div className={`p-4 sm:p-5 rounded-3xl border shadow-sm ${
          isUser
            ? 'bg-[#E8F5EF] text-[#0F281E] border-[#00A859]/40 rounded-tr-none'
            : 'bg-white text-[#0F281E] border-[#E2ECE6] rounded-tl-none'
        }`}>
          
          {/* Header row for assistant message */}
          {!isUser && (
            <div className="flex items-center justify-between gap-2 mb-3 pb-2.5 border-b border-[#E2ECE6] text-xs">
              <div className="flex items-center gap-2">
                <span className="font-bold text-[#059669] flex items-center gap-1.5 font-display">
                  <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                  <span>KrishiMitra Agricultural Assistant</span>
                </span>
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#E8F5EF] text-[#059669] border border-[#059669]/30 font-display">
                  <BookOpen className="w-3 h-3" />
                  <span>Dynamic RAG</span>
                </span>
              </div>
              <span className="text-[11px] text-[#526B60] font-medium">{message.timestamp}</span>
            </div>
          )}

          {/* User Text or Structured Assistant Response */}
          <div>
            {isUser ? (
              <p className="text-sm font-semibold text-[#0F281E] leading-relaxed">
                {message.content}
              </p>
            ) : message.content ? (
              <StructuredResponseRenderer
                content={message.content}
                onSelectCrop={onSelectCrop}
                onExplainScore={onExplainScore}
                onOpenSources={() => setIsSourcesOpen(true)}
                onOpenFullAnalysis={() => setIsAnalysisOpen(true)}
              />
            ) : (
              message.isStreaming && (
                <div className="flex items-center gap-2 text-xs text-[#526B60] py-2">
                  <Loader2 className="w-4 h-4 animate-spin text-[#059669]" />
                  <span>KrishiMitra is reasoning through soil, weather, and crop data...</span>
                </div>
              )
            )}
          </div>

          {/* Adaptive Follow-up Question & Contextual Quick-Reply Chips */}
          {!isUser && !message.isStreaming && (message.follow_up || (message.quick_replies && message.quick_replies.length > 0)) && (
            <div className="mt-3.5 pt-3 border-t border-[#E2ECE6] space-y-2">
              {message.follow_up && (
                <div className="flex items-center gap-2 text-xs font-semibold text-[#065F46] bg-[#ECFDF5] px-3.5 py-2 rounded-2xl border border-[#A7F3D0]">
                  <Sparkles className="w-3.5 h-3.5 text-[#059669] shrink-0" />
                  <span>{message.follow_up}</span>
                </div>
              )}
              {message.quick_replies && message.quick_replies.length > 0 && (
                <div className="flex flex-wrap items-center gap-1.5 pt-1">
                  {message.quick_replies.map((chip, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => onQuickReply && onQuickReply(chip)}
                      className="px-3 py-1 rounded-full text-xs font-semibold bg-[#F0FDF4] text-[#15803D] border border-[#86EFAC] hover:bg-[#15803D] hover:text-white transition shadow-sm active:scale-95 cursor-pointer"
                    >
                      {chip}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Assistant Action Bar: [🔊 Listen] [📊 Full Analysis] [📚 Sources] */}
          {!isUser && message.content && (
            <div className="mt-3 pt-2.5 border-t border-[#E2ECE6] flex flex-wrap items-center justify-between gap-2">
              <div className="flex flex-wrap items-center gap-2">
                {/* 1. Listen Aloud */}
                <SpeechAudioPlayer text={message.content} language={message.language} />

                {/* 2. Full Analysis Button */}
                {hasAnalysisData && (
                  <button
                    type="button"
                    onClick={() => setIsAnalysisOpen(true)}
                    className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#E8F5EF] text-[#00A859] border border-[#00A859]/30 hover:bg-[#00A859] hover:text-white transition shadow-sm"
                  >
                    <BarChart3 className="w-3.5 h-3.5" />
                    <span>View Full Analysis</span>
                  </button>
                )}

                {/* 3. Sources */}
                <button
                  type="button"
                  onClick={() => setIsSourcesOpen(true)}
                  className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-[#F0F7F3] text-[#0F281E] border border-[#D0E5DA] hover:text-[#00A859] hover:border-[#00A859] transition"
                >
                  <BookOpen className="w-3 h-3 text-[#00A859]" />
                  <span>Sources ({message.sources?.length ?? 0})</span>
                </button>
              </div>

              {/* Copy button */}
              <button
                type="button"
                onClick={handleCopy}
                className="p-1.5 rounded-lg text-[#526B60] hover:text-[#0F281E] hover:bg-[#F0F7F3] transition ml-auto"
                title="Copy response text"
                aria-label="Copy response"
              >
                {copied ? <Check className="w-4 h-4 text-[#00A859]" /> : <Copy className="w-4 h-4" />}
              </button>
            </div>
          )}

        </div>

      </div>

      {/* Level 2 Scientific Analysis Drawer */}
      <AgronomicDetailsDrawer
        isOpen={isAnalysisOpen}
        onClose={() => setIsAnalysisOpen(false)}
        analysis={message.detailed_analysis || null}
        cropName={message.simple_summary?.main_crop || (message.recommendation_data?.primary_recommendation?.crop as string) || 'Arhar/Tur (Pigeon Pea)'}
      />

      {/* Sources Citations Modal */}
      <SourcesModal
        isOpen={isSourcesOpen}
        onClose={() => setIsSourcesOpen(false)}
        sources={message.sources || []}
      />

    </div>
  );
};
