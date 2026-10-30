import { LanguageCode } from '../types';
import {
  speechService as unifiedSpeechService,
  cleanTextForSpeech,
  detectLanguage,
  AudioState,
  AudioMode,
  ISpeechService
} from '../services/speech';

// Re-export speech service types and utilities
export type { AudioState, AudioMode, ISpeechService } from '../services/speech';
export { cleanTextForSpeech, detectLanguage };

// Declare types for Web Speech API
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

export function isSpeechRecognitionSupported(): boolean {
  const supported = typeof window !== 'undefined' && ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window);
  if (import.meta.env.DEV) {
    console.debug('[VoicePipeline] voice_supported:', supported);
  }
  return supported;
}

export function isSpeechSynthesisSupported(): boolean {
  return unifiedSpeechService.isSupported();
}

/**
 * Backward-compatibility wrapper delegating to unified application speechService.
 */
export const speechAudioController = {
  play: (
    text: string,
    lang?: LanguageCode | string,
    onStateChange?: (state: AudioState) => void,
    mode: AudioMode = 'NORMAL_RESPONSE',
    id: string = ''
  ) => {
    unifiedSpeechService.speak({
      text,
      language: lang,
      onStateChange,
      mode,
      id
    });
  },
  pause: () => unifiedSpeechService.pause(),
  resume: () => unifiedSpeechService.resume(),
  stop: () => unifiedSpeechService.stop(),
  getState: () => unifiedSpeechService.getState(),
  getMode: () => unifiedSpeechService.getMode(),
  getId: () => unifiedSpeechService.getId()
};

export function speakText(
  text: string,
  lang: LanguageCode | string = 'en',
  onStart?: () => void,
  onEnd?: () => void,
  onError?: (err: any) => void
) {
  unifiedSpeechService.speak({
    text,
    language: lang,
    onStateChange: (state) => {
      if (state === 'PLAYING' && onStart) onStart();
      else if ((state === 'COMPLETED' || state === 'STOPPED') && onEnd) onEnd();
      else if (state === 'ERROR' && onError) onError(new Error('Audio synthesis failed'));
    }
  });
}

export function stopSpeaking() {
  unifiedSpeechService.stop();
}

export function getSpeechDiagnosticInfo(text: string, lang?: LanguageCode | string) {
  return unifiedSpeechService.getDiagnosticInfo(text, lang);
}

export const speechService = unifiedSpeechService;

export function startSpeechRecognition(
  lang: LanguageCode,
  onInterimResult: (text: string) => void,
  onFinalResult: (text: string) => void,
  onEnd?: () => void,
  onError?: (errMessage: string, rawError?: any) => void
) {
  if (!isSpeechRecognitionSupported()) {
    const errMsg = 'Speech recognition is not supported in this browser. Please use Chrome, Edge, or an Android browser.';
    if (import.meta.env.DEV) {
      console.debug('[VoicePipeline] recognition_error:', errMsg);
    }
    if (onError) onError(errMsg);
    return null;
  }

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = new SpeechRecognition();

  const langMap: Record<LanguageCode, string> = {
    en: 'en-IN',
    te: 'te-IN',
    hi: 'hi-IN'
  };

  const recognitionLang = langMap[lang] || 'en-IN';
  recognition.lang = recognitionLang;
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.maxAlternatives = 1;

  if (import.meta.env.DEV) {
    console.debug('[VoicePipeline] recognition_language:', recognitionLang);
  }

  recognition.onstart = () => {
    if (import.meta.env.DEV) {
      console.debug('[VoicePipeline] recognition_started');
    }
  };

  recognition.onresult = (event: any) => {
    let interimText = '';
    let finalText = '';

    for (let i = event.resultIndex || 0; i < event.results.length; ++i) {
      const transcriptPiece = event.results[i][0].transcript;
      if (event.results[i].isFinal) {
        finalText += transcriptPiece + ' ';
      } else {
        interimText += transcriptPiece;
      }
    }

    const fullTranscript = (finalText + interimText).trim();
    if (fullTranscript) {
      if (import.meta.env.DEV) {
        if (finalText.trim()) {
          console.debug('[VoicePipeline] final_transcript:', fullTranscript);
        } else {
          console.debug('[VoicePipeline] interim_transcript:', fullTranscript);
        }
      }
      onInterimResult(fullTranscript);
      if (finalText.trim()) {
        onFinalResult(fullTranscript);
      }
    }
  };

  recognition.onerror = (event: any) => {
    let userFriendlyError = 'An error occurred during voice recognition.';
    if (event.error === 'not-allowed' || event.error === 'permission-denied') {
      userFriendlyError = 'Microphone access was denied. Please allow microphone permissions in your browser.';
    } else if (event.error === 'no-speech') {
      userFriendlyError = 'No speech detected. Please speak into the microphone.';
    } else if (event.error === 'audio-capture') {
      userFriendlyError = 'Microphone is unavailable or in use by another application.';
    } else if (event.error === 'network') {
      userFriendlyError = 'Network error during voice recognition.';
    }

    if (import.meta.env.DEV) {
      console.debug('[VoicePipeline] recognition_error:', event.error, userFriendlyError);
    }
    if (onError) onError(userFriendlyError, event);
  };

  recognition.onend = () => {
    if (import.meta.env.DEV) {
      console.debug('[VoicePipeline] recognition_ended');
    }
    if (onEnd) onEnd();
  };

  try {
    recognition.start();
  } catch (e) {
    if (import.meta.env.DEV) {
      console.debug('[VoicePipeline] recognition_start_exception:', e);
    }
  }

  return recognition;
}
