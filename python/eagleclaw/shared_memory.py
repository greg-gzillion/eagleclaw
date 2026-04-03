"""
Shared memory system across all agents (rustypycraw, eagleclaw, crustyclaw, claw-coder)
"""

import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path

SHARED_MEMORY_DIR = Path.home() / ".claw_memory"
SHARED_MEMORY_DIR.mkdir(exist_ok=True)

DB_PATH = SHARED_MEMORY_DIR / "shared_memory.db"

class SharedMemory:
    """Cross-agent shared memory system"""
    
    def __init__(self):
        self._init_db()
    
    def _init_db(self):
        """Initialize shared database"""
        self.conn = sqlite3.connect(str(DB_PATH))
        self.cursor = self.conn.cursor()
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent TEXT,
                key TEXT,
                value TEXT,
                timestamp TEXT,
                tags TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_registry (
                agent_id TEXT PRIMARY KEY,
                name TEXT,
                repo TEXT,
                capabilities TEXT,
                last_seen TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent TEXT,
                question TEXT,
                answer TEXT,
                timestamp TEXT,
                session_id TEXT
            )
        ''')
        
        self.conn.commit()
    
    def remember(self, agent: str, key: str, value: str, tags: str = ""):
        """Store a memory accessible by all agents"""
        self.cursor.execute(
            "INSERT INTO memories (agent, key, value, timestamp, tags) VALUES (?, ?, ?, ?, ?)",
            (agent, key, value, datetime.now().isoformat(), tags)
        )
        self.conn.commit()
    
    def recall(self, key: str) -> list:
        """Retrieve memories by key (any agent)"""
        self.cursor.execute(
            "SELECT agent, key, value, tags FROM memories WHERE key LIKE ? ORDER BY timestamp DESC LIMIT 10",
            (f"%{key}%",)
        )
        return self.cursor.fetchall()
    
    def register_agent(self, agent_id: str, name: str, repo: str, capabilities: str):
        """Register an agent in the shared registry"""
        self.cursor.execute(
            "INSERT OR REPLACE INTO agent_registry VALUES (?, ?, ?, ?, ?)",
            (agent_id, name, repo, capabilities, datetime.now().isoformat())
        )
        self.conn.commit()
    
    def get_all_agents(self) -> list:
        """Get all registered agents"""
        self.cursor.execute("SELECT name, repo, capabilities FROM agent_registry")
        return self.cursor.fetchall()
    
    def log_conversation(self, agent: str, question: str, answer: str, session_id: str = ""):
        """Log conversation for cross-agent learning"""
        self.cursor.execute(
            "INSERT INTO conversations (agent, question, answer, timestamp, session_id) VALUES (?, ?, ?, ?, ?)",
            (agent, question, answer[:500], datetime.now().isoformat(), session_id)
        )
        self.conn.commit()
    
    def search_conversations(self, query: str) -> list:
        """Search past conversations across all agents"""
        self.cursor.execute(
            "SELECT agent, question, answer FROM conversations WHERE question LIKE ? OR answer LIKE ? ORDER BY timestamp DESC LIMIT 10",
            (f"%{query}%", f"%{query}%")
        )
        return self.cursor.fetchall()
    
    def get_stats(self) -> dict:
        """Get shared memory statistics"""
        self.cursor.execute("SELECT COUNT(*) FROM memories")
        memories_count = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM conversations")
        conversations_count = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM agent_registry")
        agents_count = self.cursor.fetchone()[0]
        
        return {
            "memories": memories_count,
            "conversations": conversations_count,
            "agents": agents_count
        }
    
    def close(self):
        """Close database connection"""
        self.conn.close()
