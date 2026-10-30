import { ISpeechService } from './types';
import { WebSpeechService } from './WebSpeechService';

export * from './types';
export * from './languageDetector';
export { WebSpeechService };

/**
 * Global application speech service singleton instance.
 * For web platform, uses WebSpeechService.
 * When migrating to mobile (React Native/Capacitor), replace this instance
 * with MobileSpeechService without modifying ChatMessage, ChatContext, or UI components.
 */
export const speechService: ISpeechService = new WebSpeechService();
