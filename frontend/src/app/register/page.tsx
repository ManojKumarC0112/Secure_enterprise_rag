"use client";

import { useState } from "react";
import { Shield, ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function Register() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [passkey, setPasskey] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      const res = await fetch("http://127.0.0.1:8000/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username,
          password,
          admin_passkey: passkey || null
        }),
      });
      const data = await res.json();
      
      if (res.ok) {
        alert(`Clearance granted: ${data.role.toUpperCase()}`);
        router.push("/login"); // send to login
      } else {
        setError(data.detail || "Registration failed");
      }
    } catch (err) {
      setError("Unable to connect to the authentication server.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8 selection:bg-blue-500/30 text-slate-200">
      <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none"></div>
      <div className="absolute inset-0 bg-gradient-to-tr from-slate-900 via-slate-900 to-indigo-900/40 pointer-events-none"></div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <div className="flex justify-center">
          <div className="bg-indigo-500/10 p-3 rounded-2xl border border-indigo-500/20 backdrop-blur-md">
            <Shield className="w-10 h-10 text-indigo-400" />
          </div>
        </div>
        <h2 className="mt-6 text-center text-3xl font-extrabold tracking-tight text-white drop-shadow-lg">
          Identity Provisioning
        </h2>
        <p className="mt-2 text-center text-sm text-slate-400">
          Already verified? <Link href="/login" className="font-medium text-indigo-400 hover:text-indigo-300 transition-colors">Authenticate</Link>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <div className="bg-slate-800/50 backdrop-blur-xl py-8 px-4 shadow-2xl border border-slate-700/50 sm:rounded-2xl sm:px-10">
          <form className="space-y-6" onSubmit={handleRegister}>
            
            {error && (
              <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-sm p-3 rounded-lg flex items-center justify-center">
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-slate-300">Desired Identifier</label>
              <div className="mt-1">
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="appearance-none block w-full px-3 py-2.5 border border-slate-600/50 rounded-lg shadow-sm placeholder-slate-500 bg-slate-900/50 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all sm:text-sm"
                  placeholder="Create username..."
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300">Strong Passphrase</label>
              <div className="mt-1">
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="appearance-none block w-full px-3 py-2.5 border border-slate-600/50 rounded-lg shadow-sm placeholder-slate-500 bg-slate-900/50 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all sm:text-sm"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300">Admin Invite Code (Optional)</label>
              <p className="text-xs text-slate-500 mb-2 mt-1">Leave blank for default Employee least-privilege status.</p>
              <div className="mt-1">
                <input
                  type="password"
                  value={passkey}
                  onChange={(e) => setPasskey(e.target.value)}
                  className="appearance-none block w-full px-3 py-2.5 border border-slate-600/50 rounded-lg shadow-sm placeholder-slate-500 bg-slate-900/50 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all sm:text-sm"
                  placeholder="Elevated privileges..."
                />
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex justify-center items-center gap-2 py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-900 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {isLoading ? 'Provisioning...' : 'Provision Account'}
              </button>
            </div>
            
            <div className="pt-2 text-center">
                <Link href="/login" className="text-xs text-slate-400 hover:text-slate-200 inline-flex items-center gap-1">
                    <ArrowLeft className="w-3 h-3" /> Back to Login
                </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
