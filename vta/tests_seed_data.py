"""Tests for the seed_data management command, focusing on Arctic Report Card link creation."""

from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from vta.models import Assessment, AssessmentNode, Link, Node, NodeType


class SeedDataArcticReportCardTest(TestCase):
    """Test the Arctic Report Card seed data link creation."""

    def setUp(self):
        self.out = StringIO()

    def _run_seed(self):
        """Run the seed_data command and capture output."""
        call_command('seed_data', stdout=self.out)

    # ── link data (replicated from the command for assertion matching) ──

    EXPECTED_NODE_COUNT = 12  # 7 observing systems + 5 SBAs

    OBSERVING_SYSTEMS = [
        'Surface Air Temp',
        'Lake Ice',
        'Sea Ice',
        'Precipitation',
        'Terrestrial Snow Cover',
        'Sea Surface Temp',
        'Greenland Ice Sheet',
    ]

    SOCIETAL_BENEFIT_AREAS = [
        'Fundamental Understanding',
        'Terrestrial Freshwater',
        'Marine Coastal',
        'Environmental Quality',
        'Weather and Climate',
    ]

    # 30 links: (source_title, target_title, perf, crit)
    EXPECTED_LINKS = [
        # Strong links with high ratings
        ('Sea Ice', 'Marine Coastal', 90, 10),
        ('Surface Air Temp', 'Weather and Climate', 95, 10),
        ('Greenland Ice Sheet', 'Weather and Climate', 85, 9),
        ('Lake Ice', 'Terrestrial Freshwater', 70, 7),
        ('Precipitation', 'Weather and Climate', 80, 8),
        ('Terrestrial Snow Cover', 'Terrestrial Freshwater', 65, 6),
        ('Sea Surface Temp', 'Marine Coastal', 75, 8),
        # Additional strong links
        ('Surface Air Temp', 'Fundamental Understanding', 92, 9),
        ('Sea Ice', 'Fundamental Understanding', 88, 8),
        ('Greenland Ice Sheet', 'Environmental Quality', 78, 7),
        # Medium performance links
        ('Lake Ice', 'Environmental Quality', 60, 5),
        ('Precipitation', 'Terrestrial Freshwater', 72, 6),
        ('Sea Surface Temp', 'Environmental Quality', 68, 6),
        ('Terrestrial Snow Cover', 'Weather and Climate', 74, 7),
        ('Precipitation', 'Marine Coastal', 55, 5),
        # Lower performance links
        ('Lake Ice', 'Fundamental Understanding', 50, 4),
        ('Sea Surface Temp', 'Fundamental Understanding', 45, 4),
        ('Terrestrial Snow Cover', 'Fundamental Understanding', 58, 5),
        # Links with null performance_rating
        ('Lake Ice', 'Marine Coastal', None, 6),
        ('Precipitation', 'Environmental Quality', None, 5),
        ('Sea Surface Temp', 'Weather and Climate', None, 7),
        ('Terrestrial Snow Cover', 'Marine Coastal', None, 4),
        # Links with null criticality_rating
        ('Surface Air Temp', 'Environmental Quality', 82, None),
        ('Sea Ice', 'Environmental Quality', 76, None),
        ('Lake Ice', 'Weather and Climate', 63, None),
        ('Precipitation', 'Fundamental Understanding', 48, None),
        # Remaining links to reach 30
        ('Surface Air Temp', 'Terrestrial Freshwater', 70, 6),
        ('Sea Ice', 'Terrestrial Freshwater', 62, 5),
        ('Greenland Ice Sheet', 'Fundamental Understanding', 82, 8),
        ('Greenland Ice Sheet', 'Terrestrial Freshwater', 72, 7),
    ]

    ARC_ASSESSMENT_TITLE = 'Physical Indicators: 20th Anniversary Arctic Report Card'

    # ── Helper methods ──

    def _assert_arc_assessment_exists(self):
        """Return the ARC assessment; fail if it does not exist."""
        assessments = Assessment.objects.filter(title=self.ARC_ASSESSMENT_TITLE)
        self.assertEqual(
            assessments.count(), 1,
            f'Expected exactly one ARC assessment, found {assessments.count()}',
        )
        return assessments.first()

    def _assert_nodes_exist(self):
        """Verify all 12 ARC nodes (7 OS + 5 SBA) exist and have correct types."""
        for title in self.OBSERVING_SYSTEMS:
            node = Node.objects.filter(title=title).first()
            self.assertIsNotNone(node, f'Missing observing system node: {title}')
            self.assertEqual(
                node.type, NodeType.OBSERVING_SYSTEM,
                f'{title} should be an observing system',
            )
        for title in self.SOCIETAL_BENEFIT_AREAS:
            node = Node.objects.filter(title=title).first()
            self.assertIsNotNone(node, f'Missing SBA node: {title}')
            self.assertEqual(
                node.type, NodeType.SOCIETAL_BENEFIT_AREA,
                f'{title} should be an SBA',
            )

    def _assert_assessment_nodes(self, assessment):
        """Verify all 12 nodes are linked as AssessmentNodes for the given assessment."""
        an_count = AssessmentNode.objects.filter(assessment=assessment).count()
        self.assertEqual(
            an_count, self.EXPECTED_NODE_COUNT,
            f'Expected {self.EXPECTED_NODE_COUNT} AssessmentNodes, found {an_count}',
        )

    def _get_an_map(self, assessment):
        """Return {node_title: AssessmentNode} dict for the assessment."""
        return {
            an.node.title: an
            for an in AssessmentNode.objects.filter(assessment=assessment).select_related('node')
        }

    def _get_links(self, assessment):
        """Return all Links for the ARC assessment with related nodes."""
        return Link.objects.filter(
            source_assessment_node__assessment=assessment,
        ).select_related(
            'source_assessment_node__node',
            'target_assessment_node__node',
        )

    def _build_link_map(self, assessment):
        """Return {(source_title, target_title): Link} dict."""
        return {
            (l.source_assessment_node.node.title, l.target_assessment_node.node.title): l
            for l in self._get_links(assessment)
        }

    # ── Happy path tests ──

    def test_seed_creates_arc_assessment(self):
        """Running seed_data creates the Arctic Report Card assessment."""
        self._run_seed()
        assessment = self._assert_arc_assessment_exists()
        self.assertEqual(
            assessment.description,
            'Evaluate the societal benefits of Arctic observing systems for the 20th Anniversary Arctic Report Card.',
        )
        self.assertFalse(assessment.private)
        self.assertFalse(assessment.hypothetical)

    def test_seed_creates_all_12_nodes(self):
        """Running seed_data creates all 7 observing system + 5 SBA nodes."""
        self._run_seed()
        self._assert_nodes_exist()

    def test_seed_creates_all_12_assessment_nodes(self):
        """Running seed_data links all 12 nodes as AssessmentNodes."""
        self._run_seed()
        assessment = self._assert_arc_assessment_exists()
        self._assert_assessment_nodes(assessment)

    def test_seed_creates_exactly_30_links(self):
        """Running seed_data creates exactly 30 links for the ARC assessment."""
        self._run_seed()
        assessment = self._assert_arc_assessment_exists()
        links = self._get_links(assessment)
        self.assertEqual(
            links.count(), 30,
            f'Expected 30 links, found {links.count()}',
        )

    def test_each_expected_link_exists(self):
        """Every entry in the link_data array results in a link with correct source→target."""
        self._run_seed()
        assessment = self._assert_arc_assessment_exists()
        link_map = self._build_link_map(assessment)

        # Assert each expected pair exists
        for src_title, tgt_title, perf, crit in self.EXPECTED_LINKS:
            self.assertIn(
                (src_title, tgt_title), link_map,
                f'Missing link: {src_title} → {tgt_title}',
            )

        # Assert no extra unexpected links exist
        self.assertEqual(len(link_map), 30)

    def test_each_link_has_correct_performance_rating(self):
        """Every link stores the expected performance_rating value (including nulls)."""
        self._run_seed()
        assessment = self._assert_arc_assessment_exists()
        link_map = self._build_link_map(assessment)

        for src_title, tgt_title, expected_perf, expected_crit in self.EXPECTED_LINKS:
            link = link_map[(src_title, tgt_title)]
            self.assertEqual(
                link.performance_rating, expected_perf,
                f'performance_rating mismatch for {src_title} → {tgt_title}: '
                f'expected {expected_perf}, got {link.performance_rating}',
            )

    def test_each_link_has_correct_criticality_rating(self):
        """Every link stores the expected criticality_rating value (including nulls)."""
        self._run_seed()
        assessment = self._assert_arc_assessment_exists()
        link_map = self._build_link_map(assessment)

        for src_title, tgt_title, expected_perf, expected_crit in self.EXPECTED_LINKS:
            link = link_map[(src_title, tgt_title)]
            self.assertEqual(
                link.criticality_rating, expected_crit,
                f'criticality_rating mismatch for {src_title} → {tgt_title}: '
                f'expected {expected_crit}, got {link.criticality_rating}',
            )

    def test_null_performance_ratings(self):
        """Exactly 4 links have null performance_rating (grey rendering)."""
        self._run_seed()
        assessment = self._assert_arc_assessment_exists()
        links = self._get_links(assessment)
        null_perf = [l for l in links if l.performance_rating is None]
        self.assertEqual(
            len(null_perf), 4,
            f'Expected 4 links with null performance_rating, found {len(null_perf)}',
        )

    def test_null_criticality_ratings(self):
        """Exactly 4 links have null criticality_rating (minimum thickness)."""
        self._run_seed()
        assessment = self._assert_arc_assessment_exists()
        links = self._get_links(assessment)
        null_crit = [l for l in links if l.criticality_rating is None]
        self.assertEqual(
            len(null_crit), 4,
            f'Expected 4 links with null criticality_rating, found {len(null_crit)}',
        )

    def test_performance_rating_range(self):
        """All non-null performance_ratings are in valid range (1-100)."""
        self._run_seed()
        assessment = self._assert_arc_assessment_exists()
        links = self._get_links(assessment)
        for link in links:
            if link.performance_rating is not None:
                self.assertGreaterEqual(link.performance_rating, 1)
                self.assertLessEqual(link.performance_rating, 100)

    def test_criticality_rating_range(self):
        """All non-null criticality_ratings are in valid range (1-10)."""
        self._run_seed()
        assessment = self._assert_arc_assessment_exists()
        links = self._get_links(assessment)
        for link in links:
            if link.criticality_rating is not None:
                self.assertGreaterEqual(link.criticality_rating, 1)
                self.assertLessEqual(link.criticality_rating, 10)

    def test_all_links_source_is_observing_system(self):
        """Every link's source node is an observing system."""
        self._run_seed()
        assessment = self._assert_arc_assessment_exists()
        links = self._get_links(assessment)
        for link in links:
            self.assertEqual(
                link.source_assessment_node.node.type,
                NodeType.OBSERVING_SYSTEM,
                f'Source of link is not an observing system: '
                f'{link.source_assessment_node.node.title}',
            )

    def test_all_links_target_is_societal_benefit_area(self):
        """Every link's target node is a societal benefit area."""
        self._run_seed()
        assessment = self._assert_arc_assessment_exists()
        links = self._get_links(assessment)
        for link in links:
            self.assertEqual(
                link.target_assessment_node.node.type,
                NodeType.SOCIETAL_BENEFIT_AREA,
                f'Target of link is not an SBA: '
                f'{link.target_assessment_node.node.title}',
            )

    # ── Idempotency tests ──

    def test_idempotent_does_not_duplicate_nodes(self):
        """Running seed_data twice does not duplicate ARC nodes."""
        self._run_seed()
        self._run_seed()
        for title in self.OBSERVING_SYSTEMS + self.SOCIETAL_BENEFIT_AREAS:
            self.assertEqual(
                Node.objects.filter(title=title).count(), 1,
                f'Node "{title}" was duplicated after second seed run',
            )

    def test_idempotent_does_not_duplicate_links(self):
        """Running seed_data twice does not create duplicate links."""
        self._run_seed()
        first_count = Link.objects.count()
        self._run_seed()
        second_count = Link.objects.count()
        self.assertEqual(first_count, second_count)

    def test_idempotent_links_retain_ratings(self):
        """Links retain correct ratings after running seed_data twice."""
        self._run_seed()
        self._run_seed()
        assessment = self._assert_arc_assessment_exists()
        link_map = self._build_link_map(assessment)

        for src_title, tgt_title, expected_perf, expected_crit in self.EXPECTED_LINKS:
            link = link_map[(src_title, tgt_title)]
            self.assertEqual(link.performance_rating, expected_perf)
            self.assertEqual(link.criticality_rating, expected_crit)

    # ── Boundary: rating coverage ──

    def test_performance_rating_covers_extremes(self):
        """The used performance ratings include the lowest (45) and highest (95) values."""
        self._run_seed()
        assessment = self._assert_arc_assessment_exists()
        links = self._get_links(assessment)
        ratings = {l.performance_rating for l in links if l.performance_rating is not None}
        self.assertIn(45, ratings, 'No link with performance_rating=45 (lowest non-null)')
        self.assertIn(95, ratings, 'No link with performance_rating=95 (highest)')

    def test_criticality_rating_covers_extremes(self):
        """The used criticality ratings include the lowest (4) and highest (10) values."""
        self._run_seed()
        assessment = self._assert_arc_assessment_exists()
        links = self._get_links(assessment)
        ratings = {l.criticality_rating for l in links if l.criticality_rating is not None}
        self.assertIn(4, ratings, 'No link with criticality_rating=4 (lowest non-null)')
        self.assertIn(10, ratings, 'No link with criticality_rating=10 (highest)')
