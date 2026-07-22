"use client";

interface Source {
  name: string;
  page: number | null;
  doc_id: string;
}

interface SourceCardProps {
  sources: Source[];
}

export default function SourceCard({ sources }: SourceCardProps) {
  if (sources.length === 0) return null;

  return (
    <div className="mt-2 p-3 bg-gray-50 rounded-lg border border-gray-100">
      <p className="text-xs font-medium text-gray-500 mb-2">Sources</p>
      <div className="flex flex-wrap gap-2">
        {sources.map((source, index) => (
          <span
            key={index}
            className="inline-flex items-center gap-1 text-xs bg-white text-gray-600 border border-gray-200 rounded-full px-3 py-1"
          >
            📄 {source.name}
            {source.page ? `, Page ${source.page}` : ""}
          </span>
        ))}
      </div>
    </div>
  );
}
