from django.conf import settings


class SettingsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # settings configuration params
        request.settings_params = {
            'meta_description': settings.META_DESCRIPTION,
            'meta_author': settings.META_AUTHOR,
            'lang': settings.LANGUAGE_CODE,
        }

        response = self.get_response(request)
        return response
