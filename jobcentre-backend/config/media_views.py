import mimetypes
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404


PUBLIC_MEDIA_PREFIXES = ("jobs/", "avatars/")


def public_media(request, path):
    if not path.startswith(PUBLIC_MEDIA_PREFIXES):
        raise Http404

    relative_path = Path(path)

    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise Http404

    media_root = Path(settings.MEDIA_ROOT).resolve()
    file_path = (media_root / relative_path).resolve()

    if media_root not in file_path.parents or not file_path.is_file():
        raise Http404

    content_type, _ = mimetypes.guess_type(file_path.name)

    return FileResponse(
        file_path.open("rb"),
        content_type=content_type or "application/octet-stream",
    )