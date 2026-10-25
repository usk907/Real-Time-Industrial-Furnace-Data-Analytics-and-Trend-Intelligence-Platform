import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Sparkles, Terminal, Database, HelpCircle, Code, CornerDownRight, ShieldAlert } from 'lucide-react';

interface QueryResult {
  question: string;
  sql: string | null;
  error: string | null;
  rows: any[];
  answer: string | null;
}

const EXAMPLES = [
  "How many active alarms are in the plant right now?",
  "List all devices that are currently offline",
  "What is the average value of SMS-1 Furnace Temp today?",
  "What is the maximum rated capacity among all active machines?",
  "List the latest readings for all pressure sensors"
];

export const AiQuery: React.FC = () => {
  const { token } = useAuth();
  const [question, setQuestion] = useState('');
  const [result, setResult] = useState<QueryResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSql, setShowSql] = useState(false);
  const [history, setHistory] = useState<string[]>([]);

  const handleSubmit = async (q?: string) => {
    const queryText = (q ?? question).trim();
    if (!queryText) return;

    setLoading(true);
    setError(null);
    setResult(null);
    setShowSql(false);

    try {
      const res = await fetch('/api/ai/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ question: queryText })
      });

      if (res.ok) {
        const data: QueryResult = await res.json();
        setResult(data);
        
        // Add to query history if not already present
        if (!history.includes(queryText)) {
          setHistory(prev => [queryText, ...prev].slice(0, 5));
        }
      } else {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to execute query');
      }
    } catch (e: any) {
      console.error(e);
      setError(e.message || 'Connection to the AI query engine failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  return (
    <div className="space-y-6 animate-fade-in text-xs font-semibold">
      
      {/* Title Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-wider flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-cyan-400 animate-pulse" /> AI Database Copilot
          </h2>
          <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-1">
            Plain English natural language to SQL translation & execution console
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        
        {/* Input Console */}
        <div className="xl:col-span-3 space-y-6">
          <div className="bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-6 backdrop-blur space-y-4">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2">
              <Terminal className="h-4.5 w-4.5 text-cyan-400" /> Enter Query Prompt
            </h4>
            
            <div className="flex flex-col md:flex-row gap-3">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Ask me anything, e.g. What is the average value of SMS-1 Furnace Temp today?"
                className="flex-1 bg-[#0D1227] border border-[#1F2942]/60 rounded-xl p-4 text-slate-200 text-sm focus:outline-none focus:border-cyan-400 focus:shadow-[0_0_8px_rgba(34,211,238,0.25)] transition-all placeholder-slate-600 font-sans"
                disabled={loading}
              />
              <button
                onClick={() => handleSubmit()}
                disabled={loading || !question.trim()}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-[#1C2340] disabled:text-slate-500 text-white font-extrabold px-6 py-4 rounded-xl uppercase tracking-wider transition-all shadow-lg shadow-blue-600/10 flex items-center justify-center gap-2 flex-shrink-0"
              >
                {loading ? "Analyzing..." : "Run Query"}
              </button>
            </div>

            {/* Suggestions Chips */}
            <div className="space-y-2.5">
              <p className="text-[9px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1.5">
                <HelpCircle className="h-3.5 w-3.5 text-cyan-400" /> Example Queries:
              </p>
              <div className="flex flex-wrap gap-2">
                {EXAMPLES.map((ex, idx) => (
                  <button
                    key={idx}
                    onClick={() => { setQuestion(ex); handleSubmit(ex); }}
                    className="bg-[#121933]/60 hover:bg-[#1E274D] border border-[#1F2942]/45 hover:border-cyan-400/40 text-slate-400 hover:text-cyan-300 px-3 py-2 rounded-xl text-[10px] transition-all font-sans"
                    disabled={loading}
                  >
                    {ex}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-2xl p-4 flex items-start gap-3">
              <ShieldAlert className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-bold uppercase text-[9px] tracking-wider">Query Analysis Failed</p>
                <p className="mt-1 font-sans text-xs">{error}</p>
              </div>
            </div>
          )}

          {/* Query Response Result Card */}
          {result && (
            <div className="bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-6 backdrop-blur space-y-6">
              
              {/* Natural Language Answer */}
              {result.answer && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                    <Sparkles className="h-4.5 w-4.5 text-cyan-400" /> Answer Summary
                  </h4>
                  <div className="bg-[#121933]/60 border border-[#1F2942]/45 rounded-xl p-5 text-slate-200 text-sm leading-relaxed font-sans shadow-inner">
                    {result.answer}
                  </div>
                </div>
              )}

              {/* Execution Error in Query */}
              {result.error && (
                <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl p-4 flex items-start gap-2.5">
                  <ShieldAlert className="h-4.5 w-4.5 text-red-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-bold uppercase text-[9px] tracking-wider">SQL Syntax/Validation Error</p>
                    <p className="mt-1 font-sans text-xs">{result.error}</p>
                  </div>
                </div>
              )}

              {/* SQL Toggle Panel */}
              {result.sql && (
                <div className="space-y-2.5">
                  <button
                    onClick={() => setShowSql(!showSql)}
                    className="text-[10px] text-cyan-400 font-bold uppercase tracking-wider flex items-center gap-1.5 bg-[#1B2544] hover:bg-[#25325C] border border-[#2B3A6C] px-3.5 py-2 rounded-xl transition-all"
                  >
                    <Code className="h-3.5 w-3.5" />
                    {showSql ? "Hide SQL Query" : "Show Generated SQL Query"}
                  </button>
                  {showSql && (
                    <div className="bg-[#080B17] border border-[#1F2942]/85 rounded-xl p-4 overflow-x-auto relative">
                      <pre className="text-cyan-400 font-mono text-xs leading-relaxed whitespace-pre-wrap">{result.sql}</pre>
                    </div>
                  )}
                </div>
              )}

              {/* SQL Data Output Grid Table */}
              {result.rows && result.rows.length > 0 ? (
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                    <Database className="h-4.5 w-4.5 text-cyan-400" /> Database Query Output ({result.rows.length} rows)
                  </h4>
                  <div className="border border-[#1F2942]/60 rounded-xl overflow-hidden bg-[#0A0D1A]/50">
                    <div className="overflow-x-auto max-h-96">
                      <table className="w-full text-left border-collapse text-[11px] font-sans">
                        <thead>
                          <tr className="bg-[#121933] border-b border-[#1F2942]/60 sticky top-0">
                            {Object.keys(result.rows[0]).map((col) => (
                              <th key={col} className="p-3.5 text-slate-400 font-bold uppercase tracking-wider">
                                {col}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#1F2942]/35">
                          {result.rows.map((row, idx) => (
                            <tr key={idx} className="hover:bg-[#151D3D]/40 transition-colors">
                              {Object.values(row).map((val: any, cellIdx) => (
                                <td key={cellIdx} className="p-3.5 text-slate-300 font-mono">
                                  {val === null || val === undefined ? (
                                    <span className="text-slate-600 italic">NULL</span>
                                  ) : typeof val === 'object' ? (
                                    JSON.stringify(val)
                                  ) : (
                                    String(val)
                                  )}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              ) : (
                result.sql && !result.error && (
                  <div className="p-8 text-center text-slate-500 font-sans text-xs border border-dashed border-[#1F2942]/50 rounded-xl bg-[#090D1A]/30">
                    No matching database rows were returned by the query.
                  </div>
                )
              )}

            </div>
          )}

        </div>

        {/* Sidebar History Console */}
        <div className="space-y-6">
          <div className="bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-6 backdrop-blur space-y-4">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2">
              <ClockIcon className="h-4.5 w-4.5 text-cyan-400" /> Recent Questions
            </h4>
            
            {history.length === 0 ? (
              <p className="text-slate-500 font-sans text-[11px]">No questions run in this session.</p>
            ) : (
              <div className="space-y-2">
                {history.map((h, i) => (
                  <button
                    key={i}
                    onClick={() => { setQuestion(h); handleSubmit(h); }}
                    className="w-full text-left bg-[#121933]/60 hover:bg-[#1E274D] border border-[#1F2942]/45 p-3 rounded-xl transition-all flex items-start gap-2 hover:border-cyan-400/40 text-slate-400 hover:text-cyan-300"
                  >
                    <CornerDownRight className="h-3.5 w-3.5 text-cyan-400 flex-shrink-0 mt-0.5 animate-pulse" />
                    <span className="font-sans text-[11px] leading-tight truncate-two-lines">{h}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

      </div>

    </div>
  );
};

const ClockIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
  </svg>
);
