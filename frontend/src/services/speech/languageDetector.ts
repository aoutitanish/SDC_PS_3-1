export type SupportedLanguage = "en" | "te" | "hi";

export function detectLanguage(
  text: string,
  fallbackLang: SupportedLanguage = "en"
): SupportedLanguage {
  if (!text) return fallbackLang;

  if (/[\u0C00-\u0C7F]/.test(text)) return "te";
  if (/[\u0900-\u097F]/.test(text)) return "hi";

  return fallbackLang;
}

export function detectTextLanguage(text: string): SupportedLanguage {
  return detectLanguage(text);
}

export function normalizeLanguage(language?: string): SupportedLanguage {
  const lang = (language || "en").toLowerCase();

  if (lang.startsWith("te")) return "te";
  if (lang.startsWith("hi")) return "hi";

  return "en";
}

export function getSpeechLocale(language?: string): string {
  switch (normalizeLanguage(language)) {
    case "te":
      return "te-IN";
    case "hi":
      return "hi-IN";
    default:
      return "en-IN";
  }
}

export function cleanTextForSpeech(text: string): string {
  return text
    .replace(/[*#_`]/g, "")
    .replace(/https?:\/\/\S+/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

export function cleanSpeechText(text: string): string {
  return cleanTextForSpeech(text);
}
