# authentication.py (create this file in your account app)
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from account.models import User

class BearerTokenAuthentication(BaseAuthentication):
    """
    Custom authentication class that validates bearer tokens
    Only allows access if user has valid token AND is logged in
    """
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return None
        
        try:
            # Expected format: "Bearer <token>"
            auth_parts = auth_header.split()
            
            if len(auth_parts) != 2 or auth_parts[0].lower() != 'bearer':
                raise AuthenticationFailed('Invalid authorization header format')
            
            token = auth_parts[1]
            
            # Look up user by bearer token
            try:
                user = User.objects.get(bearer_token=token, is_active=True)
            except User.DoesNotExist:
                raise AuthenticationFailed('Invalid bearer token')
            
            # Check if user is logged in
            if not user.is_logged_in:
                raise AuthenticationFailed('User is not logged in. Please login first.')
            
            return (user, None)
            
        except AuthenticationFailed:
            raise
        except Exception as e:
            raise AuthenticationFailed(str(e))
    
    def authenticate_header(self, request):
        return 'Bearer'