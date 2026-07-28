import React from 'react';
import { X, Trophy, Sparkles, BookOpen, Flame, CheckCircle, AlertTriangle } from 'lucide-react';

export default function MentorProfile({ mentor, onClose }) {
  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="w-full max-w-lg glass-panel rounded-3xl overflow-hidden border border-slate-700/60 shadow-2xl animate-in fade-in zoom-in duration-200">
        {/* Header Banner */}
        <div className="relative h-32 bg-gradient-to-r from-indigo-900 via-purple-900 to-slate-900 p-4 flex justify-between items-start">
          <button 
            onClick={onClose}
            className="p-2 rounded-full bg-slate-950/60 text-slate-300 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Profile Avatar & Info Overlay */}
        <div className="px-6 pb-6 relative">
          <div className="relative -mt-16 mb-4 inline-block">
            <img 
              src={mentor.avatar} 
              alt={mentor.name} 
              className="w-24 h-24 rounded-2xl object-cover ring-4 ring-slate-950 shadow-xl"
            />
            <span className="absolute -bottom-2 -right-2 bg-gradient-to-r from-indigo-500 to-purple-500 text-white font-bold text-xs px-2 py-0.5 rounded-full border-2 border-slate-950 shadow-md">
              Lvl {mentor.level}
            </span>
          </div>

          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            {mentor.name}
            <span className="text-xs bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-2 py-0.5 rounded-md font-normal">
              {mentor.role}
            </span>
          </h2>

          <p className="text-xs text-slate-400 mt-2 leading-relaxed">
            {mentor.backstory}
          </p>

          {/* Relationship XP Progress */}
          <div className="mt-4 p-3 rounded-2xl bg-slate-900/60 border border-slate-800">
            <div className="flex justify-between text-xs mb-1.5 font-medium">
              <span className="text-slate-300 flex items-center gap-1">
                <Trophy className="w-3.5 h-3.5 text-amber-400" />
                Mentor Rapport Level
              </span>
              <span className="text-indigo-400">{mentor.xp} / {mentor.nextLevelXp} XP</span>
            </div>
            <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
              <div 
                className="bg-gradient-to-r from-indigo-500 via-purple-500 to-amber-500 h-full rounded-full"
                style={{ width: `${(mentor.xp / mentor.nextLevelXp) * 100}%` }}
              />
            </div>
          </div>

          {/* Milestone Perks */}
          <div className="mt-4 p-3.5 rounded-2xl bg-indigo-950/30 border border-indigo-500/20">
            <h4 className="text-xs font-bold text-indigo-300 uppercase tracking-wider flex items-center gap-1.5 mb-1">
              <Sparkles className="w-3.5 h-3.5" />
              Mentor Synergy Perks
            </h4>
            <p className="text-xs text-slate-300 leading-relaxed">
              {mentor.perks}
            </p>
          </div>

          {/* "What to Improve" Feedback Grid */}
          <div className="mt-4">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
              What to Improve (Grammar & Vocab Priorities)
            </h4>

            <div className="space-y-2">
              {mentor.whatToImprove.map((item, idx) => (
                <div 
                  key={idx}
                  className="p-2.5 rounded-xl glass-card flex items-center justify-between text-xs"
                >
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded-md font-bold text-[10px] ${
                      item.priority === 'High' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' :
                      item.priority === 'Medium' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                      'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    }`}>
                      {item.category}
                    </span>
                    <span className="text-slate-200">{item.item}</span>
                  </div>

                  <span className="text-[10px] text-slate-400 font-medium">
                    {item.priority} Priority
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
