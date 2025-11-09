from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from users.models import User

class AccountTokenAuthentication(TokenAuthentication):
    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)
        
        if not hasattr(user, 'account'):
            raise AuthenticationFailed('User has no account association')
            
        return (user, token)