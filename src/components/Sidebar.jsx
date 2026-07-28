import React from 'react';
import { User, MessageSquare, Sparkles, Trophy, BookOpen, Flame } from 'lucide-react';

export default function Sidebar({ 
  mentors, 
  currentMentor, 
  onSelectMentor, 
  userProfile, 
  onOpenUserProfile, 
  isOpen, 
  onCloseMobile 
}) {
  return (
    <aside 
      className={`fixed inset-y-0 left-0 z-40 w-80 glass-panel border-r border-slate-800/60 flex flex-col transition-transform duration-300 ease-in-out lg:static lg:translate-x-0 ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      }`}
    >
      {/* Top User Profile Header */}
      <div 
        onClick={onOpenUserProfile}
        className="p-4 border-b border-slate-800/80 flex items-center justify-between cursor-pointer hover:bg-slate-800/40 transition-colors group"
      >
        <div className="flex items-center gap-3">
          <div className="relative">
            <img 
              src={userProfile.avatar} 
              alt={userProfile.name} 
              className="w-12 h-12 rounded-full object-cover ring-2 ring-indigo-500/50 group-hover:ring-indigo-400 transition-all"
            />
            <span className="absolute -bottom-1 -right-1 bg-gradient-to-r from-amber-500 to-orange-500 text-slate-950 font-bold text-[10px] px-1.5 py-0.5 rounded-full shadow-md">
              {userProfile.cefrLevel}
            </span>
          </div>
          <div>
            <h3 className="font-semibold text-slate-100 group-hover:text-indigo-400 transition-colors text-sm flex items-center gap-1.5">
              {userProfile.name}
            </h3>
            <div className="flex items-center gap-2 mt-0.5 text-xs text-slate-400">
              <span className="flex items-center gap-1 text-orange-400 font-medium">
                <Flame className="w-3.5 h-3.5 fill-orange-400" />
                {userProfile.streakDays}d streak
              </span>
              <span>•</span>
              <span className="text-indigo-300 font-medium">
                {userProfile.xpTotal} XP
              </span>
            </div>
          </div>
        </div>

        <div className="p-2 rounded-xl bg-slate-800/60 text-slate-400 group-hover:text-slate-200 group-hover:bg-indigo-600/20 transition-all">
          <User className="w-5 h-5" />
        </div>
      </div>

      {/* App Branding Title */}
      <div className="px-4 py-3 bg-slate-950/40 border-b border-slate-800/40 flex items-center justify-between">
        <span className="text-xs uppercase tracking-wider font-bold text-slate-400 flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
          AI Chameleon Mentors
        </span>
        <span className="text-[10px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded-full">
          PWA Active
        </span>
      </div>

      {/* Mentors List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {mentors.map((mentor) => {
          const isSelected = currentMentor.id === mentor.id;
          return (
            <div
              key={mentor.id}
              onClick={() => {
                onSelectMentor(mentor);
                if (onCloseMobile) onCloseMobile();
              }}
              className={`relative p-3.5 rounded-2xl cursor-pointer transition-all duration-200 flex items-center gap-3.5 ${
                isSelected 
                  ? 'bg-gradient-to-r from-indigo-950/80 to-slate-900/90 border border-indigo-500/30 shadow-lg shadow-indigo-950/30' 
                  : 'hover:bg-slate-800/40 border border-transparent'
              }`}
            >
              {/* Avatar Container with Badges */}
              <div className="relative flex-shrink-0">
                <img 
                  src={mentor.avatar} 
                  alt={mentor.name} 
                  className={`w-13 h-13 rounded-full object-cover ring-2 ${
                    isSelected ? 'ring-indigo-400' : 'ring-slate-700/60'
                  }`}
                />

                {/* Red Dot Badge: Unread / Proactive Reminders */}
                {mentor.unread && (
                  <span 
                    title="Unread reminder"
                    className="absolute top-0 right-0 w-3.5 h-3.5 bg-rose-500 border-2 border-slate-950 rounded-full shadow-md animate-pulse" 
                  />
                )}

                {/* Green Dot Badge: Unlocked Hangout Milestone */}
                {mentor.hangoutUnlocked && (
                  <span 
                    title="Hangout Milestone Unlocked!"
                    className="absolute bottom-0 right-0 w-3.5 h-3.5 bg-emerald-400 border-2 border-slate-950 rounded-full shadow-md" 
                  />
                )}
              </div>

              {/* Mentor Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h4 className="font-semibold text-slate-100 truncate text-sm">
                    {mentor.name}
                  </h4>
                  <span className="text-[10px] font-bold bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded-md">
                    Lvl {mentor.level}
                  </span>
                </div>
                <p className="text-xs text-slate-400 truncate mt-0.5">
                  {mentor.role}
                </p>
                <div className="mt-2 w-full bg-slate-800/80 h-1.5 rounded-full overflow-hidden">
                  <div 
                    className="bg-gradient-to-r from-indigo-500 to-purple-500 h-full rounded-full transition-all duration-300"
                    style={{ width: `${(mentor.xp / mentor.nextLevelXp) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer Info */}
      <div className="p-3 border-t border-slate-800/60 bg-slate-950/40 text-center">
        <p className="text-[11px] text-slate-500 font-medium">
          LinguaPhantom PWA • Interactions API Enabled
        </p>
      </div>
    </aside>
  );
}
