import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import VoiceCall from './components/VoiceCall';
import MentorProfile from './components/MentorProfile';
import UserProfile from './components/UserProfile';
import { 
  INITIAL_MENTORS, 
  INITIAL_USER_PROFILE, 
  INITIAL_STATS, 
  runMemoryExtractionWorker 
} from './services/api';

export default function App() {
  const [mentors, setMentors] = useState(INITIAL_MENTORS);
  const [currentMentor, setCurrentMentor] = useState(INITIAL_MENTORS[0]);
  const [userProfile, setUserProfile] = useState(INITIAL_USER_PROFILE);
  const [stats, setStats] = useState(INITIAL_STATS);

  const [activeView, setActiveView] = useState('chat'); // 'chat' | 'call' | 'mentor-profile' | 'user-profile'
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleSelectMentor = (mentor) => {
    setCurrentMentor(mentor);
    // Clear unread red dot on click
    setMentors(prev => prev.map(m => m.id === mentor.id ? { ...m, unread: false } : m));
    setActiveView('chat');
  };

  const handleEndCall = () => {
    // Run long-term memory extraction worker post-session
    const updatedProfile = runMemoryExtractionWorker(
      { vocabLearned: ['l\'addition', 's\'il vous plaît'] },
      userProfile
    );
    setUserProfile(updatedProfile);
    setActiveView('chat');
  };

  return (
    <div className="flex h-screen w-screen bg-slate-950 text-slate-100 font-sans overflow-hidden">
      {/* Sidebar Navigation */}
      <Sidebar 
        mentors={mentors}
        currentMentor={currentMentor}
        onSelectMentor={handleSelectMentor}
        userProfile={userProfile}
        onOpenUserProfile={() => setActiveView('user-profile')}
        isOpen={sidebarOpen}
        onCloseMobile={() => setSidebarOpen(false)}
      />

      {/* Main Active View Shell */}
      <main className="flex-1 flex flex-col h-full relative">
        <ChatWindow 
          mentor={currentMentor}
          onOpenMentorProfile={() => setActiveView('mentor-profile')}
          onStartCall={() => setActiveView('call')}
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          userProfile={userProfile}
          onUpdateUserProfile={setUserProfile}
        />
      </main>

      {/* Full-Screen Voice Call Walking Mode */}
      {activeView === 'call' && (
        <VoiceCall 
          mentor={currentMentor}
          onEndCall={handleEndCall}
        />
      )}

      {/* Mentor Dossier Modal */}
      {activeView === 'mentor-profile' && (
        <MentorProfile 
          mentor={currentMentor}
          onClose={() => setActiveView('chat')}
        />
      )}

      {/* User Profile & RPG Stat Chart Modal */}
      {activeView === 'user-profile' && (
        <UserProfile 
          userProfile={userProfile}
          stats={stats}
          onSave={setUserProfile}
          onClose={() => setActiveView('chat')}
        />
      )}
    </div>
  );
}
