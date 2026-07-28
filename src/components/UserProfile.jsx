import React, { useState } from 'react';
import { X, User, Flame, Trophy, Brain, Sparkles, Zap, Shield, Save, Bookmark } from 'lucide-react';

export default function UserProfile({ userProfile, stats, onSave, onClose }) {
  const [name, setName] = useState(userProfile.name);
  const [email, setEmail] = useState(userProfile.email);
  const [cefrLevel, setCefrLevel] = useState(userProfile.cefrLevel);

  const handleSave = () => {
    onSave({
      ...userProfile,
      name,
      email,
      cefrLevel
    });
    onClose();
  };

  const statIcons = {
    Knowledge: <Brain className="w-4 h-4 text-purple-400" />,
    Charm:     <Sparkles className="w-4 h-4 text-amber-400" />,
    Wit:       <Zap className="w-4 h-4 text-yellow-400" />,
    Courage:   <Shield className="w-4 h-4 text-rose-400" />,
    Memory:    <Bookmark className="w-4 h-4 text-emerald-400" />
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="w-full max-w-lg glass-panel rounded-3xl overflow-hidden border border-slate-700/60 shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center gap-2">
            <User className="w-5 h-5 text-indigo-400" />
            <h2 className="font-bold text-slate-100 text-base">User Profile & RPG Stat Chart</h2>
          </div>
          <button 
            onClick={onClose}
            className="p-1.5 rounded-full text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* User Details Form */}
          <div className="flex items-center gap-4 p-4 rounded-2xl glass-card">
            <img 
              src={userProfile.avatar} 
              alt={userProfile.name} 
              className="w-16 h-16 rounded-full object-cover ring-2 ring-indigo-500"
            />
            <div className="flex-1 space-y-2">
              <div>
                <label className="text-[10px] font-bold uppercase text-slate-400 block mb-0.5">Name</label>
                <input 
                  type="text" 
                  value={name} 
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="text-[10px] font-bold uppercase text-slate-400 block mb-0.5">Email</label>
                <input 
                  type="email" 
                  value={email} 
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>
          </div>

          {/* CEFR Level Selection */}
          <div className="p-4 rounded-2xl glass-card">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-300 block mb-2">
              Active CEFR Language Target
            </label>
            <div className="grid grid-cols-6 gap-2">
              {['A1', 'A2', 'B1', 'B2', 'C1', 'C2'].map((lvl) => (
                <button
                  key={lvl}
                  type="button"
                  onClick={() => setCefrLevel(lvl)}
                  className={`py-2 rounded-xl text-xs font-bold transition-all ${
                    cefrLevel === lvl
                      ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md'
                      : 'bg-slate-900 text-slate-400 hover:bg-slate-800'
                  }`}
                >
                  {lvl}
                </button>
              ))}
            </div>
          </div>

          {/* RPG Persona Stat Chart */}
          <div className="p-4 rounded-2xl glass-card space-y-3">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center justify-between">
              <span>📊 RPG Persona Stat Chart</span>
              <span className="text-[10px] text-indigo-400 font-normal">Active Synergy</span>
            </h3>

            <div className="space-y-2.5">
              {Object.entries(stats).map(([statName, val]) => {
                const lvl = Math.floor(val / 20) + 1;
                const pct = ((val % 20) / 20) * 100;
                return (
                  <div key={statName} className="space-y-1">
                    <div className="flex justify-between text-xs font-medium">
                      <span className="flex items-center gap-1.5 text-slate-200">
                        {statIcons[statName]}
                        {statName}
                      </span>
                      <span className="text-slate-400 font-mono text-[11px]">
                        Lvl {lvl} • {val} PTS
                      </span>
                    </div>
                    <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden border border-slate-800">
                      <div 
                        className="bg-gradient-to-r from-indigo-500 via-purple-500 to-emerald-400 h-full rounded-full transition-all duration-300"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Badges Showcase */}
          <div className="p-4 rounded-2xl glass-card">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
              <Trophy className="w-4 h-4 text-amber-400" />
              Unlocked Achievement Badges ({userProfile.badges.length})
            </h3>
            <div className="flex flex-wrap gap-2">
              {userProfile.badges.map((badge, idx) => (
                <span 
                  key={idx}
                  className="px-3 py-1.5 rounded-xl bg-gradient-to-r from-indigo-950 to-purple-950 border border-indigo-500/30 text-indigo-300 font-medium text-xs shadow-sm"
                >
                  {badge}
                </span>
              ))}
            </div>
          </div>

          {/* Cross-Session Long-Term Memory */}
          <div className="p-4 rounded-2xl glass-card">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Brain className="w-4 h-4 text-indigo-400" />
              Cross-Session RAG Memory Recall
            </h3>
            <ul className="space-y-1.5 text-xs text-slate-300">
              {userProfile.userMemories.map((mem, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-indigo-400">•</span>
                  <span>{mem}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/60 flex justify-end gap-2">
          <button 
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:bg-slate-800 transition-colors"
          >
            Cancel
          </button>
          <button 
            onClick={handleSave}
            className="px-5 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md flex items-center gap-1.5 transition-all"
          >
            <Save className="w-4 h-4" />
            Save Profile
          </button>
        </div>
      </div>
    </div>
  );
}
