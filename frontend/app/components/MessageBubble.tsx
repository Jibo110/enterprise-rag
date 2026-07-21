"use client";

import ReactMarkdown from "react-markdown";

interface Source {
  name: string;
  page: number | null;
  doc_id: string;
}

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  isStreaming?: boolean;
}

export default function MessageBubble({
  role,
  content,
  sources,
  isStreaming,
}: MessageBubbleProps) {
  const isUser = role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div className={`max-w-[80%] ${isUser ? "order-2" : "order-1"}`}>
        {!isUser && (
          <p className="text-xs text-gray-400 mb-1 ml-1">AI Assistant</p>
        )}

        <div
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? "bg-blue-600 text-white rounded-tr-sm"
              : "bg-white border border-gray-200 text-gray-800 rounded-tl-sm"
          }`}
        >
          {isUser ? (
            <p className="text-sm">{content}</p>
          ) : (
            <div className="text-sm prose prose-sm max-w-none">
              <ReactMarkdown>{content}</ReactMarkdown>
              {isStreaming && (
                <span className="inline-block w-2 h-4 bg-gray-400 animate-pulse ml-1" />
              )}
            </div>
          )}
        </div>

        {sources && sources.length > 0 && (
          <div className="mt-2 ml-1 flex flex-wrap gap-2">
            {sources.map((source, index) => (
              <span
                key={index}
                className="inline-flex items-center gap-1 text-xs bg-blue-50 text-blue-600 border border-blue-100 rounded-full px-3 py-1"
              >
                📄 {source.name}
                {source.page ? `, p.${source.page}` : ""}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
