"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Shield, Users, Database, ShieldAlert, Trash2, ArrowLeft, Activity, Lock } from "lucide-react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";

interface Stats {
  total_queries: number;
  total_blocks: number;
  total_users: number;
}

interface Doc {
  filename: string;
  path: string;
  classification: string;
}

export default function AdminDashboard() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  
  const [stats, setStats] = useState<Stats | null>(null);
  const [docs, setDocs] = useState<Doc[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const t = localStorage.getItem("token");
    const r = localStorage.getItem("role");
    
    if (!t || r !== "admin") {
      router.push("/");
      return;
    }
    
    setToken(t);
    fetchData(t);
  }, [router]);

  const fetchData = async (t: string) => {
    setIsLoading(true);
    try {
      const [statsRes, docsRes] = await Promise.all([
        fetch("http://127.0.0.1:8000/admin/stats", { headers: { Authorization: `Bearer ${t}` } }),
        fetch("http://127.0.0.1:8000/documents", { headers: { Authorization: `Bearer ${t}` } })
      ]);
      
      if (statsRes.ok) setStats(await statsRes.json());
      if (docsRes.ok) setDocs(await docsRes.json());
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const deleteDocument = async (path: string) => {
    if (!token) return;
    if (!confirm(`Are you sure you want to completely purge ${path} from the Vector Intelligence core?`)) return;
    
    try {
      const res = await fetch(`http://127.0.0.1:8000/documents?path=${encodeURIComponent(path)}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        setDocs(docs.filter(d => d.path !== path));
      } else {
        alert("Delete failed");
      }
    } catch (e) {
      console.error(e);
    }
  };

  if (!token || isLoading) return <div className="min-h-screen bg-slate-900 flex items-center justify-center text-white"><Activity className="w-6 h-6 animate-spin text-indigo-500" /></div>;

  const chartData = stats ? [
    { name: "Granted Queries", value: stats.total_queries - stats.total_blocks, color: "#10b981" },
    { name: "Blocked Intrusions (403)", value: stats.total_blocks, color: "#ef4444" }
  ] : [];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans p-6 md:p-10">
      
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* HEADER */}
        <header className="flex justify-between items-end border-b border-slate-200 pb-6">
          <div className="space-y-1">
            <button onClick={() => router.push("/")} className="text-sm font-bold text-slate-500 hover:text-indigo-600 flex items-center gap-1 mb-4 transition-colors">
              <ArrowLeft className="w-4 h-4" /> Return to Secure Chat
            </button>
            <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 flex items-center gap-3">
              <Shield className="w-8 h-8 text-indigo-600" />
              Command Center
            </h1>
            <p className="text-slate-500 font-medium text-sm">Global vector ingestion and telemetry.</p>
          </div>
          <div className="bg-red-50 text-red-700 px-4 py-2 rounded-lg border border-red-200 flex items-center gap-2 font-bold text-sm tracking-wider uppercase">
             <Lock className="w-4 h-4" /> Admin Access Authorized
          </div>
        </header>

        {/* TOP METRICS */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
           <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col items-center justify-center gap-2">
              <div className="p-3 bg-indigo-50 text-indigo-600 rounded-xl mb-2"><Database className="w-6 h-6" /></div>
              <span className="text-4xl font-black text-slate-900">{stats?.total_queries}</span>
              <span className="text-xs font-bold uppercase tracking-widest text-slate-400">Total Queries Evaualted</span>
           </div>
           
           <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col items-center justify-center gap-2">
              <div className="p-3 bg-red-50 text-red-600 rounded-xl mb-2"><ShieldAlert className="w-6 h-6" /></div>
              <span className="text-4xl font-black text-red-600">{stats?.total_blocks}</span>
              <span className="text-xs font-bold uppercase tracking-widest text-slate-400">Threats Blocked (403)</span>
           </div>

           <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col items-center justify-center gap-2">
              <div className="p-3 bg-blue-50 text-blue-600 rounded-xl mb-2"><Users className="w-6 h-6" /></div>
              <span className="text-4xl font-black text-slate-900">{stats?.total_users}</span>
              <span className="text-xs font-bold uppercase tracking-widest text-slate-400">Registered Identities</span>
           </div>
        </div>

        {/* MIDDLE SECTION - CHARTS AND VAULT */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
           
           {/* SECURITY PIE CHART */}
           <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 flex flex-col">
              <h2 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
                <Activity className="w-5 h-5 text-indigo-500" /> Intrusion Analytics
              </h2>
              <div className="flex-1 w-full min-h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={chartData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={5} dataKey="value">
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
           </div>

           {/* DOCUMENT MANAGEMENT VAULT */}
           <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden flex flex-col">
              <div className="px-6 py-5 border-b border-slate-100 flex justify-between items-center bg-slate-50">
                 <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                   <Database className="w-5 h-5 text-indigo-500" /> Document Vault List
                 </h2>
                 <span className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-xs font-bold">{docs.length} active files</span>
              </div>
              
              <div className="flex-1 overflow-x-auto">
                 <table className="w-full text-sm text-left">
                    <thead className="text-[10px] uppercase tracking-wider text-slate-400 bg-slate-50/50 border-b border-slate-100">
                       <tr>
                          <th className="px-6 py-4 font-bold">Physical Document Name</th>
                          <th className="px-6 py-4 font-bold">Vector Scope Level</th>
                          <th className="px-6 py-4 font-bold text-right">Sanitize Action</th>
                       </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                       {docs.length === 0 && (
                         <tr>
                           <td colSpan={3} className="px-6 py-12 text-center text-slate-400">No documents exist in the vector database.</td>
                         </tr>
                       )}
                       {docs.map((doc, idx) => (
                         <tr key={idx} className="hover:bg-slate-50 transition-colors">
                            <td className="px-6 py-4 font-medium text-slate-800 break-all">{doc.filename}</td>
                            <td className="px-6 py-4">
                               <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider border ${
                                 doc.classification === 'admin' ? 'bg-red-50 text-red-700 border-red-200' :
                                 doc.classification === 'manager' ? 'bg-purple-50 text-purple-700 border-purple-200' :
                                 doc.classification === 'mixed_clearance' ? 'bg-orange-50 text-orange-700 border-orange-200' :
                                 'bg-blue-50 text-blue-700 border-blue-200'
                               }`}>
                                 {doc.classification.replace('_', ' ')}
                               </span>
                            </td>
                            <td className="px-6 py-4 text-right">
                               <button 
                                  onClick={() => deleteDocument(doc.path)}
                                  className="p-2 text-slate-400 hover:bg-red-50 hover:text-red-600 rounded-lg transition-all border border-transparent hover:border-red-100 shadow-sm"
                                  title="Permanently Delete Evidence"
                               >
                                  <Trash2 className="w-4 h-4" />
                               </button>
                            </td>
                         </tr>
                       ))}
                    </tbody>
                 </table>
              </div>
           </div>

        </div>

      </div>
    </div>
  );
}
