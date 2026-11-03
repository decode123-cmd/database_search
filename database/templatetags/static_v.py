import hashlib
import os

from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()

_digests = {}   # file -> ((modified time, size), digest), so a file is only read again when it changes


def _source(path):
    """The file behind a static URL: DEBUG serves STATIC_ROOT, and the copy in a STATICFILES_DIRS folder is the fallback."""
    for root in [settings.STATIC_ROOT, *settings.STATICFILES_DIRS]:
        candidate = os.path.join(root, path) if root else None
        if candidate and os.path.isfile(candidate):
            return candidate
    return None


@register.simple_tag
def static_v(path):
    """Like {% static %}, but adds ?v=<hash of the file>. The files are sent without cache headers, so browsers keep an old
    copy for weeks; a new address after every change makes them load the new file."""
    url = static(path)
    source = _source(path)
    if source is None:
        return url
    stat = os.stat(source)
    signature = (stat.st_mtime_ns, stat.st_size)
    if _digests.get(source, (None,))[0] != signature:
        with open(source, 'rb') as handle:
            _digests[source] = (signature, hashlib.sha256(handle.read()).hexdigest()[:10])
    return f'{url}?v={_digests[source][1]}'
