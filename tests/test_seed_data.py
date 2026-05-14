"""Tests for the seed_data management command — Arctic Report Card seed data."""

from io import StringIO

from django.test import TestCase
from django.contrib.auth.models import User, Group
from django.core.management import call_command

from vta.models import Assessment, AssessmentNode, Link, Node, NodeType, UserProfile


def run_seed():
    """Run the seed_data management command and return stdout."""
    out = StringIO()
    call_command('seed_data', stdout=out)
    return out.getvalue()


class SeedDataArcticReportCardTest(TestCase):
    """Tests for the Arctic Report Card seed data in seed_data management command."""

    def test_arctic_report_card_assessment_created(self):
        """The Arctic Report Card assessment is created with correct metadata."""
        run_seed()
        assessment = Assessment.objects.get(
            title='Physical Indicators: 20th Anniversary Arctic Report Card'
        )
        self.assertEqual(
            assessment.description,
            'Evaluate the societal benefits of Arctic observing systems for '
            'the 20th Anniversary Arctic Report Card.',
        )
        self.assertFalse(assessment.private)
        self.assertFalse(assessment.hypothetical)

    def test_arctic_report_card_observing_system_nodes_created(self):
        """All 7 observing system nodes are created for the Arctic Report Card."""
        run_seed()
        expected_titles = [
            'Surface Air Temp',
            'Lake Ice',
            'Sea Ice',
            'Precipitation',
            'Terrestrial Snow Cover',
            'Sea Surface Temp',
            'Greenland Ice Sheet',
        ]
        for title in expected_titles:
            node = Node.objects.get(title=title)
            self.assertEqual(node.type, NodeType.OBSERVING_SYSTEM)
            self.assertEqual(node.short_name, title.split()[0])

    def test_arctic_report_card_sba_nodes_created(self):
        """All 5 societal benefit area nodes are created for the Arctic Report Card."""
        run_seed()
        expected_titles = [
            'Fundamental Understanding',
            'Terrestrial Freshwater',
            'Marine Coastal',
            'Environmental Quality',
            'Weather and Climate',
        ]
        for title in expected_titles:
            node = Node.objects.get(title=title)
            self.assertEqual(node.type, NodeType.SOCIETAL_BENEFIT_AREA)
            self.assertEqual(node.short_name, title.split()[0])

    def test_arctic_report_card_12_node_count(self):
        """Exactly 12 nodes are created for the Arctic Report Card assessment."""
        run_seed()
        assessment = Assessment.objects.get(
            title='Physical Indicators: 20th Anniversary Arctic Report Card'
        )
        anodes = AssessmentNode.objects.filter(assessment=assessment)
        self.assertEqual(anodes.count(), 12)

    def test_arctic_report_card_obs_system_count_in_assessment(self):
        """The Arctic Report Card has exactly 7 observing system AssessmentNodes."""
        run_seed()
        assessment = Assessment.objects.get(
            title='Physical Indicators: 20th Anniversary Arctic Report Card'
        )
        os_count = AssessmentNode.objects.filter(
            assessment=assessment,
            node__type=NodeType.OBSERVING_SYSTEM,
        ).count()
        self.assertEqual(os_count, 7)

    def test_arctic_report_card_sba_count_in_assessment(self):
        """The Arctic Report Card has exactly 5 SBA AssessmentNodes."""
        run_seed()
        assessment = Assessment.objects.get(
            title='Physical Indicators: 20th Anniversary Arctic Report Card'
        )
        sba_count = AssessmentNode.objects.filter(
            assessment=assessment,
            node__type=NodeType.SOCIETAL_BENEFIT_AREA,
        ).count()
        self.assertEqual(sba_count, 5)

    def test_arctic_report_card_node_descriptions(self):
        """Arctic Report Card nodes have the expected description pattern."""
        run_seed()
        os_node = Node.objects.get(title='Surface Air Temp')
        self.assertEqual(
            os_node.description,
            'Surface Air Temp observation system for Arctic monitoring.',
        )
        sba_node = Node.objects.get(title='Fundamental Understanding')
        self.assertEqual(
            sba_node.description,
            'Fundamental Understanding - societal benefit area for Arctic observations.',
        )

    def test_arctic_report_card_links_not_created(self):
        """The Arctic Report Card assessment does NOT include any links (Phase 1.2)."""
        run_seed()
        assessment = Assessment.objects.get(
            title='Physical Indicators: 20th Anniversary Arctic Report Card'
        )
        anodes = AssessmentNode.objects.filter(assessment=assessment)
        link_count = Link.objects.filter(
            source_assessment_node__in=anodes,
        ).count()
        self.assertEqual(link_count, 0)

    def test_idempotency_no_duplicate_assessment(self):
        """Running seed_data twice does not create a duplicate Arctic Report Card."""
        run_seed()
        run_seed()
        count = Assessment.objects.filter(
            title='Physical Indicators: 20th Anniversary Arctic Report Card'
        ).count()
        self.assertEqual(count, 1)

    def test_idempotency_no_duplicate_nodes(self):
        """Running seed_data twice does not create duplicate nodes for Arctic Report Card."""
        run_seed()
        run_seed()
        titles = [
            'Surface Air Temp',
            'Lake Ice',
            'Sea Ice',
            'Precipitation',
            'Terrestrial Snow Cover',
            'Sea Surface Temp',
            'Greenland Ice Sheet',
            'Fundamental Understanding',
            'Terrestrial Freshwater',
            'Marine Coastal',
            'Environmental Quality',
            'Weather and Climate',
        ]
        for title in titles:
            count = Node.objects.filter(title=title).count()
            self.assertEqual(count, 1, f'Duplicate node found: {title}')

    def test_idempotency_no_duplicate_assessment_nodes(self):
        """Running seed_data twice does not create duplicate AssessmentNodes."""
        run_seed()
        run_seed()
        assessment = Assessment.objects.get(
            title='Physical Indicators: 20th Anniversary Arctic Report Card'
        )
        for anode in AssessmentNode.objects.filter(assessment=assessment):
            count = AssessmentNode.objects.filter(
                assessment=assessment,
                node=anode.node,
            ).count()
            self.assertEqual(count, 1)

    def test_sba_nodes_have_null_framework_fields(self):
        """Arctic Report Card SBA nodes have framework_name and framework_url as None."""
        run_seed()
        sba = Node.objects.get(title='Fundamental Understanding')
        self.assertIsNone(sba.framework_name)
        self.assertIsNone(sba.framework_url)


