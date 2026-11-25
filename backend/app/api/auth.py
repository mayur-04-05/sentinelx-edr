from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app import models, schemas
from backend.app.security import rbac

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(models.User).filter(models.User.username == user_in.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Auto-escalate first user to Admin for first-run setup convenience
    user_count = db.query(models.User).count()
    assigned_role = "Admin" if user_count == 0 else user_in.role
    
    hashed_pwd = rbac.get_password_hash(user_in.password)
    new_user = models.User(
        username=user_in.username,
        hashed_password=hashed_pwd,
        role=assigned_role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Log registration in Audit Log
    audit_entry = models.AuditLog(
        username=new_user.username,
        action="USER_REGISTERED",
        target=f"role={new_user.role}",
        result="SUCCESS"
    )
    db.add(audit_entry)
    db.commit()
    
    return new_user

@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not rbac.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password"
        )
    
    access_token = rbac.create_access_token(
        data={"sub": user.username, "role": user.role}
    )
    
    # Log login in Audit Log
    audit_entry = models.AuditLog(
        username=user.username,
        action="USER_LOGGED_IN",
        target=None,
        result="SUCCESS"
    )
    db.add(audit_entry)
    db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username,
        "role": user.role
    }
