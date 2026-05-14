"""Tests for Sankey visualization: performance_rating in context data and template rendering."""

import json

from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse

from vta.models import (
    Assessment,
    AssessmentNode,
    Link,
    Node,
    NodeType,
    UserProfile,
    AssessmentStatus,
)


def create_user(username, password='pass123', **kwargs):
    user = User.objects.create_user(username=username, password=password, **kwargs)
    UserProfile.objects.get_or_create(user=user)
    return user


def add_to_group(user, group_name):
    group, _ = Group.objects.get_or_create(name=group_name)
    user.groups.add(group)


def create_node(creator, node_type=NodeType.OBSERVING_SYSTEM, title='Test Node', **kwargs):
    return Node.objects.create(
        type=node_type,
        title=title,
        short_name=kwargs.pop('short_name', 'TN'),
        description=kwargs.pop('description', 'A test node'),
        created_by=creator,
        **kwargs,
    )


def create_assessment(creator, title='Test Assessment', **kwargs):
    return Assessment.objects.create(
        title=title,
        description=kwargs.pop('description', 'A test assessment'),
        private=kwargs.pop('private', False),
        hypothetical=kwargs.pop('hypothetical', False),
        status=kwargs.pop('status', AssessmentStatus.WORK_IN_PROGRESS),
        created_by=creator,
    )


def add_node_to_assessment(assessment, node):
    return AssessmentNode.objects.create(assessment=assessment, node=node)


def create_link(source_an, target_an, performance_rating=50, criticality_rating=5):
    return Link.objects.create(
        source_assessment_node=source_an,
        target_assessment_node=target_an,
        performance_rating=performance_rating,
        criticality_rating=criticality_rating,
    )


class SankeyPerformanceRatingTest(TestCase):
    """Tests for the performance_rating field in sankey_data_json context."""

    def setUp(self):
        self.client = Client()
        self.user = create_user('analyst')
        add_to_group(self.user, 'Analyst')
        self.profile = self.user.profile
        self.assessment = create_assessment(self.profile)
        self.node1 = create_node(self.profile, title='N1', short_name='N1')
        self.node2 = create_node(self.profile, title='N2', short_name='N2')
        self.node3 = create_node(self.profile, title='N3', short_name='N3')
        self.node4 = create_node(self.profile, title='N4', short_name='N4')
        self.an1 = add_node_to_assessment(self.assessment, self.node1)
        self.an2 = add_node_to_assessment(self.assessment, self.node2)
        self.an3 = add_node_to_assessment(self.assessment, self.node3)
        self.an4 = add_node_to_assessment(self.assessment, self.node4)
        self.link = create_link(self.an1, self.an2, performance_rating=50, criticality_rating=5)
        self.client.login(username='analyst', password='pass123')

    def _get_sankey_data(self, assessment_pk=None):
        pk = assessment_pk or self.assessment.pk
        response = self.client.get(
            reverse('vta:sankey_visualization', kwargs={'pk': pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('sankey_data_json', response.context)
        return json.loads(response.context['sankey_data_json'])

    def test_performance_rating_field_present(self):
        """sankey_data_json link dict includes performance_rating."""
        data = self._get_sankey_data()
        self.assertIn('links', data)
        self.assertGreater(len(data['links']), 0)
        self.assertIn('performance_rating', data['links'][0])

    def test_performance_rating_value_matches_stored(self):
        """performance_rating value matches the link's stored rating."""
        data = self._get_sankey_data()
        self.assertEqual(data['links'][0]['performance_rating'], 50)
        self.assertEqual(data['links'][0]['value'], 50)

    def test_has_all_link_fields(self):
        """Link dict contains all expected fields."""
        data = self._get_sankey_data()
        link = data['links'][0]
        expected = {'source', 'target', 'value', 'performance_rating', 'criticality', 'gaps', 'id'}
        self.assertEqual(set(link.keys()), expected)
        self.assertEqual(link['id'], self.link.pk)
        self.assertEqual(link['criticality'], 5)
        self.assertEqual(link['gaps'], '')

    def test_null_performance_rating_stays_null(self):
        """null performance_rating stays null in JSON (not coerced to 0)."""
        create_link(self.an3, self.an4, performance_rating=None, criticality_rating=3)
        data = self._get_sankey_data()
        # Find the null-rated link (uses an3->an4 which has no other links)
        self.assertEqual(len(data['links']), 2)
        # First link (an1->an2) has rating 50, second link (an3->an4) has null
        null_link = data['links'][1]
        self.assertIsNone(null_link['performance_rating'])
        self.assertEqual(null_link['value'], 0)

    def test_null_performance_rating_serializes_as_null(self):
        """Verify null performance_rating serializes as 'null' literal, not '0'."""
        create_link(self.an3, self.an4, performance_rating=None)
        response = self.client.get(
            reverse('vta:sankey_visualization', kwargs={'pk': self.assessment.pk})
        )
        raw_json = response.context['sankey_data_json']
        self.assertIn('"performance_rating": null', raw_json)

    def test_multiple_links_varied_ratings(self):
        """Links with different ratings all appear correctly."""
        create_link(self.an3, self.an4, performance_rating=85, criticality_rating=9)
        create_link(self.an2, self.an3, performance_rating=None, criticality_rating=3)
        data = self._get_sankey_data()
        self.assertEqual(len(data['links']), 3)
        ratings = [l['performance_rating'] for l in data['links']]
        self.assertIn(50, ratings)
        self.assertIn(85, ratings)
        self.assertIn(None, ratings)

    def test_empty_assessment_shows_no_data_message(self):
        """Assessment with no links renders and shows no-data message."""
        empty = create_assessment(self.profile, title='Empty')
        response = self.client.get(
            reverse('vta:sankey_visualization', kwargs={'pk': empty.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'vta/sankey_visualization.html')
        self.assertContains(response, 'No data available for visualization')
