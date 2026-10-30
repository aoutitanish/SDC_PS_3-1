import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, X, Mic, Sparkles, Loader2 } from 'lucide-react';
import { VoiceInputButton } from './VoiceInputButton';

interface ChatComposerProps {
  onSendMessage: (text: string, imageBase64?: string) => void;
  isStreaming: boolean;
  onSelectPrompt?: (promptText: string) => void;
}

const SUGGESTED_PROMPTS = [
  'Which crop needs less water?',
  'Explain this score',
  'Show expected yield',
  'Check today’s weather',
  'Compare market risk'
];

export const ChatComposer: React.FC<ChatComposerProps> = ({
  onSendMessage,
  isStreaming,
  onSelectPrompt
}) => {
  const [inputText, setInputText] = useState('');
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isListening, setIsListening] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [inputText]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if ((!inputText.trim() && !imagePreview) || isStreaming) return;
    onSendMessage(inputText, imagePreview || undefined);
    setInputText('');
    setImagePreview(null);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        alert('Image exceeds 5MB limit. Please select a smaller photo.');
        return;
      }
      const reader = new FileReader();
      reader.onload = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <div className="border-t border-[#26374D] bg-[#0C1728]/95 backdrop-blur-md p-3 sm:p-4 space-y-2.5">
      
      {/* Suggested Prompt Chips */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 no-scrollbar">
        <span className="text-[10px] font-bold uppercase tracking-wider text-[#718197] shrink-0 flex items-center gap-1">
          <Sparkles className="w-3 h-3 text-[#08A873]" />
          <span>Suggestions:</span>
        </span>
        {SUGGESTED_PROMPTS.map((prompt, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => {
              if (onSelectPrompt) onSelectPrompt(prompt);
              else onSendMessage(prompt);
            }}
            disabled={isStreaming}
            className="px-3 py-1 rounded-full text-xs font-medium bg-[#111E31] hover:bg-[#17263A] text-[#A9B7C8] hover:text-[#F5F8FC] border border-[#26374D] hover:border-[#08A873] whitespace-nowrap transition disabled:opacity-40"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Voice Listening Notification Banner */}
      {isListening && (
        <div className="flex items-center gap-2 p-2.5 rounded-xl bg-rose-500/15 border border-rose-500/30 text-xs text-rose-300 animate-pulse">
          <Mic className="w-4 h-4 text-rose-400 shrink-0" />
          <span>Listening to speech... Speak in English, Telugu, or Hindi. Tap Send when ready.</span>
        </div>
      )}

      {/* Image Preview */}
      {imagePreview && (
        <div className="relative inline-block rounded-xl overflow-hidden border border-[#08A873] shadow-md">
          <img src={imagePreview} alt="Attached preview" className="w-20 h-20 object-cover" />
          <button
            type="button"
            onClick={() => setImagePreview(null)}
            className="absolute top-1 right-1 p-0.5 rounded-full bg-black/80 text-white"
            aria-label="Remove image"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Composer Input Form */}
      <form onSubmit={handleSubmit} className="flex items-end gap-2">
        
        {/* Hidden File Picker */}
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileUpload}
          accept="image/*"
          className="hidden"
        />

        {/* Attachment Button */}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="p-2.5 rounded-xl bg-[#111E31] border border-[#26374D] hover:border-[#3B5270] text-[#A9B7C8] hover:text-[#F5F8FC] transition shrink-0"
          title="Attach farm or leaf photo"
          aria-label="Attach Photo"
        >
          <Paperclip className="w-4 h-4" />
        </button>

        {/* Voice Input Button */}
        <VoiceInputButton
          currentText={inputText}
          onTranscript={(text) => setInputText(text)}
          onListeningChange={setIsListening}
          disabled={isStreaming}
        />

        {/* Text Input Area */}
        <div className="flex-1 min-w-0 rounded-xl bg-[#111E31] border border-[#26374D] focus-within:border-[#08A873] focus-within:ring-1 focus-within:ring-[#08A873] transition">
          <textarea
            ref={textareaRef}
            rows={1}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about crops, soil, weather, pests, or government schemes…"
            disabled={isStreaming}
            className="w-full px-3.5 py-2.5 bg-transparent text-sm text-[#F5F8FC] placeholder-[#718197] resize-none focus:outline-none max-h-32"
          />
        </div>

        {/* Submit / Send Button */}
        <button
          type="submit"
          disabled={isStreaming || (!inputText.trim() && !imagePreview)}
          className="p-2.5 rounded-xl bg-[#08A873] hover:bg-[#09C486] disabled:opacity-40 text-white font-bold transition shadow-sm flex items-center justify-center shrink-0"
          aria-label="Send message"
        >
          {isStreaming ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>

      </form>

    </div>
  );
};
