import { useState, useRef, useCallback } from "react";
import URLInput from "./components/URLInput";
import ProgressBar from "./components/ProgressBar";
import DownloadSection from "./components/DownloadSection";
import { startGeneration, checkStatus } from "./api/client";
import "./index.css";

export default function App() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState<"idle" | "processing" | "completed" | "error">("idle");
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  const handleSubmit = async (url: string, language: string, voice: string) => {
    setStatus("processing");
    setProgress(0);
    setMessage("Starting...");
    setJobId(null);

    try {
      const { job_id } = await startGeneration(url, language, voice);
      setJobId(job_id);

      pollingRef.current = setInterval(async () => {
        try {
          const result = await checkStatus(job_id);
          setProgress(result.progress);
          setMessage(result.message);

          if (result.status === "completed") {
            setStatus("completed");
            setProgress(100);
            setMessage("Done");
            stopPolling();
          } else if (result.status === "error") {
            setStatus("error");
            stopPolling();
          }
        } catch {
          setStatus("error");
          setMessage("Connection lost");
          stopPolling();
        }
      }, 1000);
    } catch (err: any) {
      setStatus("error");
      setMessage(err.message || "Failed to start");
    }
  };

  const handleReset = () => {
    stopPolling();
    setStatus("idle");
    setProgress(0);
    setMessage("");
    setJobId(null);
  };

  const isProcessing = status === "processing";

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-gray-800 py-6">
        <div className="max-w-2xl mx-auto px-4">
          <h1 className="text-2xl font-bold text-white">
            YouTube Audiobook Generator
          </h1>
          <p className="text-gray-400 mt-1 text-sm">
            Paste a YouTube URL and get a professional audiobook in Arabic, English, or Hebrew
          </p>
        </div>
      </header>

      <main className="flex-1 max-w-2xl mx-auto w-full px-4 py-10">
        <div className="space-y-8">
          <URLInput onSubmit={handleSubmit} disabled={isProcessing} />

          {status !== "idle" && (
            <ProgressBar
              progress={progress}
              message={message}
              status={status}
            />
          )}

          {status === "completed" && jobId && (
            <DownloadSection jobId={jobId} />
          )}

          {(status === "completed" || status === "error") && (
            <button
              onClick={handleReset}
              className="w-full py-2 px-4 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition cursor-pointer"
            >
              Start Over
            </button>
          )}
        </div>
      </main>

      <footer className="border-t border-gray-800 py-4 text-center text-gray-600 text-xs">
        Built with open-source TTS &middot; YouTube Transcript API &middot; FastAPI &middot; React
      </footer>
    </div>
  );
}
