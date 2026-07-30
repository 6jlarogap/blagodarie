from unittest import mock

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase

from contact.views import (
    ApiProfileGenesisAll,
    GetTrustGenesisMixin,
    PUBLIC_GRAPH_MAX_DEPTH,
    PUBLIC_GRAPH_MAX_PAGE_SIZE,
)


class GraphAdmissionControlTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_public_graph_depth_is_hard_capped(self):
        class View(GetTrustGenesisMixin):
            def get_tree(self, request, id_, recursion_depth, fmt):
                return {'depth': recursion_depth}

        response = View().get(self.factory.get(
            '/api/profile_genesis/', {'id': 'profile', 'depth': 999},
        ))

        self.assertEqual(response.data['depth'], PUBLIC_GRAPH_MAX_DEPTH)

    @mock.patch('contact.views.CurrentState')
    @mock.patch('contact.views.Profile')
    def test_all_graph_always_uses_bounded_profile_page(self, profile, current_state):
        profiles = profile.objects.select_related.return_value.filter.return_value \
            .order_by.return_value.distinct.return_value
        profiles.__iter__.return_value = iter(())
        current_state.objects.filter.return_value.select_related.return_value \
            .filter.return_value.distinct.return_value.__iter__.return_value = iter(())

        for query, page_size in (
            ({'rod': 'on'}, min(settings.PAGINATE_USERS_COUNT, PUBLIC_GRAPH_MAX_PAGE_SIZE)),
            ({'rod': 'on', 'number': 999}, PUBLIC_GRAPH_MAX_PAGE_SIZE),
        ):
            with self.subTest(query=query):
                request = self.factory.get('/api/profile_genesis/all/', query)
                request.user = AnonymousUser()
                ApiProfileGenesisAll().get(request)
                self.assertEqual(profiles.__getitem__.call_args.args[0], slice(0, page_size))
