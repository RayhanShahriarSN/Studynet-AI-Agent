# views.py
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from account.serializers import *
from django.contrib.auth import authenticate
from account.renderers import *
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_protect
from .authentication import BearerTokenAuthentication
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache


class UserRegistrationView(APIView):
    permission_classes = [AllowAny]
    renderer_classes = [UserRenderer]
    
    def post(self, request, format=None):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()
            # Bearer token is auto-generated and saved in database automatically
            return Response({
                'msg': 'Registration Successful. Please login with your credentials.'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    permission_classes = [AllowAny]
    renderer_classes = [UserRenderer]
    
    
    def post(self, request, format=None):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            username = serializer.validated_data.get('username')
            password = serializer.validated_data.get('password')
                    
            # Step 1: Authenticate with username and password
            user = authenticate(username=username, password=password)
            
            if user is not None:
                # Step 2: Check if bearer token exists in database
                if user.bearer_token:
                    # Step 3: Mark user as logged in
                    user.login_user()
                    
                    # Step 4: Return bearer token for future requests
                    return Response({
                        'bearer_token': user.bearer_token,
                        'msg': 'Login Successful. Use this bearer token for accessing other pages.'
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'errors': {'non_field_errors': ['Bearer token not found. Please contact admin.']}
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'errors': {'non_field_errors': ['Username or password is not valid']}
                }, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(never_cache, name='dispatch')
class UserLogoutView(APIView):
    renderer_classes = [UserRenderer]
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, format=None):
        # Mark user as logged out
        request.user.logout_user()
        return Response({
            'msg': 'Logout Successful. Bearer token is now invalid until you login again.'
        }, status=status.HTTP_200_OK)


class UserProfileView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]
    authentication_classes = [BearerTokenAuthentication]
    
    def get(self, request, format=None):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)





# Frontend views
def login_page(request):
    return render(request, "login.html")


def signup_page(request):
    return render(request, "signup.html")



def login_page(request):
    token = ""
    form = LoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.bearer_token:
                user.login_user()
                login(request, user)
                request.session["token"] = user.bearer_token  # save token in session

                # ✅ Redirect to dashboard
                if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
                    return redirect("api:frontend")  # or your dashboard route
                else:
                    return redirect("api:user_page")  # example user route
            else:
                messages.error(request, "❌ Bearer token not found. Contact admin.")
        else:
            messages.error(request, "❌ Invalid username or password")

    # GET request or invalid POST
    return render(request, "login.html", {"form": form, "token": token})


# Redirect based on role


# Sign Up
User = get_user_model()


def signup_page(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            password2 = form.cleaned_data["password2"]

            if password != password2:
                messages.error(request, "Passwords do not match ❌")
                return render(request, "signup.html", {"form": form})

            # Check if username or email already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists ❌")
                return render(request, "signup.html", {"form": form})
            
            if User.objects.filter(email=email).exists():
                messages.error(request, "Email already exists ❌")
                return render(request, "signup.html", {"form": form})

            # Create Django user (bearer_token auto-generated and saved internally)
            user = User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, "✅ Registration successful! Please login.")
            return redirect("login_page")
    else:
        form = SignUpForm()

    return render(request, "signup.html", {"form": form})


@never_cache
def logout_page(request):
    if request.user.is_authenticated:
        # Mark user as logged out in database
        request.user.logout_user()
    logout(request)
    request.session.flush()
    return redirect("login_page")