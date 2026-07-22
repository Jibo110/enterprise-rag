"use client";

import { useState, useCallback } from "react";
import FileUpload from "./components/FileUpload";
import ChatWindow from "./components/ChatWindow";

interface Source {
  name: string;
  page: number | null;
  doc_id: string;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  isStreaming?: boolean;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [hasDocuments, setHasDocuments] = useState(false);

  const handleUploadSuccess = useCallback((filename: string) => {
    setHasDocuments(true);
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        role: "assistant",
        content: `✅ **${filename}** uploaded and indexed. You can now ask questions about it.`,
      },
    ]);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    const assistantId = (Date.now() + 1).toString();
    setMessages((prev) => [
      ...prev,
      {
        id: assistantId,
        role: "assistant",
        content: "",
        isStreaming: true,
      },
    ]);

    try {
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: input.trim(),
          namespace: 'default',
        }),
      })

      const data = await response.json()

      setMessages(prev => prev.map(msg =>
        msg.id === assistantId
          ? { ...msg, content: data.answer, sources: data.sources, isStreaming: false }
          : msg
      ))
    } catch (err) {
      setMessages(prev => prev.map(msg =>
        msg.id === assistantId
          ? { ...msg, content: 'Something went wrong. Please try again.', isStreaming: false }
          : msg
      ))
    } finally {
      setIsLoading(false)
    }

  return (
    <div className="flex h-screen bg-gray-50">
      <div className="w-80 border-r border-gray-200 bg-white p-4 flex flex-col gap-4">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Enterprise RAG</h1>
          <p className="text-xs text-gray-400 mt-1">
            Document Q&A with citations
          </p>
        </div>
        <FileUpload
          onUploadSuccess={handleUploadSuccess}
          isUploading={isUploading}
          setIsUploading={setIsUploading}
        />
        {!hasDocuments && (
          <p className="text-xs text-gray-400 text-center">
            Upload a PDF to get started
          </p>
        )}
      </div>

      <div className="flex-1 flex flex-col">
        <div className="border-b border-gray-200 bg-white px-6 py-4">
          <h2 className="font-medium text-gray-700">
            Chat with your documents
          </h2>
        </div>

        <ChatWindow messages={messages} isLoading={isLoading} />

        <div className="border-t border-gray-200 bg-white p-4">
          <form onSubmit={handleSubmit} className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={
                hasDocuments
                  ? "Ask a question about your documents..."
                  : "Upload a document first..."
              }
              disabled={!hasDocuments || isLoading}
              className="flex-1 border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-blue-400 disabled:bg-gray-50 disabled:text-gray-400"
            />
            <button
              type="submit"
              disabled={!hasDocuments || isLoading || !input.trim()}
              className="bg-blue-600 text-white rounded-xl px-5 py-3 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
