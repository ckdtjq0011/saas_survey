"""
User repository for managing user data access.
"""
from typing import Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base_repository import BaseRepository
from app.core.security import get_password_hash, verify_password


class UserRepository(BaseRepository[User]):
    """Repository for user-related database operations."""
    
    def __init__(self, db: Session):
        super().__init__(User, db)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.db.query(User).filter(User.username == username).first()
    
    def create_user(
        self,
        email: str,
        username: str,
        password: str,
        full_name: Optional[str] = None,
        **kwargs
    ) -> User:
        """Create a new user with hashed password."""
        hashed_password = get_password_hash(password)
        
        user = self.create(
            email=email,
            username=username,
            hashed_password=hashed_password,
            full_name=full_name,
            **kwargs
        )
        return user
    
    def authenticate(
        self,
        email_or_username: str,
        password: str
    ) -> Optional[User]:
        """Authenticate user by email/username and password."""
        # Try to find user by email first
        user = self.get_by_email(email_or_username)
        
        # If not found by email, try username
        if not user:
            user = self.get_by_username(email_or_username)
        
        # Verify password if user found
        if user and verify_password(password, user.hashed_password):
            return user
        
        return None
    
    def update_password(
        self,
        user_id: int,
        new_password: str
    ) -> Optional[User]:
        """Update user's password."""
        hashed_password = get_password_hash(new_password)
        return self.update(user_id, hashed_password=hashed_password)
    
    def activate_user(self, user_id: int) -> Optional[User]:
        """Activate a user account."""
        return self.update(user_id, is_active=True)
    
    def deactivate_user(self, user_id: int) -> Optional[User]:
        """Deactivate a user account."""
        return self.update(user_id, is_active=False)
    
    def email_exists(self, email: str) -> bool:
        """Check if email already exists."""
        return self.db.query(User).filter(User.email == email).count() > 0
    
    def username_exists(self, username: str) -> bool:
        """Check if username already exists."""
        return self.db.query(User).filter(User.username == username).count() > 0