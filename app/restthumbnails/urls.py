from django.urls import re_path

from restthumbnails.defaults import URL_REGEX
from restthumbnails.views import ThumbnailView

urlpatterns = [
    re_path(URL_REGEX,
        ThumbnailView.as_view(),
        name="get_thumbnail")
]
