from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status
from users.models import User
from .serializers import UserSerializer  # ADD THIS IMPORT

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        # Accept both username and email fields
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        
        # Determine which field to use for lookup
        lookup_field = email if email else username
        
        if not lookup_field or not password:
            return Response(
                {'error': 'Must include "username/email" and "password".'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Try to get user by email or username
            user = User.objects.get(email=lookup_field)
            
            if user.check_password(password):
                token, created = Token.objects.get_or_create(user=user)
                
                # Use the serializer to get proper user data including account
                user_data = UserSerializer(user).data
                
                return Response({
                    'token': token.key,
                    'user': user_data  # RETURN FULL USER OBJECT
                })
            else:
                return Response(
                    {'error': 'Invalid credentials'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid credentials'}, 
                status=status.HTTP_400_BAD_REQUEST
            )