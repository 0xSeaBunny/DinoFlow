import os
import json
import time
import hashlib
from typing import List, Dict, Any, Optional

DEFAULT_MEMORY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "SavedInfo", "Memory")
os.makedirs(DEFAULT_MEMORY_DIR, exist_ok=True)

_agent_memories = {}


def get_agent_memory_dir(agent_name: str) -> str:
    agent_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "SavedInfo", "AgentFolders", agent_name.replace(' ', '_'))
    os.makedirs(agent_dir, exist_ok=True)
    memory_dir = os.path.join(agent_dir, "Memory")
    os.makedirs(memory_dir, exist_ok=True)
    return memory_dir


class EpisodicMemory:
    def __init__(self, memory_dir: str = None):
        self.memory_dir = memory_dir or DEFAULT_MEMORY_DIR
        self.episodic_file = os.path.join(self.memory_dir, "episodic_memory.json")
        self.memories = self._load_memories()
    
    def _load_memories(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.episodic_file):
            try:
                with open(self.episodic_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []
    
    def _save_memories(self):
        try:
            with open(self.episodic_file, "w", encoding="utf-8") as f:
                json.dump(self.memories, f, indent=2)
        except Exception as e:
            print(f"[Memory] Failed to save memories: {e}")
    
    def add_memory(self, summary: str, context: Dict[str, Any], importance: float = 1.0):
        memory = {
            "id": hashlib.md5(f"{summary}{time.time()}".encode()).hexdigest()[:12],
            "timestamp": time.time(),
            "last_accessed": time.time(),
            "summary": summary,
            "context": context,
            "importance": importance,
            "access_count": 0
        }
        self.memories.append(memory)
        self._save_memories()
        return memory["id"]
    
    def retrieve_relevant(self, query: str, top_k: int = 5, recency_weight: float = 0.4) -> List[Dict[str, Any]]:
        if not self.memories:
            return []
        

        k1 = 1.5
        b = 0.75
        

        decay_hours = 24
        decay_seconds = decay_hours * 3600
        access_bonus_multiplier = 2.0
        
        query_terms = query.lower().split()
        if not query_terms:
            return []
        
        N = len(self.memories)
        doc_data = []
        total_doc_length = 0
        term_doc_count = {}
        
        for memory in self.memories:
            summary = memory.get("summary", "").lower()
            terms = summary.split()
            doc_length = len(terms)
            total_doc_length += doc_length
            term_freq = {}
            for term in terms:
                term_freq[term] = term_freq.get(term, 0) + 1
            for term in set(terms):
                term_doc_count[term] = term_doc_count.get(term, 0) + 1
            
            doc_data.append((memory, term_freq, doc_length))
        avgdl = total_doc_length / N if N > 0 else 1
        current_time = time.time()
        scored_memories = []
        touched_memories = []
        
        for memory, term_freq, doc_length in doc_data:
            relevance_score = 0.0
            for term in query_terms:
                n_q = term_doc_count.get(term, 0)
                if n_q == 0:
                    continue
                idf = ((N - n_q + 0.5) / (n_q + 0.5))
                if idf > 0:
                    idf = idf ** 0.5
                f_qd = term_freq.get(term, 0)
                tf_component = (f_qd * (k1 + 1)) / (f_qd + k1 * (1 - b + b * (doc_length / avgdl)))
                relevance_score += idf * tf_component
            importance = memory.get("importance", 1.0)
            relevance_score *= importance
            last_accessed = memory.get("last_accessed", memory.get("timestamp", current_time))
            access_count = memory.get("access_count", 0)
            time_since_access = current_time - last_accessed
            effective_decay_seconds = decay_seconds * (1 + access_count * access_bonus_multiplier)
            import math
            lambda_decay = math.log(2) / effective_decay_seconds
            recency_score = math.exp(-lambda_decay * time_since_access)
            normalized_relevance = min(relevance_score / 10.0, 1.0)
            relevance_weight = 1.0 - recency_weight
            final_score = (normalized_relevance * relevance_weight) + (recency_score * recency_weight)
            scored_memories.append((final_score, memory))
            if final_score > 0.01:
                touched_memories.append(memory)
        
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        result = [m for s, m in scored_memories[:top_k] if s > 0.01]
        for memory in touched_memories[:top_k]:
            memory["last_accessed"] = current_time
            memory["access_count"] = memory.get("access_count", 0) + 1
        if touched_memories[:top_k]:
            self._save_memories()
        
        return result
    
    def get_recent(self, n: int = 5) -> List[Dict[str, Any]]:
        return sorted(self.memories, key=lambda x: x["timestamp"], reverse=True)[:n]
    
    def delete_memory(self, memory_id: str) -> bool:
        for i, memory in enumerate(self.memories):
            if memory.get("id") == memory_id:
                self.memories.pop(i)
                self._save_memories()
                return True
        return False
    
    def clear_all(self):
        self.memories = []
        self._save_memories()
    
    def consolidate_memories(self, similarity_threshold: float = 0.8):
        if len(self.memories) < 2:
            return 0
        import math
        
        def jaccard_similarity(text1: str, text2: str) -> float:
            set1 = set(text1.lower().split())
            set2 = set(text2.lower().split())
            if not set1 or not set2:
                return 0.0
            intersection = len(set1 & set2)
            union = len(set1 | set2)
            return intersection / union if union > 0 else 0.0
        
        merged_count = 0
        new_memories = []
        processed = set()
        
        for i, memory in enumerate(self.memories):
            if i in processed:
                continue
            summary_i = memory.get("summary", "")
            if not summary_i:
                continue
            similar_group = [memory]
            for j, other in enumerate(self.memories[i+1:], start=i+1):
                if j in processed:
                    continue
                summary_j = other.get("summary", "")
                if not summary_j:
                    continue
                similarity = jaccard_similarity(summary_i, summary_j)
                if similarity >= similarity_threshold:
                    similar_group.append(other)
                    processed.add(j)
            
            if len(similar_group) > 1:
                newest_time = max(m.get("timestamp", 0) for m in similar_group)
                base_memory = max(similar_group, key=lambda m: len(m.get("summary", "")))
                base_summary = base_memory.get("summary", "")
                total_importance = sum(m.get("importance", 1.0) for m in similar_group)
                merged_importance = min(total_importance, 2.0)
                merged_context = {}
                for m in similar_group:
                    ctx = m.get("context", {})
                    if isinstance(ctx, dict):
                        merged_context.update(ctx)
                
                consolidated = {
                    "id": hashlib.md5(f"{base_summary}{newest_time}".encode()).hexdigest()[:12],
                    "timestamp": newest_time,
                    "summary": base_summary,
                    "context": merged_context,
                    "importance": merged_importance,
                    "consolidated_from": len(similar_group)
                }
                new_memories.append(consolidated)
                merged_count += len(similar_group) - 1
            else:
                new_memories.append(memory)
            
            processed.add(i)
        if merged_count > 0:
            self.memories = new_memories
            self._save_memories()
        
        return merged_count
    
    def auto_consolidate(self, max_memories: int = 100):
        if len(self.memories) > max_memories:
            return self.consolidate_memories(similarity_threshold=0.8)
        return 0


class SkillLessons:
    def __init__(self, memory_dir: str = None):
        self.memory_dir = memory_dir or DEFAULT_MEMORY_DIR
        self.skills_file = os.path.join(self.memory_dir, "skill_lessons.json")
        self.lessons = self._load_lessons()
    
    def _load_lessons(self) -> Dict[str, List[Dict[str, Any]]]:
        if os.path.exists(self.skills_file):
            try:
                with open(self.skills_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_lessons(self):
        try:
            with open(self.skills_file, "w", encoding="utf-8") as f:
                json.dump(self.lessons, f, indent=2)
        except Exception as e:
            print(f"[Memory] Failed to save lessons: {e}")
    
    def add_lesson(self, skill_name: str, error: str, lesson: str, solution: str):
        if skill_name not in self.lessons:
            self.lessons[skill_name] = []
        
        self.lessons[skill_name].append({
            "timestamp": time.time(),
            "error": error,
            "lesson": lesson,
            "solution": solution
        })
        self.lessons[skill_name] = self.lessons[skill_name][-10:]
        self._save_lessons()
    
    def get_lessons(self, skill_name: str) -> List[Dict[str, Any]]:
        return self.lessons.get(skill_name, [])
    
    def get_all_lessons_text(self) -> str:
        if not self.lessons:
            return ""
        
        text_parts = ["## Lessons Learned from Past Tasks:"]
        for skill, lessons in self.lessons.items():
            text_parts.append(f"\n### {skill}:")
            for lesson in lessons[-3:]:
                text_parts.append(f"- {lesson['lesson']}")
        
        return "\n".join(text_parts)
    
    def clear_lessons(self):
        self.lessons = {}
        self._save_lessons()


class UserPreferences:
    def __init__(self, memory_dir: str = None):
        self.memory_dir = memory_dir or DEFAULT_MEMORY_DIR
        self.prefs_file = os.path.join(self.memory_dir, "preferences.json")
        self.preferences = self._load_preferences()
    
    def _load_preferences(self) -> Dict[str, Any]:
        if os.path.exists(self.prefs_file):
            try:
                with open(self.prefs_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {
            "style_preferences": [],
            "common_corrections": [],
            "preferred_tools": [],
            "avoided_patterns": []
        }
    
    def _save_preferences(self):
        try:
            with open(self.prefs_file, "w", encoding="utf-8") as f:
                json.dump(self.preferences, f, indent=2)
        except Exception as e:
            print(f"[Memory] Failed to save preferences: {e}")
    
    def record_correction(self, original: str, corrected: str, reason: Optional[str] = None):
        self.preferences["common_corrections"].append({
            "timestamp": time.time(),
            "original": original,
            "corrected": corrected,
            "reason": reason
        })
        if "concise" in corrected.lower() or "shorter" in corrected.lower():
            self._add_style_pref("be_concise")
        if "more detail" in corrected.lower() or "elaborate" in corrected.lower():
            self._add_style_pref("be_detailed")
        
        self._save_preferences()
    
    def _add_style_pref(self, pref: str):
        if pref not in self.preferences["style_preferences"]:
            self.preferences["style_preferences"].append(pref)
    
    def get_preferences_prompt(self) -> str:
        prefs = []
        if "be_concise" in self.preferences["style_preferences"]:
            prefs.append("Be concise and to the point.")
        if "be_detailed" in self.preferences["style_preferences"]:
            prefs.append("Provide detailed explanations.")
        
        for corr in self.preferences["common_corrections"][-5:]:
            if corr.get("reason"):
                prefs.append(corr["reason"])
        
        if prefs:
            return "\nUser Preferences:\n" + "\n".join(f"- {p}" for p in prefs)
        return ""


class PatternDetector:
    def __init__(self, memory_dir: str = None):
        self.memory_dir = memory_dir or DEFAULT_MEMORY_DIR
        self.patterns_file = os.path.join(self.memory_dir, "detected_patterns.json")
        self.patterns = self._load_patterns()
        self.current_session_actions = []
    
    def _load_patterns(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.patterns_file):
            try:
                with open(self.patterns_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []
    
    def _save_patterns(self):
        try:
            with open(self.patterns_file, "w", encoding="utf-8") as f:
                json.dump(self.patterns, f, indent=2)
        except Exception as e:
            print(f"[Memory] Failed to save patterns: {e}")
    
    def record_action(self, action_type: str, details: Dict[str, Any]):
        self.current_session_actions.append({
            "type": action_type,
            "details": details,
            "timestamp": time.time()
        })
    
    def detect_patterns(self) -> Optional[Dict[str, Any]]:
        if len(self.current_session_actions) < 5:
            return None
        action_counts = {}
        action_counts = {}
        for action in self.current_session_actions:
            key = action["type"]
            action_counts[key] = action_counts.get(key, 0) + 1
        
        for action_type, count in action_counts.items():
            if count >= 3:
                existing = any(p["action_type"] == action_type for p in self.patterns)
                if not existing:
                    pattern = {
                        "id": hashlib.md5(f"{action_type}{time.time()}".encode()).hexdigest()[:8],
                        "action_type": action_type,
                        "occurrences": count,
                        "timestamp": time.time(),
                        "proposed_skill": f"automated_{action_type}",
                        "status": "detected"
                    }
                    self.patterns.append(pattern)
                    self._save_patterns()
                    return pattern
        
        return None
    
    def get_pending_patterns(self) -> List[Dict[str, Any]]:
        return [p for p in self.patterns if p["status"] == "detected"]
    
    def approve_pattern(self, pattern_id: str):
        for p in self.patterns:
            if p["id"] == pattern_id:
                p["status"] = "approved"
                self._save_patterns()
                return p
        return None
    
    def clear_session(self):
        self.current_session_actions = []


_agent_memory_instances = {}
_current_agent_context = {"agent_name": None}


def set_current_agent(agent_name: str):
    global _current_agent_context
    _current_agent_context["agent_name"] = agent_name


def get_current_agent() -> Optional[str]:
    return _current_agent_context.get("agent_name")


def get_agent_memory_instances(agent_name: str) -> Dict[str, Any]:
    global _agent_memory_instances
    
    if agent_name not in _agent_memory_instances:
        memory_dir = get_agent_memory_dir(agent_name)
        _agent_memory_instances[agent_name] = {
            "episodic": EpisodicMemory(memory_dir),
            "skills": SkillLessons(memory_dir),
            "preferences": UserPreferences(memory_dir),
            "patterns": PatternDetector(memory_dir)
        }
    
    return _agent_memory_instances[agent_name]


def get_episodic_memory(agent_name: str) -> EpisodicMemory:
    if not agent_name:
        raise ValueError("agent_name is required")
    return get_agent_memory_instances(agent_name)["episodic"]


def get_skill_lessons(agent_name: str) -> SkillLessons:
    if not agent_name:
        raise ValueError("agent_name is required")
    return get_agent_memory_instances(agent_name)["skills"]


def get_user_preferences(agent_name: str) -> UserPreferences:
    if not agent_name:
        raise ValueError("agent_name is required")
    return get_agent_memory_instances(agent_name)["preferences"]


def get_pattern_detector(agent_name: str) -> PatternDetector:
    if not agent_name:
        raise ValueError("agent_name is required")
    return get_agent_memory_instances(agent_name)["patterns"]


def get_memory_context_for_prompt(query: str, agent_name: str) -> str:
    if not agent_name:
        raise ValueError("agent_name is required")
    parts = []
    memories = get_episodic_memory(agent_name).retrieve_relevant(query, top_k=3)
    if memories:
        parts.append("## Relevant Past Interactions:")
        for m in memories:
            parts.append(f"- {m['summary']}")
    
    lessons = get_skill_lessons(agent_name).get_all_lessons_text()
    if lessons:
        parts.append(lessons)
    prefs = get_user_preferences(agent_name).get_preferences_prompt()
    if prefs:
        parts.append(prefs)
    
    if parts:
        return "\n\n".join(parts) + "\n\n"
    return ""


def summarize_conversation(messages: List[Dict[str, str]]) -> str:
    if not messages:
        return ""
    user_msgs = [m["content"] for m in messages if m.get("role") == "user"]
    assistant_msgs = [m["content"] for m in messages if m.get("role") == "assistant"]
    if not user_msgs:
        return ""
    summary = f"User asked: {user_msgs[0][:100]}"
    if assistant_msgs:
        summary += f" | Assistant responded with: {assistant_msgs[0][:100]}"
    
    return summary


def clear_agent_memory(agent_name: str):
    memory_dir = get_agent_memory_dir(agent_name)
    episodic = get_episodic_memory(agent_name)
    episodic.clear_all()
    
    skills = get_skill_lessons(agent_name)
    skills.clear_lessons()
    
    global _agent_memory_instances
    if agent_name in _agent_memory_instances:
        del _agent_memory_instances[agent_name]
    
    try:
        import shutil
        if os.path.exists(memory_dir):
            shutil.rmtree(memory_dir)
    except Exception as e:
        print(f"[Memory] Failed to remove memory directory: {e}")
