"""Tests for Sankey visualization: criticality-based link thickness in context data.

Verifies that:
- The view passes `criticality` field in sankey_data_json context
- The getLinkThickness JS formula produces correct pixel values
- Edge cases: null, 0, negative, boundary values (1, 10)
- No regressions in existing tests
"""

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


def get_link_thickness(criticality):
    """Replicate the getLinkThickness JS logic from the Sankey template.

    Maps criticality 1-10 to 1px-21px using formula: 1 + (criticality - 1) * (20 / 9).
    Null/undefined/<1 defaults to 1px.
    """
    if criticality is None or criticality < 1:
        return 1
    return 1 + (criticality - 1) * (20 / 9)


class SankeyCriticalityFieldTest(TestCase):
    """Tests for the criticality field in sankey_data_json context."""

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

    def test_criticality_field_present(self):
        """sankey_data_json link dict includes criticality field."""
        data = self._get_sankey_data()
        self.assertIn('links', data)
        self.assertGreater(len(data['links']), 0)
        self.assertIn('criticality', data['links'][0])

    def test_criticality_value_matches_stored(self):
        """criticality value matches the link's stored criticality_rating."""
        data = self._get_sankey_data()
        self.assertEqual(data['links'][0]['criticality'], 5)

    def test_null_criticality_coerced_to_zero(self):
        """null criticality_rating is coerced to 0 in sankey_data_json."""
        create_link(self.an3, self.an4, criticality_rating=None)
        data = self._get_sankey_data()
        self.assertEqual(len(data['links']), 2)
        null_link = data['links'][1]
        self.assertEqual(null_link['criticality'], 0)

    def test_null_criticality_serializes_as_zero(self):
        """Verify null criticality_rating serializes as '0', not 'null'."""
        create_link(self.an3, self.an4, criticality_rating=None)
        response = self.client.get(
            reverse('vta:sankey_visualization', kwargs={'pk': self.assessment.pk})
        )
        raw_json = response.context['sankey_data_json']
        # criticality should be 0 (coerced from None by view), not null
        self.assertIn('"criticality": 0', raw_json)
        self.assertNotIn('"criticality": null', raw_json)

    def test_criticality_boundary_min_one(self):
        """criticality=1 is passed through correctly (minimum valid rating)."""
        create_link(self.an3, self.an4, criticality_rating=1)
        data = self._get_sankey_data()
        links_by_crit = {l['criticality'] for l in data['links']}
        self.assertIn(1, links_by_crit)

    def test_criticality_boundary_max_ten(self):
        """criticality=10 is passed through correctly (maximum valid rating)."""
        create_link(self.an3, self.an4, criticality_rating=10)
        data = self._get_sankey_data()
        links_by_crit = {l['criticality'] for l in data['links']}
        self.assertIn(10, links_by_crit)

    def test_multiple_links_varied_criticality(self):
        """Links with different criticality ratings all appear correctly."""
        create_link(self.an3, self.an4, criticality_rating=1)
        create_link(self.an2, self.an3, criticality_rating=10)
        data = self._get_sankey_data()
        self.assertEqual(len(data['links']), 3)
        crits = [l['criticality'] for l in data['links']]
        self.assertIn(5, crits)   # from setUp default
        self.assertIn(1, crits)   # from an3->an4
        self.assertIn(10, crits)  # from an2->an3

    def test_raw_json_contains_criticality_field(self):
        """Raw JSON string contains criticality field for each link."""
        response = self.client.get(
            reverse('vta:sankey_visualization', kwargs={'pk': self.assessment.pk})
        )
        raw_json = response.context['sankey_data_json']
        self.assertIn('"criticality"', raw_json)


