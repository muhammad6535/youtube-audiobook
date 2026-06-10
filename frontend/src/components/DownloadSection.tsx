import { getDownloadUrl } from "../api/client";

interface DownloadSectionProps {
  jobId: string;
}

export default function DownloadSection({ jobId }: DownloadSectionProps) {
  const downloadUrl = getDownloadUrl(jobId);

  return (
    <div className="text-center space-y-4 p-6 bg-gray-800/50 rounded-lg border border-green-800/30">
      <div className="text-green-400 text-lg font-medium">
        Audiobook Ready!
      </div>

      <audio controls className="w-full max-w-md mx-auto">
        <source src={downloadUrl} type="audio/mpeg" />
      </audio>

      <a
        href={downloadUrl}
        download
        className="inline-block px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-medium rounded-lg transition cursor-pointer"
      >
        Download MP3
      </a>
    </div>
  );
}
