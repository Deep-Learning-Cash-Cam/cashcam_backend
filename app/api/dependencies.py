import logging
from app.core.security import verify_jwt_token
from app.logs.logger_config import log
from typing import Annotated
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.crud import get_user
from app.db.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
db_dependancy = Annotated[Session, Depends(get_db)]

# Get current user from the request's state or from the token in the request's Authorization header
async def get_current_user(request: Request, db: db_dependancy):
    try:
        # Check if the user is already in the request's state
        if hasattr(request.state, 'user') and request.state.user and "id" in request.state.user:
            log(f"User found in request state", logging.INFO, debug=True)
            return get_user(db, user_id=request.state.user["id"])
        
        # Else, get token from the request's Authorization header
        token = request.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            try: # Try to verify the token
                payload = verify_jwt_token(token.split()[1])
                if payload is None: # token is invalid, return None
                    log(f"Token is invalid", logging.INFO, debug=True)
                    return None
                
                # Get the user_id and email from the token
                user_id: str = payload.get("sub")
                user_email: str = payload.get("email")
                if not user_id or not user_email:
                    log(f"Token is missing fields", logging.INFO, debug=True)
                    return None # Return None if fields are missing
                
                # Get the user from the database
                user = get_user(db, user_id, email=user_email)
                if not user:
                    log(f"User not found in the database", logging.INFO, debug=True)
                    return None # User not in the database
                
                # User found, add to request and return it
                request.state.user = {"id" : user_id}
                
                log(f"User found in request token", logging.INFO, debug=True)
                return user
            except Exception as e:
                log(f"Error during token verification in get_current_user - {str(e)}", logging.ERROR, debug=True)
        else: # No auth token found
            return None
    except Exception as e:
        log(f"Error during get_current_user - {str(e)}", logging.ERROR, debug=True)
        return None