class SankeyCriticalityThicknessTest(TestCase):
    """Tests for getLinkThickness formula logic and criticality values in view context."""

    def setUp(self):
        self.client = Client()
        self.user = create_user('analyst')
        add_to_group(self.user, 'Analyst')
        self.profile = self.user.profile
        self.assessment = create_assessment(self.profile)
        self.client.login(username='analyst', password='pass123')

    def _make_links_for_criticalities(self, criticalities):
        """Create nodes and links for each criticality value in sequence."""
        prev_an = None
        for i, crit in enumerate(criticalities):
            node = create_node(self.profile, title=f'N{i}', short_name=f'N{i}')
            an = add_node_to_assessment(self.assessment, node)
            if prev_an is not None:
                create_link(prev_an, an, criticality_rating=crit)
            prev_an = an

    def _get_sankey_data(self):
        response = self.client.get(
            reverse('vta:sankey_visualization', kwargs={'pk': self.assessment.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('sankey_data_json', response.context)
        return json.loads(response.context['sankey_data_json'])

    # --- Formula unit tests (pure logic, no DB needed) ---

    def test_thickness_formula_criticality_1(self):
        """getLinkThickness(1) = 1px (minimum valid thickness)."""
        self.assertEqual(get_link_thickness(1), 1)

    def test_thickness_formula_criticality_5(self):
        """getLinkThickness(5) = 89/9 ≈ 9.889px."""
        self.assertAlmostEqual(get_link_thickness(5), 89/9)

    def test_thickness_formula_criticality_10(self):
        """getLinkThickness(10) = 21px (maximum thickness)."""
        self.assertEqual(get_link_thickness(10), 21)

    def test_thickness_formula_full_range(self):
        """Verify the thickness formula across the full 1-10 range."""
        for crit in range(1, 11):
            expected = 1 + (crit - 1) * (20 / 9)
            self.assertAlmostEqual(
                get_link_thickness(crit), expected,
                msg=f'Thickness mismatch for criticality={crit}: '
                f'expected {expected}, got {get_link_thickness(crit)}'
            )

    def test_thickness_null_is_minimum(self):
        """getLinkThickness(None) = 1px."""
        self.assertEqual(get_link_thickness(None), 1)

    def test_thickness_zero_is_minimum(self):
        """getLinkThickness(0) = 1px."""
        self.assertEqual(get_link_thickness(0), 1)

    def test_thickness_negative_is_minimum(self):
        """getLinkThickness(negative) = 1px."""
        self.assertEqual(get_link_thickness(-5), 1)

    def test_thickness_monotonic_increasing(self):
        """Higher criticality always yields >= thickness of lower criticality."""
        for lower in range(1, 10):
            for higher in range(lower + 1, 11):
                self.assertGreaterEqual(
                    get_link_thickness(higher), get_link_thickness(lower),
                    f'Thickness not monotonic: crit {higher} -> '
                    f'{get_link_thickness(higher)} < crit {lower} -> '
                    f'{get_link_thickness(lower)}'
                )

    def test_thickness_strictly_increasing(self):
        """Each increment in criticality increases thickness by exactly 20/9px."""
        for crit in range(1, 10):
            diff = get_link_thickness(crit + 1) - get_link_thickness(crit)
            self.assertAlmostEqual(
                diff, 20/9,
                msg=f'Thickness increment from crit {crit} to {crit + 1} '
                f'is {diff}, expected {20/9}'
            )

    # --- View integration tests ---

    def _make_single_link_with_criticality(self, criticality):
        """Create two nodes and one link with the given criticality_rating."""
        n0 = create_node(self.profile, title='Src', short_name='Src')
        n1 = create_node(self.profile, title='Dst', short_name='Dst')
        an0 = add_node_to_assessment(self.assessment, n0)
        an1 = add_node_to_assessment(self.assessment, n1)
        create_link(an0, an1, criticality_rating=criticality)

    def test_view_thickness_criticality_1(self):
        """View passes criticality=1 gives formula thickness 1px."""
        self._make_single_link_with_criticality(1)
        data = self._get_sankey_data()
        link = data['links'][0]
        self.assertEqual(link['criticality'], 1)
        self.assertEqual(get_link_thickness(link['criticality']), 1)

    def test_view_thickness_criticality_5(self):
        """View passes criticality=5 gives formula thickness 89/9 ≈ 9.889px."""
        self._make_single_link_with_criticality(5)
        data = self._get_sankey_data()
        link = data['links'][0]
        self.assertEqual(link['criticality'], 5)
        self.assertAlmostEqual(get_link_thickness(link['criticality']), 89/9)

    def test_view_thickness_criticality_10(self):
        """View passes criticality=10 gives formula thickness 21px."""
        self._make_single_link_with_criticality(10)
        data = self._get_sankey_data()
        link = data['links'][0]
        self.assertEqual(link['criticality'], 10)
        self.assertEqual(get_link_thickness(link['criticality']), 21)

    def test_view_null_criticality_gives_min_thickness(self):
        """Null criticality from view (coerced to 0) generates min 1px thickness."""
        self._make_single_link_with_criticality(None)
        data = self._get_sankey_data()
        link = data['links'][0]
        self.assertEqual(link['criticality'], 0)  # coerced by view
        self.assertEqual(get_link_thickness(link['criticality']), 1)

    def test_view_criticality_zero_gives_min_thickness(self):
        """criticality=0 generates 1px thickness."""
        self._make_single_link_with_criticality(0)
        data = self._get_sankey_data()
        link = data['links'][0]
        self.assertEqual(link['criticality'], 0)
        self.assertEqual(get_link_thickness(link['criticality']), 1)

    def test_view_thicknesses_varied_range(self):
        """Multiple links with varied criticalities correctly compute thickness."""
        self._make_links_for_criticalities([1, 3, 5, 7, 10])
        data = self._get_sankey_data()
        for link in data['links']:
            expected = get_link_thickness(link['criticality'])
            self.assertGreaterEqual(expected, 1,
                                    f'Thickness should be >= 1 for criticality={link["criticality"]}')
