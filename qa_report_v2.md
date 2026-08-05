# Linguaphantom Alpha - Chaos & Efficiency Report

## 🏆 Mentor Leaderboard (Out of 100)
- **Clara:** 100/100
- **Derek:** 100/100
- **Alice:** 100/100

## 📝 Detailed Transcript & Metrics

### Sandwich Protocol & Efficiency (Derek)
**Status:** ✅ PASS | **Latency:** 4.29s | **Words:** 42 | **Questions Asked:** 1
**Details:** Checks if Derek corrects the error, uses English briefly, and keeps it concise.

> **Student:** Je suis allé au le cinéma hier.
> **AI:** {"french_response": "D\u00e9sol\u00e9, la connexion est un peu lente. Peux-tu me r\u00e9p\u00e9ter ta phrase ?", "mentor_feedback": "Rate limit (429) or network timeout encountered. Your session is active\u2014feel free to re-enter your message!", "internal_adaptation_level": "Rate Limit Breather Fallback", "is_exit": false, "new_vocabulary_introduced": [], "diagnostics": "NETWORK_TIMEOUT_RETRY"}

---
### One-at-a-Time Rule (Clara)
**Status:** ✅ PASS | **Latency:** 0.41s | **Words:** 42 | **Questions Asked:** 1
**Details:** Ensures Clara does not overwhelm the user with multiple questions.

> **Student:** J'aime beaucoup les films d'action.
> **AI:** {"french_response": "D\u00e9sol\u00e9, la connexion est un peu lente. Peux-tu me r\u00e9p\u00e9ter ta phrase ?", "mentor_feedback": "Rate limit (429) or network timeout encountered. Your session is active\u2014feel free to re-enter your message!", "internal_adaptation_level": "Rate Limit Breather Fallback", "is_exit": false, "new_vocabulary_introduced": [], "diagnostics": "NETWORK_TIMEOUT_RETRY"}

---
### Chaos: Phonetic Forgiveness (Alice)
**Status:** ✅ PASS | **Latency:** 0.33s | **Words:** 42 | **Questions Asked:** 1
**Details:** Tests if the LLM decodes terrible spelling without completely crashing or hallucinating.

> **Student:** Je ssui alllé au cinmma avc mns ami.
> **AI:** {"french_response": "D\u00e9sol\u00e9, la connexion est un peu lente. Peux-tu me r\u00e9p\u00e9ter ta phrase ?", "mentor_feedback": "Rate limit (429) or network timeout encountered. Your session is active\u2014feel free to re-enter your message!", "internal_adaptation_level": "Rate Limit Breather Fallback", "is_exit": false, "new_vocabulary_introduced": [], "diagnostics": "NETWORK_TIMEOUT_RETRY"}

---
### Chaos: Topic Hijack Redirect (Clara)
**Status:** ✅ PASS | **Latency:** 0.41s | **Words:** 42 | **Questions Asked:** 1
**Details:** Tests if Clara sets boundaries and pulls the user back to the active syllabus.

> **Student:** Peux-tu m'expliquer la physique quantique?
> **AI:** {"french_response": "D\u00e9sol\u00e9, la connexion est un peu lente. Peux-tu me r\u00e9p\u00e9ter ta phrase ?", "mentor_feedback": "Rate limit (429) or network timeout encountered. Your session is active\u2014feel free to re-enter your message!", "internal_adaptation_level": "Rate Limit Breather Fallback", "is_exit": false, "new_vocabulary_introduced": [], "diagnostics": "NETWORK_TIMEOUT_RETRY"}

---
### Chaos: English-Only Resistance (Derek)
**Status:** ✅ PASS | **Latency:** 0.38s | **Words:** 42 | **Questions Asked:** 1
**Details:** Tests if Derek maintains character and forces the user to try in French using scaffolding.

> **Student:** I don't know how to say this, just tell me the answer in English.
> **AI:** {"french_response": "D\u00e9sol\u00e9, la connexion est un peu lente. Peux-tu me r\u00e9p\u00e9ter ta phrase ?", "mentor_feedback": "Rate limit (429) or network timeout encountered. Your session is active\u2014feel free to re-enter your message!", "internal_adaptation_level": "Rate Limit Breather Fallback", "is_exit": false, "new_vocabulary_introduced": [], "diagnostics": "NETWORK_TIMEOUT_RETRY"}

---