class SeedDataDemoTest(TestCase):
    """Tests verifying the original demo data remains intact."""

    def test_original_demo_assessment_exists(self):
        """The original demo assessment is created alongside the Arctic Report Card."""
        run_seed()
        self.assertTrue(
            Assessment.objects.filter(
                title='Arctic Ice Monitoring Benefit Assessment'
            ).exists()
        )

    def test_original_demo_nodes_exist(self):
        """The original demo nodes still exist after adding Arctic Report Card data."""
        run_seed()
        self.assertTrue(Node.objects.filter(title='ICESat-2').exists())
        self.assertTrue(Node.objects.filter(title='ATL08 Land Ice Height').exists())
        self.assertTrue(Node.objects.filter(title='Sea Level Rise Monitoring').exists())
        self.assertTrue(Node.objects.filter(title='Climate Change Mitigation').exists())

    def test_original_demo_assessment_has_4_nodes(self):
        """The original demo assessment still has its 4 assessment nodes."""
        run_seed()
        assessment = Assessment.objects.get(
            title='Arctic Ice Monitoring Benefit Assessment'
        )
        self.assertEqual(assessment.assessment_nodes.count(), 4)

    def test_original_demo_links_preserved(self):
        """The original demo assessment links still exist."""
        run_seed()
        assessment = Assessment.objects.get(
            title='Arctic Ice Monitoring Benefit Assessment'
        )
        link_count = Link.objects.filter(
            source_assessment_node__assessment=assessment
        ).count()
        self.assertEqual(link_count, 3)

    def test_original_demo_users_and_groups_created(self):
        """Users and groups from the original seed data are created."""
        run_seed()
        for username in ['admin', 'analyst', 'respondent']:
            self.assertTrue(
                User.objects.filter(username=username).exists(),
                f'User {username} should exist',
            )
        for group_name in ['Admin', 'Analyst', 'Respondent']:
            self.assertTrue(
                Group.objects.filter(name=group_name).exists(),
                f'Group {group_name} should exist',
            )


class SeedDataFullRunTest(TestCase):
    """End-to-end tests for the full seed_data command."""

    def test_full_output_contains_success_messages(self):
        """The command output contains all expected success messages."""
        out = run_seed()
        self.assertIn('Seeding reference data...', out)
        self.assertIn('Created admin user', out)
        self.assertIn('Created analyst user', out)
        self.assertIn('Created respondent user', out)
        self.assertIn('Created 4 demo nodes', out)
        self.assertIn('Created demo assessment with all nodes', out)
        self.assertIn('Created demo links between assessment nodes', out)
        self.assertIn(
            'Created Arctic Report Card assessment with 12 nodes', out
        )
        self.assertIn('Seeding complete.', out)

    def test_idempotency_output_no_created_messages_on_rerun(self):
        """Running seed_data a second time does not emit 'Created' messages (idempotent)."""
        run_seed()
        out = run_seed()
        self.assertNotIn('Created Arctic Report Card assessment with 12 nodes', out)

    def test_total_node_count(self):
        """After seeding, there are 12 Arctic Report Card nodes + 4 demo nodes = 16 total."""
        run_seed()
        self.assertEqual(Node.objects.count(), 16)

    def test_total_assessment_count(self):
        """After seeding, there are exactly 2 assessments."""
        run_seed()
        self.assertEqual(Assessment.objects.count(), 2)
