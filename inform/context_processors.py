# inform/context_processors.py

from django.conf import settings

def base_url(request):
    print("base url", settings.BASE_URL)
    return {'BASE_URL': settings.BASE_URL}
