import { useState } from "react";

interface URLInputProps {
  onSubmit: (url: string, language: string, voice: string) => void;
  disabled: boolean;
}

const LANGUAGES: Record<string, string> = {
  en: "English",
  ar: "Arabic",
  he: "Hebrew",
};

const DEFAULT_VOICES: Record<string, string> = {
  en: "en-US-JennyNeural",
  ar: "ar-EG-SalmaNeural",
  he: "he-IL-HilaNeural",
};

export default function URLInput({ onSubmit, disabled }: URLInputProps) {
  const [url, setUrl] = useState("");
  const [language, setLanguage] = useState("en");
  const [voice, setVoice] = useState(DEFAULT_VOICES["en"]);
  const [voices, setVoices] = useState<Record<string, { backend: string; name: string }>>({});

  const handleLanguageChange = async (lang: string) => {
    setLanguage(lang);
    setVoice(DEFAULT_VOICES[lang]);
    try {
      const res = await fetch(`/api/voices?language=${lang}`);
      if (res.ok) {
        const data = await res.json();
        setVoices(data);
        const keys = Object.keys(data);
        if (keys.length > 0) setVoice(keys[0]);
      }
    } catch {
      // fallback
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url.trim()) onSubmit(url.trim(), language, voice);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1.5">
          YouTube URL
        </label>
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://www.youtube.com/watch?v=..."
          className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
          disabled={disabled}
        />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1.5">
            Language
          </label>
          <select
            value={language}
            onChange={(e) => handleLanguageChange(e.target.value)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
            disabled={disabled}
          >
            {Object.entries(LANGUAGES).map(([code, name]) => (
              <option key={code} value={code}>
                {name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1.5">
            Voice
          </label>
          <select
            value={voice}
            onChange={(e) => setVoice(e.target.value)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
            disabled={disabled}
          >
            {Object.keys(voices).length === 0
              ? Object.entries(DEFAULT_VOICES)
                  .filter(([langCode]) => langCode === language)
                  .map(([_, v]) => (
                    <option key={v} value={v}>
                      {v}
                    </option>
                  ))
              : Object.entries(voices).map(([name, info]) => (
                  <option key={name} value={name}>
                    {name} ({info.backend})
                  </option>
                ))}
          </select>
        </div>
      </div>

      <button
        type="submit"
        disabled={disabled || !url.trim()}
        className="w-full py-3 px-6 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 text-white font-medium rounded-lg transition cursor-pointer disabled:cursor-not-allowed"
      >
        {disabled ? "Processing..." : "Generate Audiobook"}
      </button>
    </form>
  );
}
