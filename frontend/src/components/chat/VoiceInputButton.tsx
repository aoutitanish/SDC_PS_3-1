import React, { useState, useRef } from 'react';
import { Mic, MicOff } from 'lucide-react';
import { isSpeechRecognitionSupported, startSpeechRecognition } from '../../utils/speech';
import { useLanguage } from '../../contexts/LanguageContext';

interface VoiceInputButtonProps {
  onTranscript: (text: string) => void;
  currentText?: string;
  disabled?: boolean;
  onListeningChange?: (listening: boolean) => void;
}

export const VoiceInputButton: React.FC<VoiceInputButtonProps> = ({
  onTranscript,
  currentText = '',
  disabled,
  onListeningChange
}) => {
  const { language, t } = useLanguage();
  const [isListening, setIsListening] = useState(false);
  const [recognitionInstance, setRecognitionInstance] = useState<any>(null);
  const initialPrefixRef = useRef<string>('');

  const handleToggleVoice = () => {
    if (isListening) {
      if (recognitionInstance) {
        try {
          recognitionInstance.stop();
        } catch (e) {
          console.warn('Error stopping recognition:', e);
        }
      }
      setIsListening(false);
      if (onListeningChange) onListeningChange(false);
      return;
    }

    if (!isSpeechRecognitionSupported()) {
      alert("Voice input is not supported by your current browser. Please try Chrome, Edge, or an Android browser.");
      return;
    }

    // Save existing text before recording so we don't wipe it out, but don't duplicate either
    initialPrefixRef.current = currentText ? currentText.trim() : '';

    setIsListening(true);
    if (onListeningChange) onListeningChange(true);

    const rec = startSpeechRecognition(
      language,
      // onInterimResult
      (interim) => {
        const full = initialPrefixRef.current
          ? `${initialPrefixRef.current} ${interim}`
          : interim;
        onTranscript(full);
      },
      // onFinalResult
      (final) => {
        const full = initialPrefixRef.current
          ? `${initialPrefixRef.current} ${final}`
          : final;
        onTranscript(full);
      },
      // onEnd
      () => {
        setIsListening(false);
        if (onListeningChange) onListeningChange(false);
      },
      // onError
      (errMsg) => {
        console.warn("Speech recognition error:", errMsg);
        setIsListening(false);
        if (onListeningChange) onListeningChange(false);
        alert(errMsg);
      }
    );
    setRecognitionInstance(rec);
  };

  return (
    <button
      type="button"
      onClick={handleToggleVoice}
      disabled={disabled}
      title={isListening ? t.stopAudio : t.listening}
      aria-label={isListening ? "Stop Voice Input" : "Start Voice Input"}
      className={`relative p-3 rounded-2xl transition-all duration-200 flex items-center justify-center shrink-0 ${
        isListening
          ? 'bg-rose-600 text-white shadow-lg shadow-rose-500/40 animate-pulse ring-4 ring-rose-200'
          : 'bg-white border border-[#D0E5DA] text-[#526B60] hover:text-[#059669] hover:border-[#059669]'
      } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      {isListening ? (
        <MicOff className="w-5 h-5 animate-bounce" />
      ) : (
        <Mic className="w-5 h-5" />
      )}
    </button>
  );
};
