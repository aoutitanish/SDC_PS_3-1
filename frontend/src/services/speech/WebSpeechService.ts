import { ISpeechService, SpeakOptions, AudioState, AudioMode, SpeechVoice, SpeechDiagnosticInfo } from './types';
import { detectLanguage, normalizeLanguage, cleanTextForSpeech } from './languageDetector';
import { LanguageCode } from '../../types';

/**
 * Web implementation of ISpeechService using the Web Speech API (window.speechSynthesis).
 * Encapsulates browser voice caching, asynchronous voice resolution, script detection,
 * robust language matching for Telugu/Hindi/English, and diagnostic reporting.
 */
export class WebSpeechService implements ISpeechService {
  private currentState: AudioState = 'IDLE';
  private currentMode: AudioMode = 'NORMAL_RESPONSE';
  private currentId: string = '';
  private currentUtterance: SpeechSynthesisUtterance | null = null;
  private onStateChangeCallback: ((state: AudioState) => void) | null = null;
  private voiceCache: SpeechSynthesisVoice[] = [];
  private isVoiceListLoaded: boolean = false;

  constructor() {
    this.initVoiceCache();
    this.exposeGlobalDiagnostic();
  }

  private initVoiceCache(): void {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      return;
    }

    const updateVoices = () => {
      const voices = window.speechSynthesis.getVoices();
      if (voices && voices.length > 0) {
        this.voiceCache = voices;
        this.isVoiceListLoaded = true;
      }
    };

    updateVoices();

