interface ProgressBarProps {
  progress: number;
  message: string;
  status: string;
}

export default function ProgressBar({
  progress,
  message,
  status,
}: ProgressBarProps) {
  const isError = status === "error";
  const isDone = status === "completed";

  return (
    <div className="space-y-3">
      <div className="flex justify-between text-sm text-gray-400">
        <span>{message}</span>
        <span>{progress}%</span>
      </div>

      <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 ease-out ${
            isError
              ? "bg-red-500"
              : isDone
              ? "bg-green-500"
              : "bg-blue-500"
          }`}
          style={{ width: `${progress}%` }}
        />
      </div>

      {isError && (
        <p className="text-red-400 text-sm">Generation failed. Try again.</p>
      )}
    </div>
  );
}
