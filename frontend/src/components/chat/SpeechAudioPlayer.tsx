import React, { useState, useEffect } from 'react';
import { Volume2, Square } from 'lucide-react';
import { speechService, AudioState } from '../../services/speech';
import { useLanguage } from '../../contexts/LanguageContext';
import { LanguageCode } from '../../types';

interface SpeechAudioPlayerProps {
  text: string;
  language?: LanguageCode | string;
}

export const SpeechAudioPlayer: React.FC<SpeechAudioPlayerProps> = ({ text, language }) => {
  const { language: uiLanguage, t } = useLanguage();
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    return () => {
      // If unmounting while playing, stop speech
      if (isPlaying) {
        speechService.stop();
      }
    };
  }, [isPlaying]);

  const handlePlay = () => {
    if (isPlaying) {
      speechService.stop();
      setIsPlaying(false);
      return;
    }

    if (!speechService.isSupported()) {
      alert("Text-to-speech is not supported by your current device or browser.");
      return;
    }

    // Language Precedence: script in text -> explicit message language -> UI context language -> English
    const targetLang = speechService.detectLanguage(text, language || uiLanguage);
    const diagnostic = speechService.getDiagnosticInfo(text, language || uiLanguage);

    if (!speechService.hasVoiceForLanguage(targetLang)) {
      console.warn('[SpeechAudioPlayer] Voice diagnostic warning:', diagnostic);
      alert(diagnostic.diagnosticMessage);
      return;
    }

    speechService.speak({
      text,
      language: targetLang,
      onStateChange: (state: AudioState) => {
        setIsPlaying(state === 'PLAYING');
      },
      mode: 'NORMAL_RESPONSE'
    });
  };

  return (
    <button
      type="button"
      onClick={handlePlay}
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
        isPlaying
          ? 'bg-rose-100 dark:bg-rose-950 text-rose-700 dark:text-rose-300 border border-rose-300 dark:border-rose-800 animate-pulse'
          : 'bg-stone-100 dark:bg-slate-700/60 text-slate-600 dark:text-slate-300 hover:bg-emerald-50 hover:text-emerald-700 dark:hover:bg-slate-700 border border-stone-200 dark:border-slate-600'
      }`}
      title={isPlaying ? t.stopAudio : t.listenToAudio}
      aria-label={isPlaying ? "Stop Audio" : "Listen Aloud"}
    >
      {isPlaying ? (
        <>
          <Square className="w-3.5 h-3.5 text-rose-600 fill-rose-600" />
          <span>{t.stopAudio}</span>
        </>
      ) : (
        <>
          <Volume2 className="w-3.5 h-3.5 text-emerald-600" />
          <span>{t.listenToAudio}</span>
        </>
      )}
    </button>
  );
};
