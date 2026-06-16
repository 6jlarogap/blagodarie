from django.urls import re_path
from django.views.generic.base import RedirectView

from django.conf import settings

from . import views

urlpatterns = [
    re_path(r'^api/addoperation/?$', views.api_add_operation),
    re_path(r'^api/getuseroperations/?$', views.api_get_user_operations),
    re_path(r'^api/cancel_thank/?$', views.api_cancel_thank),

    re_path(r'^api/thank_bank/?$', views.api_thank_bank),
    re_path(r'^api/get_donate_to/?$', views.api_get_donate_to),

    re_path(r'^api/addtextoperation/?$', views.api_add_text_operation),
    re_path(r'^api/gettextinfo/?$', views.api_get_textinfo),
    re_path(r'^api/gettextoperations/?$', views.api_get_text_operations),

    re_path(r'^api/getuserkeys/?$', views.api_get_user_keys),
    re_path(r'^api/addkey/?$', views.api_add_key),
    re_path(r'^api/updatekey/?$', views.api_update_key),
    re_path(r'^api/deletekey/?$', views.api_delete_key),

    re_path(r'^api/getstats/?$', views.api_get_stats),
    re_path(r'^api/getstats/did_meet/?$', views.api_get_stats, {'only': 'did_meet'}),
    re_path(r'^api/getstats/users/?$', views.api_get_stats, {'only': 'users'}),
    re_path(r'^api/getstats/symptoms/?$', views.api_get_stats, {'only': 'symptoms'}),
    re_path(r'^api/getstats/symptoms/names/?$', views.api_get_stats, {'only': 'symptoms_names'}),

    re_path(r'^api/getstats/symptoms/hist/data/?$',
        views.api_get_stats, {'only': 'symptoms_hist_data'}),
    re_path(r'^api/getstats/symptoms/moon/data/?$',
        views.api_get_stats, {'only': 'symptoms_moon_data'}),

    re_path(r'^api/getstats/user_connections/?$', views.api_get_stats, {'only': 'user_connections'}),
    re_path(r'^api/getstats/user_connections_graph/?$', views.api_get_stats, {'only': 'user_connections_graph'}),

    re_path(r'^api/profile_graph/?$', views.api_profile_graph),
    re_path(r'^api/profile_genesis/?$', views.api_profile_genesis),
    re_path(r'^api/profile_genesis/all/?$', views.api_profile_genesis_all),
    re_path(r'^api/profile_trust/?$', views.api_profile_trust),

    re_path(r'^api/addusersymptom/?$', views.api_add_user_symptom),
    re_path(r'^api/add_user_symptom/?$', views.api_add_user_symptom, {'auth': True}),
    re_path(r'^api/addincognitosymptom/?$', views.api_add_user_symptom, {'auth': False}),

    re_path(r'^api/getsymptoms/?$', views.api_getsymptoms),
    re_path(r'^api/getincognitomessages/?$', views.api_getincognitomessages),

    re_path(r'^api/addorupdatewish/?$', views.api_add_or_update_wish),
    re_path(r'^api/getwishinfo/?$', views.api_get_wish_info),
    re_path(r'^api/getuserwishes/?$', views.api_get_user_wishes),
    re_path(r'^api/deletewish/?$', views.api_delete_wish),

    re_path(r'^api/getthanksusersforanytext/?$', views.api_get_thanks_users_for_anytext),

    re_path(r'^api/addorupdateability/?$', views.api_add_or_update_ability),
    re_path(r'^api/getuserabilities/?$', views.api_get_user_abilities),
    re_path(r'^api/deleteability/?$', views.api_delete_ability),

    re_path(r'^api/invite/usetoken/?$', views.api_invite_use_token),

    re_path(r'^api/tg_message/?$', views.api_tg_message),
    re_path(r'^api/tg_message/list/?$', views.api_tg_message_list),

    re_path(r'^admin/merge_symptoms/?$', views.merge_symptoms),
]
