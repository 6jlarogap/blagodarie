from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase

from users.models import Profile

from .models import CurrentState


class GraphContractBaselineTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.profiles = {}
        for index, name in enumerate(('root', 'parent', 'grandparent', 'child', 'grandchild', 'owned')):
            user = User.objects.create_user(username=name, first_name=name.title())
            cls.profiles[name] = Profile.objects.create(
                user=user,
                latitude=55.70 + index / 100,
                longitude=37.60 + index / 100,
            )
        cls.profiles['owned'].owner = cls.profiles['root'].user
        cls.profiles['owned'].save(update_fields=('owner',))

        def parent_of(parent, child, **role):
            CurrentState.objects.create(user_from=parent.user, user_to=child.user, is_child=True, **role)
            CurrentState.objects.create(user_from=child.user, user_to=parent.user, is_child=False, **role)

        parent_of(cls.profiles['parent'], cls.profiles['root'], is_mother=True)
        parent_of(cls.profiles['grandparent'], cls.profiles['parent'], is_mother=True)
        parent_of(cls.profiles['root'], cls.profiles['child'], is_father=True)
        parent_of(cls.profiles['child'], cls.profiles['grandchild'], is_father=True)
        CurrentState.objects.create(
            user_from=cls.profiles['root'].user,
            user_to=cls.profiles['owned'].user,
            attitude=CurrentState.TRUST,
        )

    def setUp(self):
        cache.clear()

    def test_complete_d2_d3_graph_contracts_are_uncapped(self):
        expected_ids = {profile.user_id for profile in self.profiles.values()}
        expected_uuids = {str(profile.uuid) for profile in self.profiles.values()}

        d2 = self.client.get('/api/profile_genesis/all/', {
            'rod': 'on', 'dover': 'on', 'withalone': 'on',
        })
        self.assertEqual(d2.status_code, 200, d2.data)
        self.assertEqual({str(node['uuid']) for node in d2.data['users']}, expected_uuids)
        self.assertEqual(len(d2.data['connections']), 5)
        self.assertTrue(all({
            'user_id', 'uuid', 'username', 'first_name', 'photo', 'subject_kind',
            'subject_kind_confirmed', 'subject_kind_label',
        } <= node.keys() for node in d2.data['users']))
        self.assertTrue(all({'source', 'target', 'is_child', 'thanks_count', 'attitude'} <= link.keys()
                            for link in d2.data['connections']))

        d3 = self.client.get('/api/profile_genesis/all/', {
            'rod': 'on', 'dover': 'on', 'withalone': 'on', 'fmt': '3d-force-graph',
        })
        self.assertEqual(d3.status_code, 200, d3.data)
        self.assertEqual({node['id'] for node in d3.data['nodes']}, expected_ids)
        self.assertEqual(len(d3.data['links']), 5)
        self.assertIn('bot_username', d3.data)
        self.assertTrue(all({
            'id', 'uuid', 'username', 'first_name', 'photo', 'gender', 'is_dead',
            'subject_kind', 'subject_kind_confirmed', 'subject_kind_label',
        } <= node.keys() for node in d3.data['nodes']))
        self.assertTrue(all({'source', 'target', 'is_child', 'thanks_count', 'attitude'} <= link.keys()
                            for link in d3.data['links']))

    def test_full_map_marker_contract_is_uncapped_and_interactive(self):
        response = self.client.get('/api/user/points/', {'participants': 'on', 'owned': 'on'})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data['points']), len(self.profiles))
        self.assertEqual(
            {(point['latitude'], point['longitude']) for point in response.data['points']},
            {(profile.latitude, profile.longitude) for profile in self.profiles.values()},
        )
        for point in response.data['points']:
            self.assertTrue({
                'latitude', 'longitude', 'title', 'popup', 'icon', 'size_icon',
                'is_of_found_user', 'subject_kind', 'subject_kind_confirmed',
                'subject_kind_label',
            } <= point.keys())
            self.assertIn('Профиль', point['popup'])
            self.assertIn('Доверия', point['popup'])
            self.assertIn('href=', point['popup'])

    def test_uuid_genesis_honors_up_down_and_depth(self):
        root = self.profiles['root']
        cases = (
            ({'up': 'on'}, ('root', 'parent', 'grandparent')),
            ({'down': 'on'}, ('root', 'child', 'grandchild')),
            ({'up': 'on', 'down': 'on', 'depth': '1'}, ('root', 'parent', 'child')),
        )
        for direction, names in cases:
            with self.subTest(direction=direction):
                params = {'uuid': str(root.uuid), 'depth': '2'}
                params.update(direction)
                d2 = self.client.get('/api/profile_genesis/', params)
                self.assertEqual(d2.status_code, 200, d2.data)
                self.assertEqual(
                    {node['user_id'] for node in d2.data['users']},
                    {self.profiles[name].user_id for name in names},
                )
                self.assertEqual(len(d2.data['connections']), len(names) - 1)
                self.assertTrue(all({'user_id', 'uuid', 'username', 'first_name', 'photo'} <= node.keys()
                                    for node in d2.data['users']))
                self.assertTrue(all({'source', 'target'} <= link.keys()
                                    for link in d2.data['connections']))

                params.update(fmt='3d-force-graph', new='on')
                d3 = self.client.get('/api/profile_genesis/', params)
                self.assertEqual(d3.status_code, 200, d3.data)
                self.assertTrue(
                    {self.profiles[name].user_id for name in names} <=
                    {int(node_id) for node_id in d3.data['nodes_by_id']},
                )
                self.assertIn('bot_username', d3.data)
                self.assertTrue({
                    'id', 'uuid', 'username', 'first_name', 'photo', 'gender', 'is_my',
                } <= d3.data['root_node'].keys())
                self.assertTrue(all({
                    'tree_links', 'parents', 'up', 'down', 'complete', 'collapsed',
                } <= node.keys() for node in d3.data['nodes_by_id'].values()))
