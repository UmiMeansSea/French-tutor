// LinguaPhantom API & Interactions Service

export const INITIAL_MENTORS = [
  {
    id: 'clara',
    name: 'Clara',
    role: 'Vibrant Expat Friend 🌸',
    avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
    backstory: 'Born in the US, moved to France during school. Relatable, quirky, bilingual, empathetic, and a great active listener.',
    perks: 'Boosts Charm & Knowledge. Unlocks Indie Record Store & Park Bench Hangouts.',
    unread: true, // Red dot badge
    hangoutUnlocked: true, // Green dot badge
    level: 4,
    xp: 280,
    nextLevelXp: 400,
    whatToImprove: [
      { category: 'Grammar', item: 'Passé composé vs. Imparfait distinction', priority: 'High' },
      { category: 'Vocabulary', item: 'Informal texting slang & conversational fillers', priority: 'Medium' },
      { category: 'Phonetics', item: 'Liaison in "les amis" [lez-ami]', priority: 'Low' }
    ]
  },
  {
    id: 'derek',
    name: 'Derek',
    role: 'Strict Purist Teacher 🎩',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80',
    backstory: 'Traditional native French speaker with pristine English used rarely. Meticulous, direct, fair, and academic grammar coach.',
    perks: 'Boosts Wit & Knowledge. Grants Red Pen Amnesty passes & University Courtyard Hangouts.',
    unread: false,
    hangoutUnlocked: false,
    level: 3,
    xp: 150,
    nextLevelXp: 300,
    whatToImprove: [
      { category: 'Grammar', item: 'Subjunctive mood triggers (il faut que...)', priority: 'High' },
      { category: 'Spelling', item: 'Accents placement (é, è, ê, ç)', priority: 'High' }
    ]
  },
  {
    id: 'alice',
    name: 'Alice',
    role: 'Eclectic Bibliophile 📚',
    avatar: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=150&auto=format&fit=crop&q=80',
    backstory: 'Avid reader devouring novels, legends, magazines, and history. Expressive French speaker sharing literary gems.',
    perks: 'Boosts Courage & Knowledge. Unlocks Secret Archives & Antiquarian Bookstore Hangouts.',
    unread: false,
    hangoutUnlocked: true,
    level: 5,
    xp: 420,
    nextLevelXp: 500,
    whatToImprove: [
      { category: 'Vocabulary', item: 'Classical literary idioms & descriptions', priority: 'Medium' },
      { category: 'Culture', item: 'Historical context of Parisian bridges', priority: 'Low' }
    ]
  }
];

export const INITIAL_USER_PROFILE = {
  name: 'Alex Vance',
  email: 'alex.vance@example.com',
  avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&auto=format&fit=crop&q=80',
  cefrLevel: 'A2',
  streakDays: 4,
  xpTotal: 850,
  badges: ['First Steps 🌟', 'Liaison Legend 🗣️', 'Streak Master 🔥'],
  weakSpots: ['Passé composé vs Imparfait', 'Gender of nouns (la table vs le livre)'],
  userMemories: [
    'Enjoys French indie music & Parisian café culture',
    'Learned vocabulary: l\'addition, s\'il vous plaît',
    'Goal: Travel to Lyon next summer'
  ]
};

export const INITIAL_STATS = {
  Knowledge: 35,
  Charm: 42,
  Wit: 28,
  Courage: 30,
  Memory: 25
};

// Google GenAI Interactions API Simulation Client
export async function sendInteractionMessage(mentorId, userText, previousInteractionId = null) {
  // Simulate network latency for API interaction chaining
  await new Promise(res => setTimeout(res, 800));

  const interactionId = `int_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
  
  let frenchResponse = "";
  let mentorFeedback = "";
  let phoneticBreakdown = "";

  const textLower = userText.toLowerCase();

  if (textLower.includes("slow down") || textLower.includes("too fast") || textLower.includes("plus lentement")) {
    frenchResponse = "Ah, pas de problème ! Je vais parler plus lentement pour toi. Est-ce que ça va mieux maintenant ?";
    mentorFeedback = "Speed adapted! I dropped my speaking rate so you can catch every syllable. Take your time!";
    phoneticBreakdown = "Pas de pro-blè-me | Je vais par-ler plus len-te-ment";
  } else if (textLower.includes("repeat") || textLower.includes("répète")) {
    frenchResponse = "Bien sûr ! Je disais : 'Comment s'est passée ta journée ?'";
    mentorFeedback = "Here is the exact sentence rephrased clearly with syllable separation.";
    phoneticBreakdown = "Com-ment s'est pas-sée ta jour-née";
  } else if (textLower.includes("hello") || textLower.includes("bonjour") || textLower.includes("hi")) {
    if (mentorId === 'clara') {
      frenchResponse = "Coucou ! Comment ça va aujourd'hui ? Tu as passé une bonne journée ?";
      mentorFeedback = "'Coucou' is a super friendly way to say hi to friends in France! You sound very natural.";
    } else if (mentorId === 'derek') {
      frenchResponse = "Bonjour. Je suis prêt pour notre leçon d'aujourd'hui. Avez-vous révisé vos verbes ?";
      mentorFeedback = "Note the use of 'Avez-vous' — formal inversion is key when maintaining polite respect.";
    } else {
      frenchResponse = "Enchantée ! Je lisais un magnifique poème sur Paris. Que souhaites-tu explorer aujourd'hui ?";
      mentorFeedback = "'Enchantée' adds a lovely touch of elegance to any greeting.";
    }
  } else {
    frenchResponse = `Très bien ! C'est une excellente réflexion. Continuons d'échanger en français sur ce sujet !`;
    mentorFeedback = `Great attempt! Remember to keep your subject and verb agreement consistent.`;
  }

  return {
    interactionId,
    previousInteractionId,
    frenchResponse,
    mentorFeedback,
    phoneticBreakdown,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  };
}

// Long-Term Memory Extraction Worker
export function runMemoryExtractionWorker(sessionMetrics, currentProfile) {
  const newMemories = [...currentProfile.userMemories];
  
  if (sessionMetrics.vocabLearned && sessionMetrics.vocabLearned.length > 0) {
    newMemories.push(`Mastered vocab: ${sessionMetrics.vocabLearned.join(', ')}`);
  }
  
  return {
    ...currentProfile,
    userMemories: Array.from(new Set(newMemories))
  };
}
