
"use client";

import { useState, useEffect } from 'react';
import { Building2, Globe, Users, Briefcase, TrendingUp, DollarSign } from 'lucide-react';

interface ProfileData {
    name: string;
    ticker: string;
    description: string;
    industry: string;
    sector: string;
    website: string;
    employees: number | string;
    founded?: string;
    market_cap: number;
    current_price: number;
    currency: string;
}

export function CompanyProfile({ companyId }: { companyId: string }) {
    const [profile, setProfile] = useState<ProfileData | null>(null);

    useEffect(() => {
        const fetchProfile = async () => {
            try {
                const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, "");
                const res = await fetch(`${API_BASE_URL}/api/v1/company/${companyId}/metrics`);
                const data = await res.json();
                if (data.profile) setProfile(data.profile);
            } catch (e) {
                console.error("Profile Fetch Error:", e);
            }
        };
        if (companyId) fetchProfile();
    }, [companyId]);

    if (!profile) return <div className="glass-card p-8 h-full animate-pulse bg-white/5" />;

    // Format Market Cap
    const formatMarketCap = (cap: number) => {
        if (cap > 1e12) return `₹${(cap / 1e12).toFixed(1)} Trillion`;
        if (cap > 1e9) return `₹${(cap / 1e9).toFixed(1)} Billion`; // Or Crores preference
        if (cap > 1e7) return `₹${(cap / 1e7).toFixed(1)} Cr`;
        return `₹${cap.toLocaleString()}`;
    };

    // Construct "Key Facts" narrative dynamically
    // Use extracted summary if available, else fallback to a cleaner constructed string
    const keyFacts = (profile as any).extracted_summary || `${profile.name} is a leading player in the ${profile.industry} industry, significantly contributing to the ${profile.sector} sector. With a strong market presence, ${profile.name} continues to expand its global footprint and drive innovation.`;

    return (
        <div className="glass-card p-6 lg:p-8 rounded-3xl space-y-6 h-full border border-white/5 bg-black/40 backdrop-blur-xl flex flex-col justify-between">
            {/* Header */}
            <div className="flex items-center gap-4 border-b border-white/10 pb-6">
                <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center text-2xl font-bold text-white shadow-lg shadow-blue-500/20">
                    {profile.ticker?.[0] || "C"}
                </div>
                <div>
                    <h2 className="text-2xl font-bold text-white tracking-tight">{profile.name}</h2>
                    <span className="text-gray-400 text-sm font-medium bg-white/5 px-2 py-0.5 rounded-md">{profile.ticker}</span>
                </div>
            </div>

            {/* 1. Company Overview */}
            <div className="space-y-2">
                <h3 className="text-sm font-semibold text-blue-400 uppercase tracking-wider">Company Overview</h3>
                <p className="text-gray-300 text-sm leading-relaxed line-clamp-4">
                    {profile.description}
                </p>
            </div>

            {/* 2. Key Facts */}
            <div className="space-y-2">
                <h3 className="text-sm font-semibold text-blue-400 uppercase tracking-wider">Key Facts</h3>
                <p className="text-gray-400 text-sm leading-relaxed border-l-2 border-blue-500/30 pl-3 italic">
                    {keyFacts}
                </p>
            </div>

            {/* 3. Market Data Table */}
            <div className="bg-white/5 rounded-xl p-4 border border-white/5">
                <div className="grid grid-cols-2 gap-4 divide-x divide-white/10">
                    <div className="text-center space-y-1">
                        <div className="text-gray-500 text-xs uppercase font-medium">Market Cap</div>
                        <div className="text-white font-bold text-lg">{formatMarketCap(profile.market_cap)}</div>
                    </div>
                    <div className="text-center space-y-1 pl-4">
                        <div className="text-gray-500 text-xs uppercase font-medium">Share Price</div>
                        <div className="text-white font-bold text-lg text-green-400">
                            ₹{profile.current_price.toLocaleString('en-IN', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}
                        </div>
                    </div>
                </div>
            </div>

            {/* Extra Metadata Grid */}
            <div className="flex flex-col gap-3 pt-2">
                <div className="grid grid-cols-2 gap-y-2 text-xs text-gray-500">
                    <div className="flex items-center gap-2"><Briefcase size={12} /> {profile.industry}</div>
                    <div className="flex items-center gap-2"><Users size={12} /> {Number(profile.employees).toLocaleString('en-IN')} Employees</div>
                </div>
                <div className="flex justify-end border-t border-white/5 pt-3">
                    <a href={`https://finance.yahoo.com/quote/${profile.ticker}`} target="_blank" rel="noreferrer" className="text-[10px] text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors">
                        Source: Yahoo Finance ↗
                    </a>
                </div>
            </div>
        </div>
    );
}
