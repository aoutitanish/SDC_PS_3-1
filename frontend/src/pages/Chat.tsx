import React, { useState, useRef, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useChat } from '../contexts/ChatContext';
import { useLanguage } from '../contexts/LanguageContext';
import { useFarm } from '../contexts/FarmContext';
import { ChatMessage } from '../components/chat/ChatMessage';
import { ChatHistorySidebar } from '../components/chat/ChatHistorySidebar';
import { VoiceInputButton } from '../components/chat/VoiceInputButton';
import { LocationModal } from '../components/modals/LocationModal';
import { LanguageModal } from '../components/modals/LanguageModal';
import { ExportModal } from '../components/modals/ExportModal';
import { ShareModal } from '../components/modals/ShareModal';
import { CropDetailDrawer } from '../components/modals/CropDetailDrawer';
import { ScoreExplainModal } from '../components/modals/ScoreExplainModal';
import { TOP_RECOMMENDED_CROPS, CropSummary } from '../data/dashboardMock';
import {
  Send,
  Camera,
  MapPin,
  Mic,
  Sparkles,
  Share2,
  Download,
  Trash2,
  Edit3,
  X,
  Loader2,
  ChevronRight,
  ShieldCheck,
  History
} from 'lucide-react';

export const Chat: React.FC = () => {
  const { messages, isStreaming, sendMessage, clearChat, startNewSession } = useChat();
  const { farm } = useFarm();
  const { language, setLanguage } = useLanguage();
  const location = useLocation();

  const [inputText, setInputText] = useState('');
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isVoiceListening, setIsVoiceListening] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(true);
  const [isLocationOpen, setIsLocationOpen] = useState(false);
  const [isLanguageOpen, setIsLanguageOpen] = useState(false);
  const [isExportOpen, setIsExportOpen] = useState(false);
  const [isShareOpen, setIsShareOpen] = useState(false);
  const [selectedCrop, setSelectedCrop] = useState<CropSummary | null>(null);
  const [isCropDrawerOpen, setIsCropDrawerOpen] = useState(false);
  const [explainData, setExplainData] = useState<{ cropName: string; score: number; conf: string } | null>(null);
  const [isScoreModalOpen, setIsScoreModalOpen] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const suggestedQuestions = [
    'Which crops are suitable for sandy loam soil with drip irrigation?',
    'What is the optimal soil pH and temperature range for cotton?',
    'My tomato leaves are turning yellow. What could be the cause?',
    'What are the sowing guidelines for wheat in Rabi season?'
  ];

  // Parse URL query if redirected from home
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const q = params.get('q');
    if (q) {
      sendMessage(q);
    }
  }, [location.search]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if ((!inputText.trim() && !imagePreview) || isStreaming) return;
    sendMessage(inputText, imagePreview || undefined);
    setInputText('');
    setImagePreview(null);
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
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

  const handleSelectCrop = (cropOrName: CropSummary | string) => {
    if (typeof cropOrName === 'string') {
      const found = TOP_RECOMMENDED_CROPS.find(c => c.name.toLowerCase().includes(cropOrName.toLowerCase())) || TOP_RECOMMENDED_CROPS[0];
      setSelectedCrop(found);
    } else {
      setSelectedCrop(cropOrName);
    }
    setIsCropDrawerOpen(true);
  };

  const handleExplainScore = (cropName: string, score: number, conf: string) => {
    setExplainData({ cropName, score, conf });
    setIsScoreModalOpen(true);
  };

  const isInitialState = messages.length <= 1;

  return (
    <div className="relative min-h-[calc(100vh-4.5rem)] -m-4 sm:-m-6 lg:-m-8 py-8 px-4 sm:px-6 flex flex-col items-center justify-start overflow-x-hidden">
      
      {/* Lush Green Crop Field Background with Gradient Overlay */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <img
          src="/images/green_crop_field_bg.jpg"
          alt="Agricultural field backdrop"
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-emerald-950/75 backdrop-blur-[2px]" />
      </div>

      <div className="relative z-10 w-full max-w-6xl mx-auto space-y-6">
        
        {/* Top Centered Greeting Banner */}
        <div className="text-center space-y-2 text-white">
          <div className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full bg-white/15 backdrop-blur-md text-emerald-200 text-xs font-bold uppercase tracking-wider font-display">
            <Sparkles className="w-3.5 h-3.5 text-amber-300" />
            <span>AI Agricultural Assistant</span>
          </div>
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight font-display drop-shadow-md">
            Smart Farming Guidance in Your Language
          </h1>
          <p className="text-sm sm:text-base text-emerald-100 font-medium max-w-lg mx-auto font-sans">
            Ask any crop suitability, soil nutrient, pest diagnosis, or rainfall question below.
          </p>
        </div>

        {/* Main Content: History Beside + Chat Box */}
        <div className="flex flex-col lg:flex-row items-start gap-6 w-full">
          
          {/* History Sidebar Beside Chat */}
          <ChatHistorySidebar
            isOpen={isHistoryOpen}
            onToggle={() => setIsHistoryOpen(!isHistoryOpen)}
          />

          {/* Floating White Chat Container with Rich Depth */}
          <div className="flex-1 w-full bg-white rounded-3xl shadow-2xl border border-emerald-100 overflow-hidden flex flex-col transition-all duration-300 min-h-[580px]">
            
            {/* Card Top Action Bar */}
            <div className="px-6 py-3.5 bg-[#F8FAF9] border-b border-[#E2ECE6] flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <button
                  type="button"
                  onClick={() => setIsHistoryOpen(!isHistoryOpen)}
                  className="p-1.5 rounded-xl text-[#526B60] hover:text-[#059669] hover:bg-white transition border border-transparent hover:border-[#E2ECE6] mr-1"
                  title="Toggle Consultation History"
                >
                  <History className="w-4 h-4 text-[#059669]" />
                </button>
                <span className="w-2.5 h-2.5 rounded-full bg-[#059669] animate-pulse" />
                <span className="font-extrabold text-sm text-[#0F281E] tracking-tight font-display">
                  KrishiChat AI
                </span>
                <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-[#E8F5EF] text-[#059669] border border-[#059669]/25 font-display flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3" />
                  <span>Evidence-Backed</span>
                </span>
              </div>

              <div className="flex items-center gap-1.5">
                {/* New Consultation */}
                <button
                  type="button"
                  onClick={startNewSession}
                  className="p-2 rounded-xl text-[#526B60] hover:text-[#059669] hover:bg-white transition shadow-sm border border-transparent hover:border-[#E2ECE6]"
                  title="New Consultation"
                >
                  <Edit3 className="w-4 h-4" />
                </button>

                {/* Share */}
                <button
                  type="button"
                  onClick={() => setIsShareOpen(true)}
                  className="p-2 rounded-xl text-[#526B60] hover:text-[#059669] hover:bg-white transition shadow-sm border border-transparent hover:border-[#E2ECE6]"
                  title="Share Advisory"
                >
                  <Share2 className="w-4 h-4" />
                </button>

                {/* Export */}
                <button
                  type="button"
                  onClick={() => setIsExportOpen(true)}
                  className="p-2 rounded-xl text-[#526B60] hover:text-[#059669] hover:bg-white transition shadow-sm border border-transparent hover:border-[#E2ECE6]"
                  title="Export Advisory"
                >
                  <Download className="w-4 h-4" />
                </button>

                {/* Clear Chat */}
                <button
                  type="button"
                  onClick={clearChat}
                  className="p-2 rounded-xl text-[#526B60] hover:text-rose-600 hover:bg-rose-50 transition shadow-sm border border-transparent hover:border-rose-200"
                  title="Clear Current Screen"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Card Body */}
            <div className="p-6 sm:p-8 space-y-6 flex-1 max-h-[58vh] overflow-y-auto">
              
              {/* Mascot Avatar & Hero Header */}
              {isInitialState && (
                <div className="text-center space-y-3 py-2 animate-in fade-in">
                  <div className="relative inline-block">
                    <img
                      src="/images/krishi_mascot_avatar.jpg"
                      alt="KrishiMitra Mascot Avatar"
                      className="w-24 h-24 sm:w-28 sm:h-28 rounded-full object-cover mx-auto shadow-lg ring-4 ring-[#E8F5EF]"
                    />
                    <span className="absolute bottom-1 right-1 w-5 h-5 rounded-full bg-[#059669] border-2 border-white flex items-center justify-center text-white text-[10px] font-bold">
                      ✓
                    </span>
                  </div>

                  <div>
                    <h2 className="text-2xl font-black text-[#0F281E] tracking-tight font-display">
                      KrishiChat AI
                    </h2>
                    <p className="text-xs font-bold text-[#059669] font-display">
                      Powered by KrishiMitra AI • Smart Agriculture Assistant
                    </p>
                    <p className="text-xs text-[#526B60] max-w-md mx-auto mt-1 leading-relaxed font-sans">
                      Explainable AI providing grounded crop advice, soil diagnosis, and weather insights for Indian farmers.
                    </p>
                  </div>

                  {/* Dynamic Intelligence Strip */}
                  <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#F0F7F3] border border-[#D0E5DA] text-xs font-semibold text-[#0F281E] font-sans">
                    <Sparkles className="w-3.5 h-3.5 text-[#059669]" />
                    <span>Dynamic RAG • Local Ollama Qwen 3.5 9B</span>
                  </div>
                </div>
              )}

              {/* Suggested Question Pills */}
              {isInitialState && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-2">
                  {suggestedQuestions.map((q, idx) => (
                    <button
                      key={idx}
                      onClick={() => sendMessage(q)}
                      className="p-3.5 rounded-2xl bg-[#F0F7F3] hover:bg-[#E2F2E9] border border-[#D0E5DA] text-xs font-semibold text-[#0F281E] text-left transition hover:scale-[1.01] flex items-center justify-between group shadow-sm font-sans"
                    >
                      <span className="line-clamp-1">{q}</span>
                      <ChevronRight className="w-4 h-4 text-[#059669] opacity-0 group-hover:opacity-100 transition-opacity shrink-0 ml-1" />
                    </button>
                  ))}
                </div>
              )}

              {/* Active Message Stream */}
              {!isInitialState && (
                <div className="space-y-4">
                  {messages.map((msg) => (
                    <ChatMessage
                      key={msg.id}
                      message={msg}
                      onSelectCrop={handleSelectCrop}
                      onExplainScore={handleExplainScore}
                      onQuickReply={(reply) => sendMessage(reply)}
                    />
                  ))}
                  <div ref={messagesEndRef} />
                </div>
              )}

            </div>

            {/* Card Bottom Composer */}
            <div className="p-4 sm:p-5 bg-[#F8FAF9] border-t border-[#E2ECE6]">
              
              {/* Voice Listening Banner */}
              {isVoiceListening && (
                <div className="mb-2 p-2.5 rounded-2xl bg-rose-50 border border-rose-200 text-xs text-rose-800 font-semibold flex items-center gap-2 animate-pulse font-sans">
                  <Mic className="w-4 h-4 text-rose-600 shrink-0" />
                  <span>Listening... Speak your question and review in the box below.</span>
                </div>
              )}

              {/* Image Preview Thumbnail */}
              {imagePreview && (
                <div className="relative inline-block mb-2 rounded-xl overflow-hidden border border-[#059669] shadow-md">
                  <img src={imagePreview} alt="Attached crop" className="w-16 h-16 object-cover" />
                  <button
                    type="button"
                    onClick={() => setImagePreview(null)}
                    className="absolute top-1 right-1 p-0.5 rounded-full bg-black/70 text-white"
                    aria-label="Remove image"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              )}

              <form onSubmit={handleSend} className="flex items-center gap-2">
                
                {/* Hidden File Picker */}
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleImageUpload}
                  accept="image/*"
                  className="hidden"
                />

                {/* Location Tag */}
                <button
                  type="button"
                  onClick={() => setIsLocationOpen(true)}
                  className="p-3 rounded-2xl bg-white border border-[#D0E5DA] text-[#526B60] hover:text-[#059669] hover:border-[#059669] transition shrink-0 shadow-sm"
                  title="Set Location"
                >
                  <MapPin className="w-4 h-4" />
                </button>

                {/* Camera / Photo Attachment */}
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="p-3 rounded-2xl bg-white border border-[#D0E5DA] text-[#526B60] hover:text-[#059669] hover:border-[#059669] transition shrink-0 shadow-sm"
                  title="Attach Crop Image"
                >
                  <Camera className="w-4 h-4" />
                </button>

                {/* Text Input */}
                <input
                  type="text"
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder="Ask KrishiChat any crop or soil question..."
                  disabled={isStreaming}
                  className="flex-1 px-4 py-3 rounded-2xl bg-white border border-[#D0E5DA] text-sm text-[#0F281E] placeholder-[#526B60] focus:border-[#059669] focus:outline-none transition shadow-sm font-sans"
                />

                {/* Voice Mic Button */}
                <VoiceInputButton
                  currentText={inputText}
                  onTranscript={(text) => setInputText(text)}
                  onListeningChange={setIsVoiceListening}
                  disabled={isStreaming}
                />

                {/* Send Button */}
                <button
                  type="submit"
                  disabled={isStreaming || (!inputText.trim() && !imagePreview)}
                  className="p-3.5 rounded-2xl bg-[#059669] hover:bg-[#047857] disabled:opacity-40 text-white font-bold transition shadow-md shadow-[#059669]/25 flex items-center justify-center shrink-0"
                  aria-label="Send message"
                >
                  {isStreaming ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Send className="w-5 h-5" />
                  )}
                </button>

              </form>

              <div className="text-center mt-2.5">
                <span className="text-[10px] text-[#526B60] font-medium font-sans">
                  Powered by KrishiMitra AI • Evidence-Based Dynamic Retrieval & Qwen Intelligence
                </span>
              </div>

            </div>

          </div>

        </div>

      </div>

      {/* Modals & Drawers */}
      <LocationModal
        isOpen={isLocationOpen}
        onClose={() => setIsLocationOpen(false)}
      />

      <LanguageModal
        isOpen={isLanguageOpen}
        onClose={() => setIsLanguageOpen(false)}
      />

      <ExportModal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        chatContent={messages.map(m => `${m.sender.toUpperCase()}: ${m.content}`).join('\n\n')}
      />

      <ShareModal
        isOpen={isShareOpen}
        onClose={() => setIsShareOpen(false)}
      />

      <CropDetailDrawer
        isOpen={isCropDrawerOpen}
        onClose={() => setIsCropDrawerOpen(false)}
        crop={selectedCrop}
      />

      <ScoreExplainModal
        isOpen={isScoreModalOpen}
        onClose={() => setIsScoreModalOpen(false)}
        cropName={explainData?.cropName}
        score={explainData?.score}
        confidence={explainData?.conf}
      />

    </div>
  );
};
