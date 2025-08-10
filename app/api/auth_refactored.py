"""
Authentication and authorization module with clean architecture
"""
from __future__ import annotations
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from jose import JWTError, jwt

from app.db.base import get_db
from app.models import User
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# ==================== Data Transfer Objects ====================

class UserRegistration(BaseModel):
    """Data required for user registration"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, regex="^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=8, max_length=100)


class UserProfile(BaseModel):
    """Public user profile information"""
    id: int
    email: str
    username: str
    is_active: bool
    is_superuser: bool = False
    
    class Config:
        orm_mode = True


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TokenPayload(BaseModel):
    """JWT token payload structure"""
    sub: str  # Subject (username)
    exp: Optional[int] = None  # Expiration time
    iat: Optional[int] = None  # Issued at time


# ==================== Service Layer ====================

class AuthenticationService:
    """Handle authentication business logic"""
    
    @staticmethod
    def authenticate_user(
        username: str,
        password: str,
        db: Session
    ) -> Optional[User]:
        """
        Authenticate a user with username and password
        Returns the user if authentication succeeds, None otherwise
        """
        user = UserRepository.get_user_by_username(username, db)
        
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        return user
    
    @staticmethod
    def create_user_account(
        registration_data: UserRegistration,
        db: Session
    ) -> User:
        """
        Create a new user account
        Raises HTTPException if username or email already exists
        """
        # Check for existing user
        if UserRepository.get_user_by_email(registration_data.email, db):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        if UserRepository.get_user_by_username(registration_data.username, db):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create new user
        hashed_password = get_password_hash(registration_data.password)
        
        new_user = User(
            email=registration_data.email,
            username=registration_data.username,
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=False
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_user
    
    @staticmethod
    def generate_user_token(user: User) -> TokenResponse:
        """
        Generate JWT token for authenticated user
        """
        token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=token_expires
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
        )


class TokenService:
    """Handle JWT token operations"""
    
    @staticmethod
    def decode_token(token: str) -> TokenPayload:
        """
        Decode and validate JWT token
        Raises HTTPException if token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            username = payload.get("sub")
            if not username:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            return TokenPayload(**payload)
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )


# ==================== Repository Layer ====================

class UserRepository:
    """Database operations for User model"""
    
    @staticmethod
    def get_user_by_email(email: str, db: Session) -> Optional[User]:
        """Find user by email address"""
        return db.query(User).filter(
            User.email == email
        ).first()
    
    @staticmethod
    def get_user_by_username(username: str, db: Session) -> Optional[User]:
        """Find user by username"""
        return db.query(User).filter(
            User.username == username
        ).first()
    
    @staticmethod
    def get_user_by_id(user_id: int, db: Session) -> Optional[User]:
        """Find user by ID"""
        return db.query(User).filter(
            User.id == user_id
        ).first()


# ==================== Dependencies ====================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token
    """
    token_payload = TokenService.decode_token(token)
    
    user = UserRepository.get_user_by_username(
        username=token_payload.sub,
        db=db
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    
    return user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current user if they are a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return current_user


# ==================== API Endpoints ====================

@router.post("/register", response_model=UserProfile)
async def register_user(
    registration_data: UserRegistration,
    db: Session = Depends(get_db)
) -> UserProfile:
    """
    Register a new user account
    
    Requirements:
    - Email must be unique
    - Username must be unique
    - Password must be at least 8 characters
    """
    new_user = AuthenticationService.create_user_account(
        registration_data=registration_data,
        db=db
    )
    
    return UserProfile(
        id=new_user.id,
        email=new_user.email,
        username=new_user.username,
        is_active=new_user.is_active,
        is_superuser=new_user.is_superuser
    )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> TokenResponse:
    """
    Login with username and password
    
    Returns JWT access token on successful authentication
    """
    user = AuthenticationService.authenticate_user(
        username=form_data.username,
        password=form_data.password,
        db=db
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return AuthenticationService.generate_user_token(user)


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> UserProfile:
    """
    Get the current authenticated user's profile
    """
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    current_user: User = Depends(get_current_user)
) -> TokenResponse:
    """
    Refresh the access token for the current user
    """
    return AuthenticationService.generate_user_token(current_user)


@router.post("/logout")
async def logout_user() -> dict:
    """
    Logout the current user
    
    Note: With JWT, actual logout is handled client-side by removing the token
    This endpoint is for consistency and future session management
    """
    return {"message": "Successfully logged out"}