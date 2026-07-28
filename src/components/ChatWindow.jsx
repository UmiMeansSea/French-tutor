import React, { useState, useRef, useEffect } from 'react';
import { 
  Phone, 
  Send, 
  MoreVertical, 
  Menu, 
  Sparkles, 
  Volume2, 
  VolumeX, 
  Mic,
  BookOpen,
  Compass,
  Smile,
  ShieldAlert,
  Flame
} from 'lucide-react';
import { sendInteractionMessage } from '../services/api';

export default function ChatWindow({ 
  mentor, 
  onOpenMentorProfile, 
  onStartCall, 
  onToggleSidebar,
  userProfile,
  onUpdateUserProfile
}) {
  const [messages, setMessages] = useState([
    {
      id: 'init-1',
      sender: 'mentor',
      french: `Bonjour ! Je suis ${mentor.name}. Comment vas-tu aujourd'hui ?`,
      feedback: `I'm locked in as your mentor! Ask me anything, request a /story, or try a /roleplay!`,
      timestamp: '10:00 AM'
    }
  ]);

  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [previousInteractionId, setPreviousInteractionId] = useState(null);
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // Speech synthesis helper
  const speakText = (text) => {
    if (!ttsEnabled || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'fr-FR';
    utterance.rate = 0.9;
    window.speechSynthesis.speak(utterance);
  };

  const handleSend = async (textToSend = input) => {
    if (!textToSend.trim()) return;

    const userMsg = {
      id: `usr_${Date.now()}`,
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    try {
      // Interactions API server-side chaining call
      const res = await sendInteractionMessage(mentor.id, textToSend, previousInteractionId);
      
      setPreviousInteractionId(res.interactionId);

      const mentorMsg = {
        id: `mnt_${Date.now()}`,
        sender: 'mentor',
        french: res.frenchResponse,
        feedback: res.mentorFeedback,
        phonetics: res.phoneticBreakdown,
        timestamp: res.timestamp
      };

      setMessages(prev => [...prev, mentorMsg]);
      speakText(res.frenchResponse);

      // Award XP
      if (onUpdateUserProfile) {
        onUpdateUserProfile(prev => ({
          ...prev,
          xpTotal: prev.xpTotal + 15
        }));
      }
    } catch (error) {
      console.error("Chat error:", error);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-950/60 relative">
      {/* Top Header */}
      <header className="h-16 px-4 glass-panel border-b border-slate-800/80 flex items-center justify-between z-20">
        <div className="flex items-center gap-3">
          {/* Mobile Sidebar Toggle Button */}
          <button 
            onClick={onToggleSidebar}
            className="lg:hidden p-2 rounded-xl text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 transition-all"
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Mentor Profile Picture & Header Trigger */}
          <div 
            onClick={onOpenMentorProfile}
            className="flex items-center gap-3 cursor-pointer group"
          >
            <div className="relative">
              <img 
                src={mentor.avatar} 
                alt={mentor.name} 
                className="w-10 h-10 rounded-full object-cover ring-2 ring-indigo-500/40 group-hover:ring-indigo-400 transition-all"
              />
              <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-emerald-400 border-2 border-slate-950 rounded-full" />
            </div>

            <div>
              <h2 className="font-semibold text-slate-100 group-hover:text-indigo-400 transition-colors text-sm flex items-center gap-1.5">
                {mentor.name}
                <span className="text-[10px] bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-1.5 py-0.2 rounded-md">
                  {mentor.role.split(' ')[0]}
                </span>
              </h2>
              <p className="text-[11px] text-slate-400 truncate">
                Online • Tap for Dossier & RPG Perks
              </p>
            </div>
          </div>
        </div>

        {/* Top Header Action Buttons */}
        <div className="flex items-center gap-1.5">
          {/* Voice Speech Toggle */}
          <button 
            onClick={() => setTtsEnabled(!ttsEnabled)}
            title={ttsEnabled ? "Mute Speech Synthesis" : "Enable Speech Synthesis"}
            className={`p-2 rounded-xl transition-all ${
              ttsEnabled ? 'text-indigo-400 bg-indigo-500/10' : 'text-slate-400 hover:bg-slate-800/60'
            }`}
          >
            {ttsEnabled ? <Volume2 className="w-5 h-5" /> : <VolumeX className="w-5 h-5" />}
          </button>

          {/* Voice Call / Walking Mode Button */}
          <button 
            onClick={onStartCall}
            title="Start Voice Call Mode"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-slate-950 font-bold text-xs shadow-md shadow-emerald-950/40 transition-all active:scale-95"
          >
            <Phone className="w-4 h-4 fill-slate-950" />
            <span className="hidden sm:inline">Call Mode</span>
          </button>

          <button className="p-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition-all">
            <MoreVertical className="w-5 h-5" />
          </button>
        </div>
      </header>

      {/* Quick Interactive Command Bar */}
      <div className="px-4 py-2 bg-slate-900/40 border-b border-slate-800/40 flex items-center gap-2 overflow-x-auto no-scrollbar text-xs">
        <button 
          onClick={() => handleSend("Please give me 1 native French sentence for me to shadow and repeat back.")}
          className="flex-shrink-0 flex items-center gap-1 px-2.5 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 hover:bg-indigo-500/20 transition-all"
        >
          <Sparkles className="w-3.5 h-3.5" />
          /shadow
        </button>
        <button 
          onClick={() => handleSend("Please read me a short story in French for my level and ask 2 questions.")}
          className="flex-shrink-0 flex items-center gap-1 px-2.5 py-1 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-300 hover:bg-purple-500/20 transition-all"
        >
          <BookOpen className="w-3.5 h-3.5" />
          /story
        </button>
        <button 
          onClick={() => handleSend("Let's do a Café simulation. Act as the waiter in Paris!")}
          className="flex-shrink-0 flex items-center gap-1 px-2.5 py-1 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 hover:bg-amber-500/20 transition-all"
        >
          <Compass className="w-3.5 h-3.5" />
          /roleplay
        </button>
        <button 
          onClick={() => handleSend("Let's do our mentor hangout session!")}
          className="flex-shrink-0 flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 hover:bg-emerald-500/20 transition-all"
        >
          <Smile className="w-3.5 h-3.5" />
          /hangout
        </button>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div 
            key={msg.id}
            className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
          >
            {msg.sender === 'user' ? (
              <div className="max-w-[85%] sm:max-w-[70%] bg-gradient-to-r from-indigo-600 to-indigo-700 text-white p-3.5 rounded-2xl rounded-tr-xs shadow-md border border-indigo-500/30">
                <p className="text-sm leading-relaxed font-normal">{msg.text}</p>
                <span className="text-[10px] text-indigo-200/70 block text-right mt-1 font-mono">
                  {msg.timestamp}
                </span>
              </div>
            ) : (
              <div className="max-w-[90%] sm:max-w-[75%] glass-card p-4 rounded-2xl rounded-tl-xs shadow-xl space-y-2 border border-slate-700/50">
                {/* Main French Response */}
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm sm:text-base font-semibold text-slate-100 leading-relaxed">
                    {msg.french}
                  </p>
                  <button 
                    onClick={() => speakText(msg.french)}
                    className="p-1 rounded-lg text-slate-400 hover:text-indigo-400 hover:bg-slate-800/60 transition-all"
                  >
                    <Volume2 className="w-4 h-4" />
                  </button>
                </div>

                {/* Phonetics / Liaison Breakdown */}
                {msg.phonetics && (
                  <div className="p-2 rounded-xl bg-purple-950/40 border border-purple-500/20 text-xs text-purple-300 font-mono flex items-center gap-2">
                    <Sparkles className="w-3.5 h-3.5 text-purple-400 flex-shrink-0" />
                    <span>Liaison: {msg.phonetics}</span>
                  </div>
                )}

                {/* Mentor Feedback & Coaching */}
                {msg.feedback && (
                  <div className="p-2.5 rounded-xl bg-indigo-950/30 border border-indigo-500/20 text-xs text-indigo-200 leading-relaxed">
                    <span className="font-bold text-indigo-400 block mb-0.5">
                      💡 Mentor Note:
                    </span>
                    {msg.feedback}
                  </div>
                )}

                <span className="text-[10px] text-slate-500 block text-right font-mono">
                  {msg.timestamp}
                </span>
              </div>
            )}
          </div>
        ))}

        {/* Typing Indicator */}
        {isTyping && (
          <div className="flex items-center gap-2 glass-card px-4 py-3 rounded-2xl rounded-tl-xs w-28">
            <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" />
            <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce [animation-delay:0.2s]" />
            <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce [animation-delay:0.4s]" />
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Sticky Bottom Input Bar */}
      <footer className="p-3 glass-panel border-t border-slate-800/80 z-20">
        <form 
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`Message ${mentor.name} in French or English...`}
            className="flex-1 bg-slate-900/90 border border-slate-800 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500/60 focus:ring-2 focus:ring-indigo-500/20 transition-all"
          />

          <button 
            type="submit"
            disabled={!input.trim()}
            className="p-3 rounded-2xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-40 disabled:hover:from-indigo-600 disabled:hover:to-purple-600 text-white font-semibold shadow-lg shadow-indigo-950/50 transition-all active:scale-95 flex items-center justify-center"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </footer>
    </div>
  );
}
