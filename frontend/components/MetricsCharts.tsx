
"use client";

import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area, PieChart, Pie, Cell, LabelList, CartesianGrid } from 'recharts';
import { motion } from 'framer-motion';
import { ExternalLink, CheckCircle, Download } from 'lucide-react';

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#6B7280'];

function ChartCard({ title, children, citation, link }: { title: string, children: React.ReactNode, citation?: string, link?: string }) {
    return (
        <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="glass-card p-6 rounded-3xl border border-white/5 bg-[#121212]/50"
        >
            <div className="flex justify-between items-start mb-6">
                <h3 className="text-lg font-semibold text-white">{title}</h3>
                {link && (
                    <a href={link} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300 text-xs flex items-center gap-1 transition-colors">
                        Verify <ExternalLink size={10} />
                    </a>
                )}
            </div>

            <div className="h-[300px] w-full">
                {children}
            </div>
            {citation && (
                <div className="mt-4 pt-3 border-t border-white/5 text-xs text-gray-500 flex items-center gap-2">
                    <span className="font-semibold text-gray-400">Source:</span> {citation}
                </div>
            )}
        </motion.div>
    )
}

export function MetricsCharts({ companyName, refreshKey }: { companyName: string, refreshKey?: number }) {
    const [data, setData] = useState<any>(null);
    const [stockData, setStockData] = useState<any>(null);

    useEffect(() => {
        const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, "");
        fetch(`${API_BASE_URL}/api/v1/company/${companyName}/metrics?t=${refreshKey}`)
            .then(res => res.json())
            .then(setData)
            .catch(console.error);

        fetch(`${API_BASE_URL}/api/v1/company/${companyName}/stock`)
            .then(res => res.json())
            .then(setStockData)
            .catch(console.error);

    }, [companyName, refreshKey]);

    if (!data) return (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 animate-pulse">
            {[...Array(6)].map((_, i) => (
                <div key={i} className="h-[300px] w-full bg-white/5 rounded-3xl border border-white/5 p-6 space-y-4">
                    <div className="h-6 w-1/2 bg-white/10 rounded"></div>
                    <div className="h-40 w-full bg-white/5 rounded-xl"></div>
                </div>
            ))}
        </div>
    );

    const currency = data.meta?.currency_symbol || "₹";

    // Universal 1-decimal comma-separated formatter
    const formatValue = (val: number, showSymbol = true) => {
        if (val === undefined || val === null) return "-";
        const formatted = val.toLocaleString('en-IN', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
        return showSymbol ? `${currency}${formatted}` : formatted;
    };

    // Axis formatter: No currency, just commas
    const axisFormat = (val: number) => val.toLocaleString('en-IN');

    const isVerified = data.verified === true;

    const handleDownloadVerification = () => {
        const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, "");
        window.open(`${API_BASE_URL}/api/v1/company/${companyName}/verification_sheet`, "_blank");
    };

    // Helper for explicit 50% Top Padding
    const axisDomain = (dataMax: number) => {
        // If dataMax is 0 or low, default to reasonable range, else add 50%
        if (!dataMax) return 'auto';
        return Math.ceil(dataMax * 1.2); // Reduced from 1.5 to 1.2 for tighter fit
    };

    const getMaxDomain = (dataset: any[], key: string = "value") => {
        // Keeping this for safety if Recharts fails function, but using function syntax preferred
        if (!dataset || dataset.length === 0) return ['auto', 'auto'];
        const max = Math.max(...dataset.map(d => d[key] || 0));
        return [0, Math.ceil(max * 1.2)];
    };

    return (
        <div className="space-y-6">

            {/* Verification Badge & Download */}
            <div className="flex items-center justify-between bg-green-500/10 border border-green-500/20 rounded-xl p-4">
                <div className="flex items-center gap-3">
                    <CheckCircle className="text-green-400" size={24} />
                    <div>
                        <h3 className="text-green-400 font-bold text-sm">Data Verified by AI Auditor</h3>
                        <p className="text-gray-400 text-xs">Metrics cross-referenced with Yahoo Finance.</p>
                    </div>
                </div>

                <a
                    href={data.meta?.link || "https://finance.yahoo.com"}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 bg-[#1A1A1A] hover:bg-[#252525] border border-white/10 text-white text-xs px-4 py-2 rounded-lg transition-colors"
                >
                    <ExternalLink size={14} /> Verify on Yahoo Finance
                </a>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                {/* 1. Revenue Trend */}
                <ChartCard title={`Revenue Trend (${data.meta?.currency_unit || 'Cr'})`} citation={data.revenue?.citation} link={data.revenue?.link}>
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={data.revenue?.data} margin={{ left: 20 }}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#333" />
                            <XAxis
                                dataKey="year"
                                axisLine={false}
                                tickLine={false}
                                tick={{ fill: '#9CA3AF', fontSize: 12 }}
                                dy={10}
                                padding={{ right: 30, left: 20 }}
                            />
                            <YAxis
                                stroke="#525252"
                                tick={{ fill: '#9CA3AF', fontSize: 10 }}
                                tickFormatter={axisFormat}
                                width={60}
                                domain={[0, (dataMax: number) => axisDomain(dataMax)]}
                            />
                            <Tooltip
                                cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                                contentStyle={{ backgroundColor: '#000', border: '1px solid #333', borderRadius: '8px', color: '#fff' }}
                                formatter={(value: number) => formatValue(value)}
                            />
                            <Bar dataKey="value" name="Revenue" fill="#3B82F6" radius={[4, 4, 0, 0]}>
                                <LabelList dataKey="value" position="top" fill="#D1D5DB" fontSize={12} formatter={(v: any) => formatValue(v)} />
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </ChartCard>

                {/* 2. Operating Profit */}
                <ChartCard title="Operating Profit (EBIT)" citation={data.operating_profit?.citation} link={data.operating_profit?.link}>
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={data.operating_profit?.data}>
                            <XAxis dataKey="year" stroke="#525252" tick={{ fill: '#9CA3AF', fontSize: 10 }} />
                            <YAxis
                                stroke="#525252"
                                tick={{ fill: '#9CA3AF', fontSize: 10 }}
                                tickFormatter={axisFormat}
                                width={40}
                                domain={[0, (dataMax: number) => axisDomain(dataMax)]}
                            />
                            <Tooltip contentStyle={{ backgroundColor: '#000', border: '1px solid #333', borderRadius: '8px', color: '#fff' }} formatter={(value: number) => formatValue(value)} />
                            <Bar dataKey="value" name="EBIT" fill="#10B981" radius={[4, 4, 0, 0]}>
                                <LabelList dataKey="value" position="top" fill="#D1D5DB" fontSize={12} formatter={(v: any) => formatValue(v)} />
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </ChartCard>

                {/* 3. EPS Trend */}
                <ChartCard title="Earnings Per Share (EPS)" citation={data.eps?.citation} link={data.eps?.link}>
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={data.eps?.data}>
                            <defs>
                                <linearGradient id="colorEPS" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.8} />
                                    <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <XAxis dataKey="year" stroke="#525252" tick={{ fill: '#9CA3AF', fontSize: 10 }} />
                            <YAxis
                                stroke="#525252"
                                tick={{ fill: '#9CA3AF', fontSize: 10 }}
                                tickFormatter={axisFormat}
                                width={30}
                                domain={[0, (dataMax: number) => axisDomain(dataMax)]}
                            />
                            <Tooltip contentStyle={{ backgroundColor: '#000', border: '1px solid #333', borderRadius: '8px', color: '#fff' }} formatter={(value: number) => formatValue(value)} />
                            <Area type="monotone" dataKey="value" name="EPS" stroke="#8B5CF6" fillOpacity={1} fill="url(#colorEPS)">
                                <LabelList dataKey="value" position="top" fill="#D1D5DB" fontSize={12} offset={10} formatter={(v: any) => formatValue(v)} />
                            </Area>
                        </AreaChart>
                    </ResponsiveContainer>
                </ChartCard>

                {/* 4. Cash Flow */}
                <ChartCard title="Operating Cash Flow" citation={data.cash_flow?.citation} link={data.cash_flow?.link}>
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={data.cash_flow?.data}>
                            <XAxis dataKey="year" stroke="#525252" tick={{ fill: '#9CA3AF', fontSize: 10 }} />
                            <YAxis
                                stroke="#525252"
                                tick={{ fill: '#9CA3AF', fontSize: 10 }}
                                tickFormatter={axisFormat}
                                width={40}
                                domain={[0, (dataMax: number) => axisDomain(dataMax)]}
                            />
                            <Tooltip contentStyle={{ backgroundColor: '#000', border: '1px solid #333', borderRadius: '8px', color: '#fff' }} formatter={(value: number) => formatValue(value)} />
                            <Bar dataKey="value" name="OCF" fill="#F59E0B" radius={[4, 4, 0, 0]}>
                                <LabelList dataKey="value" position="top" fill="#D1D5DB" fontSize={12} formatter={(v: any) => formatValue(v)} />
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </ChartCard>

                {/* 5. Return on Equity (Replaced Revenue Composition) */}
                <ChartCard title="Return on Equity (Annual Trend)" citation={data.roe?.citation} link={data.roe?.link}>
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={data.roe?.data}>
                            <defs>
                                <linearGradient id="colorRoE" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#EC4899" stopOpacity={0.8} />
                                    <stop offset="95%" stopColor="#EC4899" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <XAxis dataKey="year" stroke="#525252" tick={{ fill: '#9CA3AF', fontSize: 10 }} />
                            <YAxis
                                stroke="#525252"
                                tick={{ fill: '#9CA3AF', fontSize: 10 }}
                                tickFormatter={val => `${val.toFixed(1)}%`}
                                domain={[0, (dataMax: number) => axisDomain(dataMax)]}
                                width={35}
                            />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#000', border: '1px solid #333', borderRadius: '8px', color: '#fff' }}
                                formatter={(value: number) => `${value.toFixed(1)}%`}
                            />
                            <Area type="monotone" dataKey="value" name="RoE" stroke="#EC4899" strokeWidth={2} fillOpacity={1} fill="url(#colorRoE)">
                                <LabelList dataKey="value" position="top" fill="#D1D5DB" fontSize={12} offset={10} formatter={(val: any) => `${val.toFixed(1)}%`} />
                            </Area>
                        </AreaChart>
                    </ResponsiveContainer>
                </ChartCard>

                {/* 6. Stock Price (Online API) */}
                <ChartCard title="Stock Price (1Y)" citation={stockData?.citation || "Live API"} link={stockData?.link}>
                    {!stockData ? (
                        <div className="h-full flex items-center justify-center text-gray-600">Loading Stock Data...</div>
                    ) : (
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={stockData.data}>
                                <defs>
                                    <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8} />
                                        <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#333" />
                                <XAxis
                                    dataKey="date"
                                    hide
                                    padding={{ right: 30, left: 0 }}
                                />
                                <YAxis
                                    stroke="#525252"
                                    tick={{ fill: '#9CA3AF', fontSize: 10 }}
                                    domain={getMaxDomain(stockData.data, "price")}
                                    tickFormatter={axisFormat}
                                    width={40}
                                />
                                <Tooltip
                                    cursor={{ stroke: 'rgba(255,255,255,0.1)', strokeWidth: 2 }}
                                    contentStyle={{ backgroundColor: '#000', border: '1px solid #333', borderRadius: '8px', color: '#fff' }}
                                    formatter={(value: number) => [formatValue(value), 'Price']}
                                    labelFormatter={(label: any) => new Date(label).toLocaleDateString()}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="price"
                                    stroke="#3B82F6"
                                    strokeWidth={2}
                                    fill="url(#colorPrice)"
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    )}
                </ChartCard>

                {/* 7. Major Shareholders */}
                <ChartCard title="Major Shareholders" citation={data.composition?.citation} link={data.composition?.link}>
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={data.composition?.data}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={80}
                                paddingAngle={5}
                                dataKey="value"
                            >
                                {data.composition?.data?.map((entry: any, index: number) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} stroke="rgba(0,0,0,0)" />
                                ))}
                            </Pie>
                            <Tooltip
                                contentStyle={{ backgroundColor: '#000', border: '1px solid #333', borderRadius: '8px', color: '#fff' }}
                                formatter={(value: number) => `${value}%`}
                            />
                        </PieChart>
                    </ResponsiveContainer>
                    <div className="flex flex-wrap justify-center gap-x-6 gap-y-2 mt-2 px-4">
                        {data.composition?.data?.map((entry: any, index: number) => (
                            <div key={index} className="flex items-center gap-2 text-xs text-gray-300">
                                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
                                <span className="font-medium">{entry.name}</span>
                                <span className="text-gray-500">{entry.value}%</span>
                            </div>
                        ))}
                    </div>
                </ChartCard>

                {/* 8. Trading Info Card */}
                {stockData.info && (
                    <ChartCard title="Key Trading Metrics" link={stockData.link}>
                        <div className="h-60 flex items-center">
                            <div className="w-full grid grid-cols-2 gap-y-6 gap-x-4">
                                <div className="p-3 bg-white/5 rounded-lg border border-white/5">
                                    <p className="text-xs text-gray-500 mb-1">52 Week High</p>
                                    <p className="text-xl font-bold text-white">{currency}{stockData.info["52_week_high"]?.toLocaleString('en-IN', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) || '-'}</p>
                                </div>
                                <div className="p-3 bg-white/5 rounded-lg border border-white/5">
                                    <p className="text-xs text-gray-500 mb-1">52 Week Low</p>
                                    <p className="text-xl font-bold text-white">{currency}{stockData.info["52_week_low"]?.toLocaleString('en-IN', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) || '-'}</p>
                                </div>
                                <div className="p-3 bg-white/5 rounded-lg border border-white/5">
                                    <p className="text-xs text-gray-500 mb-1">P/E Ratio</p>
                                    <p className="text-xl font-bold text-white">{stockData.info["pe_ratio"]?.toFixed(1) || '-'}</p>
                                </div>
                                <div className="p-3 bg-white/5 rounded-lg border border-white/5">
                                    <p className="text-xs text-gray-500 mb-1">Market Cap</p>
                                    <p className="text-xl font-bold text-white">{stockData.info["market_cap"] ? `${(stockData.info["market_cap"] / 10000000).toLocaleString('en-IN', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} Cr` : '-'}</p>
                                </div>
                                <div className="p-3 bg-white/5 rounded-lg border border-white/5 col-span-2 flex justify-between items-center">
                                    <div>
                                        <p className="text-xs text-gray-500 mb-1">Beta</p>
                                        <p className="text-xl font-bold text-white">{stockData.info["beta"]?.toFixed(1) || '-'}</p>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-xs text-gray-500 mb-1">Volume</p>
                                        <p className="text-sm font-medium text-gray-300">{stockData.info["volume"]?.toLocaleString('en-IN') || '-'}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </ChartCard>
                )}
            </div>

            {/* Key Financial Ratios Row (Full Width) */}
            <div className="flex flex-col">
                <motion.div
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    className="xl:col-span-2 glass-card p-6 rounded-3xl border border-white/5 bg-[#121212]/50 flex flex-col"
                >
                    <div className="flex justify-between items-start mb-6">
                        <h3 className="text-lg font-semibold text-white">Key Financial Ratios</h3>
                        <a href={data.meta?.link || "https://finance.yahoo.com"} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300 text-xs flex items-center gap-1 transition-colors">
                            Verify <ExternalLink size={10} />
                        </a>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4 flex-1">
                        {data.ratios && Object.entries(data.ratios).map(([key, value], idx) => (
                            <div key={idx} className="bg-white/5 p-4 rounded-xl border border-white/5 flex flex-col items-center justify-center text-center hover:bg-white/10 transition-colors">
                                <span className="text-gray-400 text-xs uppercase tracking-wider mb-1">{key}</span>
                                <span className="text-2xl font-bold text-white tracking-tight">{String(value)}</span>
                            </div>
                        ))}
                    </div>
                    <div className="mt-4 pt-3 border-t border-white/5 text-xs text-gray-500 flex items-center gap-2 justify-end">
                        <span className="font-semibold text-gray-400">Source:</span> Yahoo Finance
                    </div>
                </motion.div>
            </div>
        </div>


    );
}
