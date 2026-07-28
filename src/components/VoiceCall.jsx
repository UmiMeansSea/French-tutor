import React, { useState, useEffect } from 'react';
import { PhoneOff, Mic, MicOff, Volume2, Subtitles, ShieldAlert, Sparkles } from 'lucide-react';

export default function VoiceCall({ mentor, onEndCall }) {
  const [callStatus, setCallStatus] = useState('Connecting...');
  const [isMuted, setIsMuted] = useState(false);
  const [showCc, setShowCc] = useState(true);
  const [speedMode, setSpeedMode] = useState('normal'); // 'normal' | 'turtle'
  const [currentCaption, setCurrentCaption] = useState("Bonjour ! Je te réécoute. Parle librement sans interruption.");

  useEffect(() => {
    const timer = setTimeout(() => {
      setCallStatus('Live Voice Call • Hands-Free Mode');
    }, 1500);
    return () => clearTimeout(timer);
  }, []);

  const toggleSpeed = () => {
    if (speedMode === 'normal') {
      setSpeedMode('turtle');
      setCurrentCaption("*(Speed Mode: Turtle 🐢 - Slow pace engaged)*");
    } else {
      setSpeedMode('normal');
      setCurrentCaption("*(Speed Mode: Normal 🐇 - Natural pace engaged)*");
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/95 backdrop-blur-2xl flex flex-col justify-between p-6 overflow-hidden">
      {/* Top Header */}
      <div className="flex items-center justify-between z-10">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/80 border border-slate-800 text-xs font-medium text-indigo-300">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          {callStatus}
        </div>

        {/* Speed Mode Toggle Button */}
        <button 
          onClick={toggleSpeed}
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-indigo-500/40 text-xs font-bold text-slate-200 transition-all active:scale-95"
        >
          {speedMode === 'normal' ? 'Normal 🐇' : 'Turtle 🐢'}
        </button>
      </div>

      {/* Center Avatar & Visualizer */}
      <div className="flex-1 flex flex-col items-center justify-center relative my-auto z-10">
        <div className="relative">
          {/* Animated Glow Wave Pulsing Ring */}
          <div className="absolute -inset-6 rounded-full bg-gradient-to-r from-indigo-500/30 to-purple-500/30 blur-xl animate-pulse" />
          
          <img 
            src={mentor.avatar} 
            alt={mentor.name} 
            className="w-36 h-36 sm:w-44 sm:h-44 rounded-full object-cover ring-4 ring-indigo-500/50 shadow-2xl relative z-10"
          />
          <span className="absolute bottom-2 right-2 z-20 w-6 h-6 bg-emerald-400 border-4 border-slate-950 rounded-full" />
        </div>

        <h2 className="text-2xl font-bold text-slate-100 mt-6 font-heading tracking-wide">
          {mentor.name}
        </h2>
        <p className="text-xs text-indigo-300 font-medium mt-1">
          {mentor.role}
        </p>

        {/* Audio Wave Visualizer Animation */}
        <div className="flex items-center gap-1.5 h-12 mt-8">
          <div className="w-1.5 h-8 bg-indigo-500 rounded-full wave-bar" />
          <div className="w-1.5 h-12 bg-purple-500 rounded-full wave-bar" />
          <div className="w-1.5 h-10 bg-indigo-400 rounded-full wave-bar" />
          <div className="w-1.5 h-6 bg-purple-400 rounded-full wave-bar" />
          <div className="w-1.5 h-11 bg-indigo-500 rounded-full wave-bar" />
        </div>
      </div>

      {/* Closed Captions Banner */}
      {showCc && (
        <div className="mx-auto max-w-md w-full mb-6 p-4 rounded-2xl glass-card border border-slate-800/80 text-center z-10">
          <p className="text-xs sm:text-sm text-slate-200 font-medium leading-relaxed italic">
            "{currentCaption}"
          </p>
        </div>
      )}

      {/* Bottom Control Bar */}
      <div className="flex items-center justify-center gap-6 pb-6 z-10">
        {/* Closed Captions Toggle */}
        <button 
          onClick={() => setShowCc(!showCc)}
          title="Toggle Closed Captions"
          className={`p-4 rounded-full transition-all ${
            showCc ? 'bg-indigo-600/30 border border-indigo-500/50 text-indigo-300' : 'bg-slate-900/80 border border-slate-800 text-slate-500'
          }`}
        >
          <span className="font-bold text-xs">CC</span>
        </button>

        {/* End Call Button */}
        <button 
          onClick={onEndCall}
          title="End Call"
          className="p-5 rounded-full bg-rose-600 hover:bg-rose-500 text-white shadow-xl shadow-rose-950/60 transition-all active:scale-95"
        >
          <PhoneOff className="w-7 h-7" />
        </button>

        {/* Mute Mic Toggle */}
        <button 
          onClick={() => setIsMuted(!isMuted)}
          title={isMuted ? "Unmute Microphone" : "Mute Microphone"}
          className={`p-4 rounded-full transition-all ${
            isMuted ? 'bg-rose-500/20 border border-rose-500/40 text-rose-400' : 'bg-slate-900/80 border border-slate-800 text-slate-300'
          }`}
        >
          {isMuted ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
        </button>
      </div>
    </div>
  );
}