    // Attach event listeners for asynchronous voice loading in Chrome, Edge, and Safari
    if (typeof window.speechSynthesis.addEventListener === 'function') {
      window.speechSynthesis.addEventListener('voiceschanged', updateVoices);
    }
    if (window.speechSynthesis.onvoiceschanged !== undefined) {
      window.speechSynthesis.onvoiceschanged = updateVoices;
    }
  }

  private refreshVoiceCache(): SpeechSynthesisVoice[] {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      const voices = window.speechSynthesis.getVoices();
      if (voices && voices.length > 0) {
        this.voiceCache = voices;
        this.isVoiceListLoaded = true;
      }
    }
    return this.voiceCache;
  }

  private getVoicesSync(): SpeechSynthesisVoice[] {
    if (this.voiceCache && this.voiceCache.length > 0) {
      return this.voiceCache;
    }
    return this.refreshVoiceCache();
  }

  /**
   * Helper to ensure voices are loaded even if window.speechSynthesis.getVoices()
   * was initially empty when the app loaded.
   */
  public async ensureVoicesLoaded(timeoutMs: number = 300): Promise<SpeechSynthesisVoice[]> {
    if (!this.isSupported()) return [];
    const voices = this.getVoicesSync();
    if (voices.length > 0) return voices;

    return new Promise((resolve) => {
      let resolved = false;

      const onVoices = () => {
        if (!resolved) {
          resolved = true;
          const v = this.refreshVoiceCache();
          resolve(v);
        }
      };

      if (typeof window.speechSynthesis.addEventListener === 'function') {
        window.speechSynthesis.addEventListener('voiceschanged', onVoices, { once: true });
      }

      setTimeout(() => {
        if (!resolved) {
          resolved = true;
          resolve(this.refreshVoiceCache());
        }
      }, timeoutMs);
    });
  }

  public isSupported(): boolean {
    return typeof window !== 'undefined' && 'speechSynthesis' in window;
  }

  public getState(): AudioState {
    return this.currentState;
  }

  public getMode(): AudioMode {
    return this.currentMode;
  }

  public getId(): string {
    return this.currentId;
  }

  public detectLanguage(text: string, fallbackLang?: LanguageCode | string): LanguageCode {
    return detectLanguage(text, normalizeLanguage(fallbackLang));
  }

  public async getAvailableVoices(): Promise<SpeechVoice[]> {
    if (!this.isSupported()) return [];

    let voices = await this.ensureVoicesLoaded();
    if (!voices || voices.length === 0) {
      voices = this.getVoicesSync();
    }

    return (voices || []).map((v, idx) => ({
      id: v.voiceURI || `voice_${idx}_${v.lang}`,
      name: v.name,
      lang: v.lang,
      isDefault: v.default
    }));
  }

  private cleanNormalize(str: string): string {
    return (str || '').toLowerCase().replace(/_/g, '-').trim();
  }

  private isTeluguVoice(v: SpeechSynthesisVoice): boolean {
    const normLang = this.cleanNormalize(v.lang);
    const normName = (v.name || '').toLowerCase();
    const normURI = (v.voiceURI || '').toLowerCase();

    return (
      normLang === 'te-in' ||
      normLang.startsWith('te-') ||
      normLang === 'te' ||
      normName.includes('telugu') ||
      normURI.includes('telugu') ||
      normName.includes('te-in') ||
      normName.includes('te_in')
    );
  }

  private isHindiVoice(v: SpeechSynthesisVoice): boolean {
    const normLang = this.cleanNormalize(v.lang);
    const normName = (v.name || '').toLowerCase();
    const normURI = (v.voiceURI || '').toLowerCase();

    return (
      normLang === 'hi-in' ||
      normLang.startsWith('hi-') ||
      normLang === 'hi' ||
      normName.includes('hindi') ||
      normURI.includes('hindi') ||
      normName.includes('hi-in') ||
      normName.includes('hi_in')
    );
  }

  private isEnglishVoice(v: SpeechSynthesisVoice): boolean {
    const normLang = this.cleanNormalize(v.lang);
    const normName = (v.name || '').toLowerCase();

    return (
      normLang.startsWith('en') ||
      normName.includes('english')
    );
  }

  /**
   * Resolves the best matching SpeechSynthesisVoice for a target application language.
   * Maps 'te'->'te-IN', 'hi'->'hi-IN', 'en'->'en-IN'.
   * Never forces an English voice onto Telugu or Hindi text.
   */
  public findMatchingVoice(targetLang: LanguageCode | string): SpeechSynthesisVoice | null {
    const voices = this.getVoicesSync();
    if (!voices || voices.length === 0) {
      return null;
    }

    const normTarget = normalizeLanguage(targetLang);

    if (normTarget === 'te') {
      const teVoice = voices.find(v => this.isTeluguVoice(v));
      if (teVoice) return teVoice;
      return null; // DO NOT fallback to an English voice object for Telugu!
    }

    if (normTarget === 'hi') {
      const hiVoice = voices.find(v => this.isHindiVoice(v));
      if (hiVoice) return hiVoice;
      return null; // DO NOT fallback to an English voice object for Hindi!
    }

    // English language matching: Prefer Indian English (en-IN), then any English voice
    const enInVoice = voices.find(v => {
      const normLang = this.cleanNormalize(v.lang);
      const normName = (v.name || '').toLowerCase();
      return normLang === 'en-in' || normName.includes('india') || normName.includes('en-in');
    });
    if (enInVoice) return enInVoice;

    const anyEnVoice = voices.find(v => this.isEnglishVoice(v));
    if (anyEnVoice) return anyEnVoice;

    return voices.find(v => v.default) || voices[0] || null;
  }

  public hasVoiceForLanguage(lang: LanguageCode | string): boolean {
    if (!this.isSupported()) return false;
    const normTarget = normalizeLanguage(lang);
    if (normTarget === 'en') {
      // English is supported if synthesis is available
      return true;
    }
    return this.findMatchingVoice(normTarget) !== null;
  }

  public getDiagnosticInfo(text: string, language?: LanguageCode | string): SpeechDiagnosticInfo {
    const detectedLanguage = this.detectLanguage(text, language);
    const localeMap: Record<LanguageCode, string> = {
      en: 'en-IN',
      te: 'te-IN',
      hi: 'hi-IN'
    };
    const requestedLocale = localeMap[detectedLanguage] || 'en-IN';

    const voices = this.getVoicesSync();
    const rawMatchedVoice = this.findMatchingVoice(detectedLanguage);

    const formatVoice = (v: SpeechSynthesisVoice | null): SpeechVoice | null => {
      if (!v) return null;
      return {
        id: v.voiceURI || `voice_${v.name}_${v.lang}`,
        name: v.name,
        lang: v.lang,
        isDefault: v.default
      };
    };

    const matchedVoice = formatVoice(rawMatchedVoice);
    const availableTeluguVoices = voices.filter(v => this.isTeluguVoice(v)).map(v => formatVoice(v)!);
    const availableHindiVoices = voices.filter(v => this.isHindiVoice(v)).map(v => formatVoice(v)!);
    const availableEnglishVoices = voices.filter(v => this.isEnglishVoice(v)).map(v => formatVoice(v)!);

    let availableVoicesForLang: SpeechVoice[] = [];
    if (detectedLanguage === 'te') availableVoicesForLang = availableTeluguVoices;
    else if (detectedLanguage === 'hi') availableVoicesForLang = availableHindiVoices;
    else availableVoicesForLang = availableEnglishVoices;

    const isVoiceAvailable = this.hasVoiceForLanguage(detectedLanguage);

    let diagnosticMessage = '';
    if (isVoiceAvailable && matchedVoice) {
      diagnosticMessage = `Speech voice '${matchedVoice.name}' (${matchedVoice.lang}) is ready for ${requestedLocale}.`;
    } else if (detectedLanguage === 'te') {
      diagnosticMessage = 'Telugu speech voice is not available in this browser/system.';
    } else if (detectedLanguage === 'hi') {
      diagnosticMessage = 'Hindi speech voice is not available in this browser/system.';
    } else {
      diagnosticMessage = 'English speech voice is ready.';
    }

    return {
      detectedLanguage,
      requestedLocale,
      matchedVoice,
      availableVoicesForLang,
      availableTeluguVoices,
      availableHindiVoices,
      availableEnglishVoices,
      isVoiceAvailable,
      diagnosticMessage
    };
  }

  private exposeGlobalDiagnostic(): void {
    if (typeof window !== 'undefined') {
      (window as any).getSpeechDiagnostic = (text: string = 'పంట సిఫార్సు', lang?: string) => {
        const info = this.getDiagnosticInfo(text, lang);
        console.table({
          detectedLanguage: info.detectedLanguage,
          requestedLocale: info.requestedLocale,
          isVoiceAvailable: info.isVoiceAvailable,
          matchedVoice: info.matchedVoice ? `${info.matchedVoice.name} (${info.matchedVoice.lang})` : 'None',
          availableTeluguCount: info.availableTeluguVoices.length,
          availableHindiCount: info.availableHindiVoices.length,
          availableEnglishCount: info.availableEnglishVoices.length
        });
        console.log('[SpeechDiagnosticInfo]', info);
        return info;
      };
    }
  }

  private setState(state: AudioState) {
    this.currentState = state;
    if (this.onStateChangeCallback) {
      this.onStateChangeCallback(state);
    }
  }

  public speak(options: SpeakOptions): void {
    if (!this.isSupported()) {
      if (options.onStateChange) options.onStateChange('ERROR');
      return;
    }

    // Cancel any active playback across the app
    this.stop();

    const cleanedText = cleanTextForSpeech(options.text);
    if (!cleanedText) {
      if (options.onStateChange) options.onStateChange('IDLE');
      return;
    }

    // Resolve target application language using robust detection precedence
    const targetLang = this.detectLanguage(options.text, options.language);
    const diagnostic = this.getDiagnosticInfo(options.text, options.language);

    if (!diagnostic.isVoiceAvailable && (targetLang === 'te' || targetLang === 'hi')) {
      console.warn(`[WebSpeechService] ${diagnostic.diagnosticMessage}`);
      if (options.onStateChange) options.onStateChange('ERROR');
      this.currentState = 'IDLE';
      return;
    }

    this.currentMode = options.mode || 'NORMAL_RESPONSE';
    this.currentId = options.id || '';
    this.onStateChangeCallback = options.onStateChange || null;

    const utterance = new SpeechSynthesisUtterance(cleanedText);
    this.currentUtterance = utterance;

    utterance.lang = diagnostic.requestedLocale;
    utterance.rate = options.rate !== undefined ? options.rate : 0.95;
    utterance.pitch = options.pitch !== undefined ? options.pitch : 1.0;

    const matchedVoice = this.findMatchingVoice(targetLang);
    if (matchedVoice) {
      utterance.voice = matchedVoice;
      utterance.lang = matchedVoice.lang || diagnostic.requestedLocale;
    }

    utterance.onstart = () => {
      this.setState('PLAYING');
    };

    utterance.onpause = () => {
      this.setState('PAUSED');
    };

    utterance.onresume = () => {
      this.setState('PLAYING');
    };

    utterance.onend = () => {
      this.setState('COMPLETED');
      this.currentState = 'IDLE';
    };

    utterance.onerror = (e) => {
      if (e.error === 'canceled' || e.error === 'interrupted') {
        this.setState('STOPPED');
        this.currentState = 'IDLE';
      } else {
        console.warn('[WebSpeechService] SpeechSynthesis error:', e);
        this.setState('ERROR');
        this.currentState = 'IDLE';
      }
    };

    this.setState('PLAYING');
    window.speechSynthesis.speak(utterance);
  }

  public pause(): void {
    if (!this.isSupported()) return;
    if (window.speechSynthesis.speaking && !window.speechSynthesis.paused) {
      window.speechSynthesis.pause();
      this.setState('PAUSED');
    }
  }

  public resume(): void {
    if (!this.isSupported()) return;
    if (window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
      this.setState('PLAYING');
    }
  }

  public stop(): void {
    if (!this.isSupported()) return;
    if (window.speechSynthesis.speaking || window.speechSynthesis.pending || window.speechSynthesis.paused) {
      window.speechSynthesis.cancel();
    }
    this.currentUtterance = null;
    this.setState('STOPPED');
    this.currentState = 'IDLE';
  }
}





