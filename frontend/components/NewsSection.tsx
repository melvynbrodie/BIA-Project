
"use client";

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Newspaper, ExternalLink, Clock } from 'lucide-react';

export function NewsSection({ companyName }: { companyName: string }) {
    const [news, setNews] = useState<any[]>([]);

    useEffect(() => {
        const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, "");
        fetch(`${API_BASE_URL}/api/v1/company/${companyName}/news`)
            .then(res => res.json())
            .then(setNews)
            .catch(console.error);
    }, [companyName]);

    if (!news || news.length === 0) return null;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
        >
            <div className="flex items-center gap-3 mb-4">
                <div className="h-8 w-1 bg-blue-500 rounded-full" />
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                    <Newspaper size={24} className="text-blue-400" /> Latest Financial News
                </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {news.map((item, idx) => (
                    <motion.a
                        key={idx}
                        href={item.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        whileHover={{ scale: 1.02 }}
                        className="glass-card p-5 rounded-2xl border border-white/5 bg-[#121212]/50 hover:bg-[#1A1A1A] transition-all group"
                    >
                        <div className="flex flex-col h-full justify-between">
                            <div>
                                <div className="flex justify-between items-start gap-4 mb-2">
                                    <span className="text-xs font-semibold text-blue-400 bg-blue-400/10 px-2 py-1 rounded-md">
                                        {item.publisher}
                                    </span>
                                    <ExternalLink size={14} className="text-gray-600 group-hover:text-blue-400 transition-colors" />
                                </div>
                                <h3 className="text-white font-medium leading-relaxed group-hover:text-blue-100 transition-colors">
                                    {item.title}
                                </h3>
                            </div>

                            <div className="mt-4 pt-3 border-t border-white/5 flex items-center text-xs text-gray-500 gap-1">
                                <Clock size={12} />
                                <span>
                                    {item.time
                                        ? new Date(item.time * 1000).toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })
                                        : 'Recent'}
                                </span>
                            </div>
                        </div>
                    </motion.a>
                ))}
            </div>
        </motion.div>
    );
}
