import threading

thread_local = threading.local()

class AccountMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Clean previous account
        if hasattr(thread_local, 'current_account'):
            del thread_local.current_account
        
        # Set account for authenticated users
        if request.user.is_authenticated and hasattr(request.user, 'account'):
            thread_local.current_account = request.user.account
            request.account = request.user.account
        
        response = self.get_response(request)
        return response

def get_current_account():
    return getattr(thread_local, 'current_account', None)