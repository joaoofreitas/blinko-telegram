import sqlite3
import logging
from cryptography.fernet import Fernet
from typing import Optional

logger = logging.getLogger(__name__)

class UserStorage:
    """Handles secure storage and retrieval of user tokens."""
    
    def __init__(self, db_path: str = "./bot_data.db", encryption_key: Optional[str] = None):
        self.db_path = db_path
        
        # Initialize encryption
        if encryption_key:
            self.cipher = Fernet(encryption_key.encode())
        else:
            # Generate a key if none provided (for development)
            key = Fernet.generate_key()
            self.cipher = Fernet(key)
            logger.warning("Using auto-generated encryption key. This is not secure for production!")
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Initialize the SQLite database with user tokens and message tracking tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_tokens (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        encrypted_token TEXT NOT NULL,
                        blinko_url TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS note_messages (
                        user_id INTEGER,
                        message_id INTEGER,
                        chat_id INTEGER,
                        note_id TEXT,
                        note_type INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (user_id, message_id, chat_id)
                    )
                """)
                conn.commit()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def store_user_token(self, user_id: int, username: str, token: str, blinko_url: str = None) -> bool:
        """Store an encrypted user token."""
        try:
            encrypted_token = self.cipher.encrypt(token.encode()).decode()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO user_tokens 
                    (user_id, username, encrypted_token, blinko_url, updated_at) 
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (user_id, username, encrypted_token, blinko_url))
                conn.commit()
            
            logger.info(f"Token stored for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store token for user {user_id}: {e}")
            return False
    
    def get_user_token(self, user_id: int) -> Optional[str]:
        """Retrieve and decrypt a user token."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT encrypted_token FROM user_tokens WHERE user_id = ?", 
                    (user_id,)
                )
                result = cursor.fetchone()
                
                if result:
                    encrypted_token = result[0]
                    token = self.cipher.decrypt(encrypted_token.encode()).decode()
                    return token
                return None
        except Exception as e:
            logger.error(f"Failed to retrieve token for user {user_id}: {e}")
            return None
    
    def get_user_config(self, user_id: int) -> Optional[dict]:
        """Get full user configuration."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT encrypted_token, blinko_url, username, created_at 
                    FROM user_tokens WHERE user_id = ?
                """, (user_id,))
                result = cursor.fetchone()
                
                if result:
                    encrypted_token, blinko_url, username, created_at = result
                    token = self.cipher.decrypt(encrypted_token.encode()).decode()
                    return {
                        'token': token,
                        'blinko_url': blinko_url,
                        'username': username,
                        'created_at': created_at
                    }
                return None
        except Exception as e:
            logger.error(f"Failed to get config for user {user_id}: {e}")
            return None
    
    def remove_user_token(self, user_id: int) -> bool:
        """Remove a user's token."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM user_tokens WHERE user_id = ?", (user_id,))
                conn.commit()
            logger.info(f"Token removed for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove token for user {user_id}: {e}")
            return False
    
    def get_user_count(self) -> int:
        """Get total number of configured users."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM user_tokens")
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Failed to get user count: {e}")
            return 0
    
    def store_note_message(self, user_id: int, message_id: int, chat_id: int, note_id: str, note_type: int) -> bool:
        """Store a mapping between a telegram message and a blinko note for reply-to-update functionality."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO note_messages 
                    (user_id, message_id, chat_id, note_id, note_type) 
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, message_id, chat_id, note_id, note_type))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to store note message mapping: {e}")
            return False
    
    def get_note_from_reply(self, user_id: int, reply_to_message_id: int, chat_id: int) -> Optional[dict]:
        """Get note information from a reply to a bot message."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT note_id, note_type FROM note_messages 
                    WHERE user_id = ? AND message_id = ? AND chat_id = ?
                """, (user_id, reply_to_message_id, chat_id))
                result = cursor.fetchone()
                
                if result:
                    note_id, note_type = result
                    return {
                        'note_id': note_id,
                        'note_type': note_type
                    }
                return None
        except Exception as e:
            logger.error(f"Failed to get note from reply: {e}")
            return None
