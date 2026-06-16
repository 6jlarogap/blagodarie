from django.urls import re_path
from . import views

urlpatterns = [
    re_path(r'^api/wote/vote/?$', views.api_wote_vote),
    re_path(r'^api/wote/vote/sums/?$', views.api_wote_vote_sums),
    re_path(r'^api/wote/vote/graph/?$', views.api_wote_vote_graph),
    re_path(r'^api/wote/vote/my/?$', views.api_wote_vote_my),
]
