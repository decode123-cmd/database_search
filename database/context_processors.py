from django.conf import settings


def site(request):
    """Makes the database's name available to every template as {{ site_name }}."""
    return {'site_name': getattr(settings, 'SITE_NAME', 'CancerImmunoDB')}
