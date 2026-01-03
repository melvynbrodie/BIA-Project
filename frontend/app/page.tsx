"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, FileText, Send, Sparkles, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

import { MetricsCharts } from "@/components/MetricsCharts";
import { CompanyProfile } from "@/components/CompanyProfile";
import { NewsSection } from "@/components/NewsSection";


const COMPANIES = ["TCS", "Infosys", "Wipro", "HCL Tech", "Tech Mahindra", "Adani Enterprises", "Reliance", "Tata Motors", "Maruti Suzuki", "L&T"];

function ProgressCounter({ value }: { value: number }) {
  return (
    <div className="flex justify-between text-xs text-gray-400">
      <span>Processing Annual Report...</span>
      <span>{Math.floor(value)}%</span>
    </div>
  )
}


export default function Home() {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [companyId, setCompanyId] = useState("TCS");
  const [question, setQuestion] = useState("");
  const [chatHistory, setChatHistory] = useState<{ role: 'user' | 'agent', content: any }[]>([]);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [isPolling, setIsPolling] = useState(false);
  const [progress, setProgress] = useState(0);


  const [showDashboard, setShowDashboard] = useState(false);

  // Drag Handlers
  const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = (e: React.DragEvent) => { e.preventDefault(); setIsDragging(false); };
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0]);
  };

  const onProgressComplete = () => {
    setShowDashboard(true);
    setUploading(false);
    setUploadSuccess(false);
    setIsPolling(false);
    setProgress(0);
  };

  // Progress Simulation Effect
  useEffect(() => {
    if (!uploading) return;

    // Normal slow progress up to 95%
    if (!uploadSuccess) {
      const timer = setInterval(() => {
        setProgress(old => {
          if (old >= 95) return 95; // Wait here
          const increment = old > 80 ? 0.2 : 0.5; // Asymptotic
          return Math.min(95, old + increment);
        })
      }, 100);
      return () => clearInterval(timer);
    }
  }, [uploading, uploadSuccess]);

  // Completion Effect
  useEffect(() => {
    if (uploadSuccess) {
      const finishTimer = setInterval(() => {
        setProgress(old => {
          if (old >= 100) {
            clearInterval(finishTimer);
            setTimeout(onProgressComplete, 500);
            return 100;
          }
          return old + 5; // Fast increment to finish
        });
      }, 50);
      return () => clearInterval(finishTimer);
    }
  }, [uploadSuccess]);

  // Polling Effect
  useEffect(() => {
    if (!isPolling || !companyId) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/v1/company/${companyId}/status`);
        const data = await res.json();
        console.log("Polling Status:", data.status);

        if (data.status === "ready") {
          clearInterval(interval);
          setIsPolling(false);
          setUploadSuccess(true); // Now trigger the smooth finish
          setRefreshTrigger(prev => prev + 1); // Refresh data
        }
      } catch (e) {
        console.error("Polling Error:", e);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [isPolling, companyId]);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setUploadSuccess(false);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("company_id", companyId); // In real app, extracting from file is better
    formData.append("period", "FY25");

    try {
      const res = await fetch("http://localhost:8000/api/v1/upload", { method: "POST", body: formData });
      if (res.ok) {
        const data = await res.json();
        console.log("Detected Company:", data.company_id);
        if (data.company_id) setCompanyId(data.company_id);

        if (data.company_id) setCompanyId(data.company_id);

        // setRefreshTrigger(prev => prev + 1);
        // Start polling instead of immediate success
        setIsPolling(true);
      }
      else {
        alert("Upload failed.");
        setUploading(false);
      }
    } catch (e) {
      console.error(e);
      alert("Error connecting to server.");
      setUploading(false);
    }
    // finally { setUploading(false); } // Moved to onComplete
  };

  const handleAsk = async () => {
    if (!question) return;
    const currentQ = question;
    setQuestion("");
    setChatHistory(prev => [...prev, { role: 'user', content: currentQ }]);
    setLoadingAnalysis(true);

    try {
      const res = await fetch("http://localhost:8000/api/v1/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_id: companyId,
          question: currentQ
        })
      });

      if (!res.ok) {
        throw new Error(`Server error: ${res.status}`);
      }

      const data = await res.json();
      setChatHistory(prev => [...prev, { role: 'agent', content: data }]);
    } catch (e) {
      console.error(e);
      setChatHistory(prev => [...prev, {
        role: 'agent',
        content: { final_analysis: "⚠️ I encountered an error while analyzing the document. Please try asking again." }
      }]);
    }
    finally { setLoadingAnalysis(false); }
  };

  return (
    <main className="min-h-screen bg-[#050505] text-white p-6 md:p-12 font-sans selection:bg-blue-500/30 overflow-x-hidden">
      <div className="max-w-[1600px] mx-auto space-y-12">

        {/* Header */}
        <section className="pt-8 flex flex-col items-center text-center space-y-4">
          <motion.h1
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="text-4xl md:text-6xl font-bold tracking-tight text-white bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-500"
          >
            AI Financial Analyst
          </motion.h1>
          <p className="text-gray-500 font-medium max-w-2xl">
            Upload an Annual Report (PDF) to instantly analyze financial trends, key ratios, and chat with the document.
          </p>
        </section>

        {/* Upload Section (Always Visible if no dashboard, or minimized?) - Let's keep it visible but primary */}
        {!showDashboard ? (
          <motion.section
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="max-w-2xl mx-auto glass-card rounded-[2rem] p-8 border border-white/5 bg-[#121212]/50"
          >
            <div className="flex flex-col items-center gap-6">
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={cn(
                  "w-full border-2 border-dashed rounded-2xl h-48 flex flex-col items-center justify-center transition-all cursor-pointer bg-white/5 relative",
                  isDragging ? "border-blue-500 bg-blue-500/10" : "border-white/10 hover:border-white/20 hover:bg-white/10",
                  file ? "border-green-500/50 bg-green-500/5" : ""
                )}
              >
                {file ? (
                  <div className="flex flex-col items-center gap-2 text-green-400">
                    <FileText size={48} />
                    <span className="text-lg font-medium">{file.name}</span>
                    <span className="text-xs text-gray-400">Ready to process</span>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-3 text-gray-500">
                    <Upload size={48} />
                    <span className="text-lg font-medium">Drag & Drop Annual Report (PDF)</span>
                    <span className="text-sm">or click to browse</span>
                  </div>
                )}
                <input type="file" className="hidden" onChange={(e) => e.target.files && setFile(e.target.files[0])} id="file-upload" />
                <label htmlFor="file-upload" className="absolute inset-0 cursor-pointer" />
              </div>

              <div className="w-full">
                {uploading ? (
                  <div className="w-full space-y-2">
                    <ProgressCounter value={progress} />
                    {/* Fake progress bar since we don't have real-time socket progress yet */}
                    <div className="h-2 w-full bg-white/10 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: "0%" }}
                        animate={{ width: `${progress}%` }}
                        transition={{ duration: 0.1, ease: "linear" }}
                        className="h-full bg-blue-500 rounded-full"
                      />
                    </div>
                    <p className="text-center text-xs text-gray-500 mt-2">Extracting Financial Data & Training Chatbot</p>
                  </div>
                ) : (
                  <button
                    onClick={handleUpload}
                    disabled={!file}
                    className="w-full bg-white text-black font-bold text-lg px-8 py-4 rounded-xl hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    <Sparkles size={20} /> Generate Analysis Dashboard
                  </button>
                )}
              </div>
            </div>
          </motion.section>
        ) : (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-12">

            {/* Top Grid: Profile + Chat */}
            <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
              {/* Left: Profile (5 cols) */}
              <div className="xl:col-span-5 h-full">
                <CompanyProfile companyId={companyId} />
              </div>

              {/* Right: Chat (7 cols) */}
              <div className="xl:col-span-7 h-full">
                <div className="glass-card rounded-[2rem] p-8 flex flex-col h-[600px] border border-white/5 bg-[#121212]/50 backdrop-blur-2xl relative overflow-hidden">
                  <div className="flex items-center gap-3 mb-6 z-10">
                    <Sparkles className="text-yellow-400" size={24} />
                    <div>
                      <h2 className="text-2xl font-bold text-white">Analysis Assistant</h2>
                      <p className="text-xs text-gray-400">Ask questions based on the uploaded PDF</p>
                    </div>
                  </div>

                  <div className="flex-1 overflow-y-auto space-y-6 pr-2 custom-scrollbar z-10">
                    {chatHistory.length === 0 && (
                      <div className="h-full flex flex-col items-center justify-center text-gray-600 gap-4">
                        <p>The annual report has been processed.</p>
                        <p>Ask specifically about risks, future outlook, or segment performance.</p>
                      </div>
                    )}
                    {chatHistory.map((msg, i) => (
                      <div key={i} className={cn("flex flex-col gap-2 max-w-[90%]", msg.role === 'user' ? "ml-auto items-end" : "items-start")}>
                        <div className={cn("p-4 rounded-2xl text-sm leading-relaxed", msg.role === 'user' ? "bg-blue-600 text-white" : "bg-[#1A1A1A] text-gray-200")}>
                          {msg.role === 'user' ? msg.content : (
                            <div className="whitespace-pre-wrap">{msg.content.final_analysis || msg.content.answer || msg.content.analysis}</div>
                          )}
                        </div>
                      </div>
                    ))}

                    {/* Thinking Indicator */}
                    {loadingAnalysis && (
                      <div className="flex flex-col gap-2 max-w-[90%] items-start">
                        <div className="p-4 rounded-2xl text-sm bg-[#1A1A1A] text-gray-400 flex items-center gap-2">
                          <Sparkles size={14} className="animate-spin text-yellow-400" />
                          <span className="animate-pulse">Thinking...</span>
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="mt-6 pt-4 border-t border-white/5 z-10 relative">
                    <input
                      type="text"
                      placeholder="Type your question..."
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
                      className="w-full bg-[#0A0A0A] border border-white/10 rounded-xl pl-5 pr-14 py-4 focus:outline-none focus:ring-1 focus:ring-white/20 transition-all placeholder:text-gray-700"
                    />
                    <button
                      onClick={handleAsk}
                      disabled={!question || loadingAnalysis}
                      className="absolute right-2 top-6 bg-white text-black p-2 rounded-lg hover:bg-gray-200"
                    >
                      <Send size={18} />
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Middle: Charts */}
            <section className="space-y-8">
              <div className="flex items-center gap-4">
                <h2 className="text-3xl font-bold text-white">Financial Trends</h2>
                <div className="h-px flex-1 bg-gradient-to-r from-white/10 to-transparent" />
              </div>
              <MetricsCharts companyName={companyId} refreshKey={refreshTrigger} />
            </section>

            {/* News Section */}
            <NewsSection companyName={companyId} />

          </motion.div>
        )}

      </div>
    </main>
  );
}
