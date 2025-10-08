# middleware.py (create this file in your account app)
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.urls import reverse
from account.models import User

class BearerTokenMiddleware(MiddlewareMixin):
    """
    Middleware to check bearer token authentication for frontend views
    Automatically validates user's login status on every request
    """
    
    # URLs that don't require authentication
    EXEMPT_URLS = [
        '/',
        '/login/',
        '/signup/',
        '/admin/',
        '/static/',
        '/media/',
    ]
    
    def process_request(self, request):
        # Skip authentication for exempt URLs
        path = request.path
        for exempt_url in self.EXEMPT_URLS:
            if path.startswith(exempt_url):
                return None
        
        # Check if user is authenticated via Django session
        if request.user.is_authenticated:
            try:
                # Verify bearer token exists and user is logged in
                user = User.objects.get(id=request.user.id)
                

                # Check if bearer token exists
                if not user.bearer_token:
                    # Logout user if no bearer token
                    from django.contrib.auth import logout
                    logout(request)
                    return redirect('login_page')
                
                # Check if user is logged in
                if not user.is_logged_in:
                    # Logout user if marked as logged out
                    from django.contrib.auth import logout
                    logout(request)
                    return redirect('login_page')
                
                # User is valid, continue
                return None
                
            except User.DoesNotExist:
                return redirect('login_page')
        else:
            # User not authenticated, redirect to login
            return redirect('login_page')
        
        return None