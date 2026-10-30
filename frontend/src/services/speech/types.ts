import { LanguageCode } from '../../types';

export type AudioState = 'IDLE' | 'PLAYING' | 'PAUSED' | 'STOPPED' | 'COMPLETED' | 'ERROR';
export type AudioMode = 'NORMAL_RESPONSE' | 'FULL_ANALYSIS';

export interface SpeechVoice {
  id: string;
  name: string;
  lang: string;
  isDefault?: boolean;
}

export interface SpeechDiagnosticInfo {
  detectedLanguage: LanguageCode;
  requestedLocale: string;
  matchedVoice: SpeechVoice | null;
  availableVoicesForLang: SpeechVoice[];
  availableTeluguVoices: SpeechVoice[];
  availableHindiVoices: SpeechVoice[];
  availableEnglishVoices: SpeechVoice[];
  isVoiceAvailable: boolean;
  diagnosticMessage: string;
}

export interface SpeakOptions {
  text: string;
  language?: LanguageCode | string;
  onStateChange?: (state: AudioState) => void;
  mode?: AudioMode;
  id?: string;
  rate?: number;
  pitch?: number;
}

export interface ISpeechService {
  isSupported(): boolean;
  detectLanguage(text: string, fallbackLang?: LanguageCode | string): LanguageCode;
  getAvailableVoices(): Promise<SpeechVoice[]>;
  hasVoiceForLanguage(lang: LanguageCode | string): boolean;
  getDiagnosticInfo(text: string, language?: LanguageCode | string): SpeechDiagnosticInfo;
  speak(options: SpeakOptions): void;
  pause(): void;
  resume(): void;
  stop(): void;
  getState(): AudioState;
  getMode(): AudioMode;
  getId(): string;
}
