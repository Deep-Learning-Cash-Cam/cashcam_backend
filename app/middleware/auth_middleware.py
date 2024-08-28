# from fastapi import Request, HTTPException
# from app.core.security import verify_token, create_access_token

# # NOT FINISHED!

# # Middleware to refresh tokens
# async def refresh_tokens(request: Request, call_next):
#     # Get the token from the request's Authorization header
#     access_token = request.headers.get("Authorization")
    
#     if access_token and access_token.startswith("Bearer "):
#         access_token = access_token.split(" ")[1]
#         payload = verify_token(access_token)
        
#         if payload is None: # Token is invalid or expired, try to refresh using the refresh token
#             refresh_token = request.cookies.get("refresh_token") # Get the refresh token from the cookies
#             if refresh_token:
#                 new_payload = verify_token(refresh_token, token_type="refresh")
#                 if new_payload: # Refresh token is valid
#                     # Create a new access token and set the user in the request state (user id and email)
#                     new_access_token = create_access_token({"sub": new_payload.id, "email": new_payload.email})
#                     request.state.user = new_payload
#                     response = await call_next(request)
#                     response.headers["New-Access-Token"] = new_access_token
#                     return response
                
#             raise HTTPException(status_code=401, detail="Token has expired")
        
#         request.state.user = payload
#     return await call_next(request)