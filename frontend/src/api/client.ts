const DEV = window.location.port === "5173";
const API_BASE = DEV ? "http://127.0.0.1:8000" : "";

export interface LanguageMap {
  [code: string]: string;
}

export interface VoiceInfo {
  backend: string;
  name: string;
}

export interface VoiceMap {
  [name: string]: VoiceInfo;
}

export interface GenerateResponse {
  job_id: string;
}

export interface StatusResponse {
  status: string;
  progress: number;
  message: string;
}

export async function fetchLanguages(): Promise<LanguageMap> {
  const res = await fetch(`${API_BASE}/languages`);
  if (!res.ok) throw new Error("Failed to load languages");
  return res.json();
}

export async function fetchVoices(language: string): Promise<VoiceMap> {
  const res = await fetch(`${API_BASE}/voices?language=${language}`);
  if (!res.ok) throw new Error("Failed to load voices");
  return res.json();
}

export async function startGeneration(
  url: string,
  language: string,
  voice: string
): Promise<GenerateResponse> {
  const res = await fetch(`${API_BASE}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, language, voice }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Generation failed");
  }
  return res.json();
}

export async function checkStatus(
  jobId: string
): Promise<StatusResponse> {
  const res = await fetch(`${API_BASE}/status/${jobId}`);
  if (!res.ok) throw new Error("Failed to check status");
  return res.json();
}

export function getDownloadUrl(jobId: string): string {
  return `${API_BASE}/download/${jobId}`;
}
