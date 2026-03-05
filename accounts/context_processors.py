# accounts/context_processors.py

from .models import UserProfile


def user_profile(request):
    if request.user.is_authenticated:
        userprofile, _ = UserProfile.objects.get_or_create(user=request.user)
        return {'userprofile': userprofile}
    return {'userprofile': None}