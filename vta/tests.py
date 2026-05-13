"""Comprehensive tests for VTA app: models, forms, views, and templatetags."""

from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.core.exceptions import ValidationError

from vta.models import (
    Assessment,
    AssessmentNode,
    Link,
    Node,
    NodeType,
    UserProfile,
    AssessmentStatus,
)
from vta.forms import (
    AssessmentForm,
    NodeForm,
    LinkForm,
    UserProfileForm,
    AssessmentNodeAddForm,
    SurveyResponseForm,
)


# ---------------------------------------------------------------------------
# Fixtures helper
# ---------------------------------------------------------------------------

def create_user(username: str, password: str = 'pass123', **kwargs) -> User:
    """Create a user with profile."""
    user = User.objects.create_user(username=username, password=password, **kwargs)
    UserProfile.objects.get_or_create(user=user)
    return user


def add_to_group(user: User, group_name: str) -> None:
    """Add user to a group (creates group if needed)."""
    group, _ = Group.objects.get_or_create(name=group_name)
    user.groups.add(group)


def create_node(
    creator: UserProfile,
    node_type: str = NodeType.OBSERVING_SYSTEM,
    title: str = 'Test Node',
    **kwargs,
) -> Node:
    """Create a node with required fields."""
    return Node.objects.create(
        type=node_type,
        title=title,
        short_name=kwargs.pop('short_name', 'TN'),
        description=kwargs.pop('description', 'A test node'),
        created_by=creator,
        **kwargs,
    )


def create_assessment(
    creator: UserProfile,
    title: str = 'Test Assessment',
    status: str = AssessmentStatus.WORK_IN_PROGRESS,
    **kwargs,
) -> Assessment:
    """Create an assessment."""
    return Assessment.objects.create(
        title=title,
        description=kwargs.pop('description', 'A test assessment'),
        private=kwargs.pop('private', False),
        hypothetical=kwargs.pop('hypothetical', False),
        status=status,
        created_by=creator,
    )


def add_node_to_assessment(assessment: Assessment, node: Node) -> AssessmentNode:
    """Add a node to an assessment."""
    return AssessmentNode.objects.create(assessment=assessment, node=node)


def create_link(
    source_an: AssessmentNode,
    target_an: AssessmentNode,
    performance_rating: int = 50,
    criticality_rating: int = 5,
) -> Link:
    """Create a link between two assessment nodes."""
    return Link.objects.create(
        source_assessment_node=source_an,
        target_assessment_node=target_an,
        performance_rating=performance_rating,
        criticality_rating=criticality_rating,
    )


# ---------------------------------------------------------------------------
# Model Tests
# ---------------------------------------------------------------------------

class AssessmentModelTest(TestCase):
    """Tests for the Assessment model."""

    def setUp(self):
        self.user = create_user('testuser')
        add_to_group(self.user, 'Analyst')
        self.profile = self.user.profile

    def test_assessment_str(self):
        assessment = create_assessment(self.profile, title='My Assessment')
        self.assertEqual(str(assessment), 'My Assessment')

    def test_assessment_is_active_work_in_progress(self):
        assessment = create_assessment(self.profile, status=AssessmentStatus.WORK_IN_PROGRESS)
        self.assertTrue(assessment.is_active)

    def test_assessment_is_active_published(self):
        assessment = create_assessment(self.profile, status=AssessmentStatus.PUBLISHED)
        self.assertTrue(assessment.is_active)

    def test_assessment_is_not_active_closed(self):
        assessment = create_assessment(self.profile, status=AssessmentStatus.CLOSED)
        self.assertFalse(assessment.is_active)

    def test_assessment_is_not_active_archived(self):
        assessment = create_assessment(self.profile, status=AssessmentStatus.ARCHIVED)
        self.assertFalse(assessment.is_active)

    def test_assessment_default_status(self):
        assessment = create_assessment(self.profile)
        self.assertEqual(assessment.status, AssessmentStatus.WORK_IN_PROGRESS)

    def test_assessment_ordering(self):
        a1 = create_assessment(self.profile, title='First')
        a2 = create_assessment(self.profile, title='Second')
        self.assertEqual(list(Assessment.objects.all()), [a2, a1])


class NodeModelTest(TestCase):
    """Tests for the Node model."""

    def setUp(self):
        self.user = create_user('testuser')
        add_to_group(self.user, 'Analyst')
        self.profile = self.user.profile

    def test_node_str(self):
        node = create_node(self.profile, title='My Node')
        self.assertIn('My Node', str(node))

    def test_node_is_other_subtype_observing_system(self):
        node = create_node(self.profile, node_type=NodeType.OBSERVING_SYSTEM)
        self.assertTrue(node.is_other_subtype)
        self.assertFalse(node.is_sba_subtype)

    def test_node_is_other_subtype_data_product(self):
        node = create_node(self.profile, node_type=NodeType.DATA_PRODUCT)
        self.assertTrue(node.is_other_subtype)
        self.assertFalse(node.is_sba_subtype)

    def test_node_is_other_subtype_application(self):
        node = create_node(self.profile, node_type=NodeType.APPLICATION)
        self.assertTrue(node.is_other_subtype)
        self.assertFalse(node.is_sba_subtype)

    def test_node_is_sba_subtype(self):
        node = create_node(self.profile, node_type=NodeType.SOCIETAL_BENEFIT_AREA)
        self.assertFalse(node.is_other_subtype)
        self.assertTrue(node.is_sba_subtype)

    def test_node_ordering(self):
        n1 = create_node(self.profile, node_type=NodeType.SOCIETAL_BENEFIT_AREA, title='Zebra')
        n2 = create_node(self.profile, node_type=NodeType.OBSERVING_SYSTEM, title='Alpha')
        result = list(Node.objects.all())
        self.assertEqual(result[0], n2)
        self.assertEqual(result[1], n1)


class AssessmentNodeModelTest(TestCase):
    """Tests for the AssessmentNode model."""

    def setUp(self):
        self.user = create_user('testuser')
        add_to_group(self.user, 'Analyst')
        self.profile = self.user.profile
        self.assessment = create_assessment(self.profile)
        self.node = create_node(self.profile)

    def test_assessment_node_str(self):
        an = add_node_to_assessment(self.assessment, self.node)
        expected = f'{self.assessment.title} -> {self.node.title}'
        self.assertEqual(str(an), expected)

    def test_assessment_node_is_application(self):
        app_node = create_node(self.profile, node_type=NodeType.APPLICATION)
        an = add_node_to_assessment(self.assessment, app_node)
        self.assertTrue(an.is_application)

    def test_assessment_node_not_application(self):
        an = add_node_to_assessment(self.assessment, self.node)
        self.assertFalse(an.is_application)

    def test_unique_constraint(self):
        add_node_to_assessment(self.assessment, self.node)
        with self.assertRaises(Exception):
            add_node_to_assessment(self.assessment, self.node)


class LinkModelTest(TestCase):
    """Tests for the Link model."""

    def setUp(self):
        self.user = create_user('testuser')
        add_to_group(self.user, 'Analyst')
        self.profile = self.user.profile
        self.assessment1 = create_assessment(self.profile, title='Assessment 1')
        self.assessment2 = create_assessment(self.profile, title='Assessment 2')
        self.node1 = create_node(self.profile, title='Node 1', short_name='N1')
        self.node2 = create_node(self.profile, title='Node 2', short_name='N2')
        self.an1_1 = add_node_to_assessment(self.assessment1, self.node1)
        self.an1_2 = add_node_to_assessment(self.assessment1, self.node2)
        self.an2_1 = add_node_to_assessment(self.assessment2, self.node1)

    def test_link_str(self):
        link = create_link(self.an1_1, self.an1_2)
        expected = f'{self.node1.title} -> {self.node2.title}'
        self.assertEqual(str(link), expected)

    def test_link_same_assessment_valid(self):
        link = create_link(self.an1_1, self.an1_2)
        link.clean()

    def test_link_cross_assessment_invalid(self):
        link = Link(
            source_assessment_node=self.an1_1,
            target_assessment_node=self.an2_1,
        )
        with self.assertRaises(ValidationError):
            link.clean()

    def test_link_unique_constraint(self):
        create_link(self.an1_1, self.an1_2)
        with self.assertRaises(Exception):
            create_link(self.an1_1, self.an1_2)

    def test_link_performance_rating_validators(self):
        link = Link(
            source_assessment_node=self.an1_1,
            target_assessment_node=self.an1_2,
            performance_rating=101,
        )
        with self.assertRaises(ValidationError):
            link.full_clean()

    def test_link_criticality_rating_validators(self):
        link = Link(
            source_assessment_node=self.an1_1,
            target_assessment_node=self.an1_2,
            criticality_rating=11,
        )
        with self.assertRaises(ValidationError):
            link.full_clean()


class UserProfileModelTest(TestCase):
    """Tests for the UserProfile model."""

    def test_profile_str_with_full_name(self):
        user = create_user('testuser', first_name='John', last_name='Doe')
        profile = user.profile
        self.assertEqual(str(profile), 'John Doe')

    def test_profile_str_with_username_only(self):
        user = create_user('testuser')
        profile = user.profile
        self.assertEqual(str(profile), 'testuser')


# ---------------------------------------------------------------------------
# Form Tests
# ---------------------------------------------------------------------------

class AssessmentFormTest(TestCase):
    """Tests for the AssessmentForm."""

    def test_valid_form(self):
        form = AssessmentForm(data={
            'title': 'Test',
            'description': 'Desc',
            'private': False,
            'hypothetical': False,
            'status': AssessmentStatus.WORK_IN_PROGRESS,
        })
        self.assertTrue(form.is_valid())

    def test_empty_form_invalid(self):
        form = AssessmentForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)


class NodeFormTest(TestCase):
    """Tests for the NodeForm."""

    def test_valid_form(self):
        form = NodeForm(data={
            'type': NodeType.OBSERVING_SYSTEM,
            'title': 'Test Node',
            'short_name': 'TN',
            'description': '',
            'organization': '',
            'funder': '',
            'funding_country': '',
            'website': '',
            'contact_information': '',
            'persistent_identifier': '',
            'hypothetical': False,
            'framework_name': '',
            'framework_url': '',
        })
        self.assertTrue(form.is_valid())

    def test_empty_form_invalid(self):
        form = NodeForm(data={})
        self.assertFalse(form.is_valid())


class LinkFormTest(TestCase):
    """Tests for the LinkForm."""

    def setUp(self):
        self.user = create_user('testuser')
        add_to_group(self.user, 'Analyst')
        self.profile = self.user.profile
        self.assessment = create_assessment(self.profile)
        self.node1 = create_node(self.profile, title='N1', short_name='N1')
        self.node2 = create_node(self.profile, title='N2', short_name='N2')
        self.an1 = add_node_to_assessment(self.assessment, self.node1)
        self.an2 = add_node_to_assessment(self.assessment, self.node2)

    def test_valid_form(self):
        form = LinkForm(data={
            'source_assessment_node': self.an1.pk,
            'target_assessment_node': self.an2.pk,
            'performance_rating': 50,
            'criticality_rating': 5,
            'performance_rating_rationale': '',
            'criticality_rating_rationale': '',
            'gaps_description': '',
            'attribute_description': '',
        })
        self.assertTrue(form.is_valid())

    def test_cross_assessment_error(self):
        assessment2 = create_assessment(self.profile, title='Assessment 2')
        an_other = add_node_to_assessment(assessment2, self.node1)
        form = LinkForm(data={
            'source_assessment_node': self.an1.pk,
            'target_assessment_node': an_other.pk,
            'performance_rating': '',
            'criticality_rating': '',
            'performance_rating_rationale': '',
            'criticality_rating_rationale': '',
            'gaps_description': '',
            'attribute_description': '',
        })
        self.assertFalse(form.is_valid())


class SurveyResponseFormTest(TestCase):
    """Tests for the SurveyResponseForm."""

    def test_valid_form_with_ratings(self):
        form = SurveyResponseForm(data={
            'performance_rating': 80,
            'criticality_rating': 7,
            'performance_rating_rationale': 'Good performance',
            'criticality_rating_rationale': 'Very critical',
            'gaps_description': 'Some gaps',
            'attribute_description': 'Attributes',
        })
        self.assertTrue(form.is_valid())

    def test_empty_form_valid(self):
        form = SurveyResponseForm(data={})
        self.assertTrue(form.is_valid())

    def test_performance_rating_out_of_range(self):
        form = SurveyResponseForm(data={'performance_rating': 101})
        self.assertFalse(form.is_valid())

    def test_criticality_rating_out_of_range(self):
        form = SurveyResponseForm(data={'criticality_rating': 11})
        self.assertFalse(form.is_valid())


class UserProfileFormTest(TestCase):
    """Tests for the UserProfileForm."""

    def setUp(self):
        self.user = create_user('testuser')
        self.profile = self.user.profile

    def test_valid_form(self):
        form = UserProfileForm(
            instance=self.profile,
            data={
                'orcid': '0000-0000-0000-0000',
                'biography': 'Test bio',
                'affiliation': 'Test Org',
            },
        )
        self.assertTrue(form.is_valid())

    def test_empty_form_valid(self):
        form = UserProfileForm(instance=self.profile, data={})
        self.assertTrue(form.is_valid())


# ---------------------------------------------------------------------------
# View Tests - Authentication & Authorization
# ---------------------------------------------------------------------------

class BaseViewTest(TestCase):
    """Base class for view tests with common setup."""

    def setUp(self):
        self.client = Client()
        self.admin = create_user('admin')
        add_to_group(self.admin, 'Admin')
        self.analyst = create_user('analyst')
        add_to_group(self.analyst, 'Analyst')
        self.respondent = create_user('respondent')
        add_to_group(self.respondent, 'Respondent')
        self.profile = self.analyst.profile
        self.assessment = create_assessment(self.profile)
        self.node1 = create_node(self.profile, title='N1', short_name='N1')
        self.node2 = create_node(self.profile, title='N2', short_name='N2')
        self.an1 = add_node_to_assessment(self.assessment, self.node1)
        self.an2 = add_node_to_assessment(self.assessment, self.node2)
        self.link = create_link(self.an1, self.an2)

    def _login(self, username='analyst'):
        if username == 'admin':
            user = self.admin
        elif username == 'respondent':
            user = self.respondent
        else:
            user = self.analyst
        self.client.login(username=username, password='pass123')

    def assert_login_redirect(self, response):
        """Assert the response redirects to the login page."""
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)


# ---------------------------------------------------------------------------
# Home View Tests
# ---------------------------------------------------------------------------

class HomeViewTest(BaseViewTest):
    """Tests for the home page view."""

    def test_home_unauthenticated(self):
        response = self.client.get(reverse('vta:home'))
        self.assertEqual(response.status_code, 200)

    def test_home_authenticated_analyst(self):
        self._login()
        response = self.client.get(reverse('vta:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'vta/home.html')

    def test_home_authenticated_respondent(self):
        self._login('respondent')
        response = self.client.get(reverse('vta:home'))
        self.assertEqual(response.status_code, 200)

    def test_home_shows_all_assessments_for_analyst(self):
        self._login()
        private_assessment = create_assessment(self.profile, title='Private', private=True)
        response = self.client.get(reverse('vta:home'))
        self.assertContains(response, 'Private')

    def test_home_hides_private_assessments_for_respondent(self):
        self._login('respondent')
        create_assessment(self.profile, title='Private', private=True)
        response = self.client.get(reverse('vta:home'))
        self.assertNotContains(response, 'Private')


# ---------------------------------------------------------------------------
# Assessment View Tests
# ---------------------------------------------------------------------------

class AssessmentListViewTest(BaseViewTest):
    """Tests for the assessment list view."""

    def test_list_requires_login(self):
        response = self.client.get(reverse('vta:assessment_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_list_analyst_sees_all(self):
        self._login()
        response = self.client.get(reverse('vta:assessment_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'vta/assessment_list.html')

    def test_list_respondent_sees_public_only(self):
        self._login('respondent')
        private_assessment = create_assessment(self.profile, title='Private', private=True)
        response = self.client.get(reverse('vta:assessment_list'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Private')


class AssessmentDetailViewTest(BaseViewTest):
    """Tests for the assessment detail view."""

    def test_detail_requires_login(self):
        response = self.client.get(reverse('vta:assessment_detail', kwargs={'pk': self.assessment.pk}))
        self.assert_login_redirect(response)

    def test_detail_shows_assessment(self):
        self._login()
        response = self.client.get(reverse('vta:assessment_detail', kwargs={'pk': self.assessment.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'vta/assessment_detail.html')
        self.assertContains(response, self.assessment.title)

    def test_detail_shows_nodes(self):
        self._login()
        response = self.client.get(reverse('vta:assessment_detail', kwargs={'pk': self.assessment.pk}))
        self.assertContains(response, self.node1.title)

    def test_detail_shows_links(self):
        self._login()
        response = self.client.get(reverse('vta:assessment_detail', kwargs={'pk': self.assessment.pk}))
        self.assertContains(response, self.link.source_assessment_node.node.title)

    def test_detail_404(self):
        self._login()
        response = self.client.get(reverse('vta:assessment_detail', kwargs={'pk': 9999}))
        self.assertEqual(response.status_code, 404)


class AssessmentCreateViewTest(BaseViewTest):
    """Tests for the assessment create view."""

    def test_create_requires_login(self):
        response = self.client.get(reverse('vta:assessment_create'))
        self.assert_login_redirect(response)

    def test_create_analyst_access(self):
        self._login()
        response = self.client.get(reverse('vta:assessment_create'))
        self.assertEqual(response.status_code, 200)

    def test_create_admin_access(self):
        self._login('admin')
        response = self.client.get(reverse('vta:assessment_create'))
        self.assertEqual(response.status_code, 200)

    def test_create_respondent_forbidden(self):
        self._login('respondent')
        response = self.client.get(reverse('vta:assessment_create'))
        self.assertEqual(response.status_code, 403)

    def test_create_valid_data(self):
        self._login()
        data = {
            'title': 'New Assessment',
            'description': 'Test description',
            'private': False,
            'hypothetical': False,
            'status': AssessmentStatus.WORK_IN_PROGRESS,
        }
        response = self.client.post(reverse('vta:assessment_create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Assessment.objects.filter(title='New Assessment').exists())


class AssessmentUpdateViewTest(BaseViewTest):
    """Tests for the assessment update view."""

    def test_update_analyst_access(self):
        self._login()
        response = self.client.get(reverse('vta:assessment_update', kwargs={'pk': self.assessment.pk}))
        self.assertEqual(response.status_code, 200)

    def test_update_respondent_forbidden(self):
        self._login('respondent')
        response = self.client.get(reverse('vta:assessment_update', kwargs={'pk': self.assessment.pk}))
        self.assertEqual(response.status_code, 403)

    def test_update_valid_data(self):
        self._login()
        data = {
            'title': 'Updated Title',
            'description': 'Updated',
            'private': False,
            'hypothetical': False,
            'status': AssessmentStatus.PUBLISHED,
        }
        response = self.client.post(reverse('vta:assessment_update', kwargs={'pk': self.assessment.pk}), data)
        self.assertEqual(response.status_code, 302)
        self.assessment.refresh_from_db()
        self.assertEqual(self.assessment.title, 'Updated Title')


class AssessmentDeleteViewTest(BaseViewTest):
    """Tests for the assessment delete view."""

    def test_delete_analyst_access(self):
        self._login()
        response = self.client.get(reverse('vta:assessment_delete', kwargs={'pk': self.assessment.pk}))
        self.assertEqual(response.status_code, 200)

    def test_delete_respondent_forbidden(self):
        self._login('respondent')
        response = self.client.get(reverse('vta:assessment_delete', kwargs={'pk': self.assessment.pk}))
        self.assertEqual(response.status_code, 403)

    def test_delete_post(self):
        self._login()
        assessment_pk = self.assessment.pk
        response = self.client.post(reverse('vta:assessment_delete', kwargs={'pk': assessment_pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Assessment.objects.filter(pk=assessment_pk).exists())


# ---------------------------------------------------------------------------
# Node View Tests
# ---------------------------------------------------------------------------

class NodeListViewTest(BaseViewTest):
    """Tests for the node list view."""

    def test_list_requires_login(self):
        response = self.client.get(reverse('vta:node_list'))
        self.assert_login_redirect(response)

    def test_list_authenticated(self):
        self._login()
        response = self.client.get(reverse('vta:node_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'vta/node_list.html')

    def test_list_filter_by_type(self):
        self._login()
        response = self.client.get(reverse('vta:node_list'), {'type': NodeType.OBSERVING_SYSTEM})
        self.assertEqual(response.status_code, 200)

    def test_list_search(self):
        self._login()
        response = self.client.get(reverse('vta:node_list'), {'search': 'N1'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'N1')


class NodeDetailViewTest(BaseViewTest):
    """Tests for the node detail view."""

    def test_detail_requires_login(self):
        response = self.client.get(reverse('vta:node_detail', kwargs={'pk': self.node1.pk}))
        self.assert_login_redirect(response)

    def test_detail_authenticated(self):
        self._login()
        response = self.client.get(reverse('vta:node_detail', kwargs={'pk': self.node1.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'vta/node_detail.html')


class NodeCreateViewTest(BaseViewTest):
    """Tests for the node create view."""

    def test_create_analyst_access(self):
        self._login()
        response = self.client.get(reverse('vta:node_create'))
        self.assertEqual(response.status_code, 200)

    def test_create_respondent_forbidden(self):
        self._login('respondent')
        response = self.client.get(reverse('vta:node_create'))
        self.assertEqual(response.status_code, 403)

    def test_create_valid_data(self):
        self._login()
        data = {
            'type': NodeType.OBSERVING_SYSTEM,
            'title': 'New Node',
            'short_name': 'NN',
            'description': '',
            'organization': '',
            'funder': '',
            'funding_country': '',
            'website': '',
            'contact_information': '',
            'persistent_identifier': '',
            'hypothetical': False,
            'framework_name': '',
            'framework_url': '',
        }
        response = self.client.post(reverse('vta:node_create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Node.objects.filter(title='New Node').exists())


class NodeUpdateViewTest(BaseViewTest):
    """Tests for the node update view."""

    def test_update_analyst_access(self):
        self._login()
        response = self.client.get(reverse('vta:node_update', kwargs={'pk': self.node1.pk}))
        self.assertEqual(response.status_code, 200)

    def test_update_respondent_forbidden(self):
        self._login('respondent')
        response = self.client.get(reverse('vta:node_update', kwargs={'pk': self.node1.pk}))
        self.assertEqual(response.status_code, 403)


class NodeDeleteViewTest(BaseViewTest):
    """Tests for the node delete view."""

    def test_delete_analyst_access(self):
        self._login()
        response = self.client.get(reverse('vta:node_delete', kwargs={'pk': self.node1.pk}))
        self.assertEqual(response.status_code, 200)

    def test_delete_respondent_forbidden(self):
        self._login('respondent')
        response = self.client.get(reverse('vta:node_delete', kwargs={'pk': self.node1.pk}))
        self.assertEqual(response.status_code, 403)


class NodeSearchViewTest(BaseViewTest):
    """Tests for the node search view."""

    def test_search_requires_login(self):
        response = self.client.get(reverse('vta:node_search'))
        self.assert_login_redirect(response)

    def test_search_returns_results(self):
        self._login()
        response = self.client.get(reverse('vta:node_search'), {'q': 'N1'})
        self.assertEqual(response.status_code, 200)

    def test_search_json_response(self):
        self._login()
        response = self.client.get(
            reverse('vta:node_search'),
            {'q': 'N1'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')


# ---------------------------------------------------------------------------
# Link View Tests
# ---------------------------------------------------------------------------

class LinkListViewTest(BaseViewTest):
    """Tests for the link list view."""

    def test_list_requires_login(self):
        response = self.client.get(
            reverse('vta:link_list', kwargs={'assessment_id': self.assessment.pk})
        )
        self.assert_login_redirect(response)

    def test_list_authenticated(self):
        self._login()
        response = self.client.get(
            reverse('vta:link_list', kwargs={'assessment_id': self.assessment.pk})
        )
        self.assertEqual(response.status_code, 200)


class LinkCreateViewTest(BaseViewTest):
    """Tests for the link create view."""

    def test_create_requires_login(self):
        response = self.client.get(
            reverse('vta:link_create', kwargs={'assessment_id': self.assessment.pk})
        )
        self.assert_login_redirect(response)

    def test_create_authenticated(self):
        self._login()
        response = self.client.get(
            reverse('vta:link_create', kwargs={'assessment_id': self.assessment.pk})
        )
        self.assertEqual(response.status_code, 200)


class LinkUpdateViewTest(BaseViewTest):
    """Tests for the link update view."""

    def test_update_requires_login(self):
        response = self.client.get(reverse('vta:link_update', kwargs={'pk': self.link.pk}))
        self.assert_login_redirect(response)

    def test_update_authenticated(self):
        self._login()
        response = self.client.get(reverse('vta:link_update', kwargs={'pk': self.link.pk}))
        self.assertEqual(response.status_code, 200)


class LinkDeleteViewTest(BaseViewTest):
    """Tests for the link delete view."""

    def test_delete_requires_login(self):
        response = self.client.get(reverse('vta:link_delete', kwargs={'pk': self.link.pk}))
        self.assert_login_redirect(response)

    def test_delete_post(self):
        self._login()
        link_pk = self.link.pk
        response = self.client.post(reverse('vta:link_delete', kwargs={'pk': link_pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Link.objects.filter(pk=link_pk).exists())


# ---------------------------------------------------------------------------
# Survey Response Tests
# ---------------------------------------------------------------------------

class SurveyResponseViewTest(BaseViewTest):
    """Tests for the survey response view."""

    def test_response_requires_login(self):
        response = self.client.get(
            reverse(
                'vta:survey_response',
                kwargs={'assessment_id': self.assessment.pk, 'link_id': self.link.pk},
            )
        )
        self.assert_login_redirect(response)

    def test_response_authenticated(self):
        self._login('respondent')
        response = self.client.get(
            reverse(
                'vta:survey_response',
                kwargs={'assessment_id': self.assessment.pk, 'link_id': self.link.pk},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'vta/survey_response.html')

    def test_submit_response(self):
        self._login('respondent')
        data = {
            'performance_rating': 90,
            'criticality_rating': 8,
            'performance_rating_rationale': 'Great',
            'criticality_rating_rationale': 'Very important',
            'gaps_description': '',
            'attribute_description': '',
        }
        response = self.client.post(
            reverse(
                'vta:survey_response',
                kwargs={'assessment_id': self.assessment.pk, 'link_id': self.link.pk},
            ),
            data,
        )
        self.assertEqual(response.status_code, 302)
        self.link.refresh_from_db()
        self.assertEqual(self.link.performance_rating, 90)

    def test_submit_response_redirects_to_complete_when_last_link(self):
        self._login('respondent')
        data = {
            'performance_rating': 50,
            'criticality_rating': 5,
            'performance_rating_rationale': '',
            'criticality_rating_rationale': '',
            'gaps_description': '',
            'attribute_description': '',
        }
        response = self.client.post(
            reverse(
                'vta:survey_response',
                kwargs={'assessment_id': self.assessment.pk, 'link_id': self.link.pk},
            ),
            data,
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('/complete/', response.url)


class AssessmentCompleteViewTest(BaseViewTest):
    """Tests for the assessment complete view."""

    def test_complete_requires_login(self):
        response = self.client.get(
            reverse('vta:assessment_complete', kwargs={'pk': self.assessment.pk})
        )
        self.assert_login_redirect(response)

    def test_complete_authenticated(self):
        self._login()
        response = self.client.get(
            reverse('vta:assessment_complete', kwargs={'pk': self.assessment.pk})
        )
        self.assertEqual(response.status_code, 200)


# ---------------------------------------------------------------------------
# Visualization View Tests
# ---------------------------------------------------------------------------

class SankeyVisualizationViewTest(BaseViewTest):
    """Tests for the Sankey visualization view."""

    def test_sankey_requires_login(self):
        response = self.client.get(
            reverse('vta:sankey_visualization', kwargs={'pk': self.assessment.pk})
        )
        self.assert_login_redirect(response)

    def test_sankey_authenticated(self):
        self._login()
        response = self.client.get(
            reverse('vta:sankey_visualization', kwargs={'pk': self.assessment.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'vta/sankey_visualization.html')

    def test_sankey_contains_data(self):
        self._login()
        response = self.client.get(
            reverse('vta:sankey_visualization', kwargs={'pk': self.assessment.pk})
        )
        self.assertIn('sankey_data_json', response.context)


class ValueTreeJsonViewTest(BaseViewTest):
    """Tests for the value tree JSON API view."""

    def test_json_requires_login(self):
        response = self.client.get(
            reverse('vta:value_tree_json', kwargs={'pk': self.assessment.pk})
        )
        self.assert_login_redirect(response)

    def test_json_authenticated(self):
        self._login()
        response = self.client.get(
            reverse('vta:value_tree_json', kwargs={'pk': self.assessment.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_json_contains_nodes_and_adjacency(self):
        self._login()
        response = self.client.get(
            reverse('vta:value_tree_json', kwargs={'pk': self.assessment.pk})
        )
        data = response.json()
        self.assertIn('nodes', data)
        self.assertIn('adjacency', data)


class ResultsDashboardViewTest(BaseViewTest):
    """Tests for the results dashboard view."""

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('vta:results_dashboard'))
        self.assert_login_redirect(response)

    def test_dashboard_authenticated(self):
        self._login()
        response = self.client.get(reverse('vta:results_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'vta/results_dashboard.html')

    def test_dashboard_contains_stats(self):
        self._login()
        response = self.client.get(reverse('vta:results_dashboard'))
        self.assertIn('rating_stats', response.context)
        self.assertIn('assessments', response.context)


# ---------------------------------------------------------------------------
# User Profile View Tests
# ---------------------------------------------------------------------------

class UserProfileUpdateViewTest(BaseViewTest):
    """Tests for the user profile view."""

    def test_profile_requires_login(self):
        response = self.client.get(reverse('vta:user_profile'))
        self.assert_login_redirect(response)

    def test_profile_authenticated(self):
        self._login()
        response = self.client.get(reverse('vta:user_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'vta/user_profile.html')

    def test_profile_update(self):
        self._login()
        data = {
            'orcid': '0000-0000-0000-0000',
            'biography': 'Updated bio',
            'affiliation': 'New Org',
        }
        response = self.client.post(reverse('vta:user_profile'), data)
        self.assertEqual(response.status_code, 302)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.biography, 'Updated bio')


# ---------------------------------------------------------------------------
# Template Tag Tests
# ---------------------------------------------------------------------------

class TemplateTagTest(TestCase):
    """Tests for custom template tags."""

    def setUp(self):
        from vta.templatetags.vta_tags import has_group, has_any_group, is_analyst_or_admin
        self.has_group = has_group
        self.has_any_group = has_any_group
        self.is_analyst_or_admin = is_analyst_or_admin

        self.user = create_user('testuser')
        add_to_group(self.user, 'Analyst')
        self.anonymous = type('obj', (object,), {'is_authenticated': False})()

    def test_has_group_true(self):
        self.assertTrue(self.has_group(self.user, 'Analyst'))

    def test_has_group_false(self):
        self.assertFalse(self.has_group(self.user, 'Admin'))

    def test_has_group_anonymous(self):
        self.assertFalse(self.has_group(self.anonymous, 'Analyst'))

    def test_has_any_group_true(self):
        self.assertTrue(self.has_any_group(self.user, 'Analyst,Admin'))

    def test_has_any_group_false(self):
        self.assertFalse(self.has_any_group(self.user, 'Admin,Respondent'))

    def test_has_any_group_anonymous(self):
        self.assertFalse(self.has_any_group(self.anonymous, 'Analyst'))

    def test_is_analyst_or_admin_true(self):
        self.assertTrue(self.is_analyst_or_admin(self.user))

    def test_is_analyst_or_admin_false(self):
        resp = create_user('resp')
        add_to_group(resp, 'Respondent')
        self.assertFalse(self.is_analyst_or_admin(resp))

    def test_is_analyst_or_admin_anonymous(self):
        self.assertFalse(self.is_analyst_or_admin(self.anonymous))


# ---------------------------------------------------------------------------
# URL Resolution Tests
# ---------------------------------------------------------------------------

class UrlResolutionTest(TestCase):
    """Test that all named URLs resolve correctly."""

    def setUp(self):
        self.user = create_user('testuser')
        add_to_group(self.user, 'Analyst')
        self.profile = self.user.profile
        self.assessment = create_assessment(self.profile)
        self.node = create_node(self.profile)

    def test_home_url(self):
        url = reverse('vta:home')
        self.assertEqual(url, '/')

    def test_assessment_list_url(self):
        url = reverse('vta:assessment_list')
        self.assertEqual(url, '/assessments/')

    def test_assessment_create_url(self):
        url = reverse('vta:assessment_create')
        self.assertEqual(url, '/assessments/create/')

    def test_assessment_detail_url(self):
        url = reverse('vta:assessment_detail', kwargs={'pk': self.assessment.pk})
        self.assertEqual(url, f'/assessments/{self.assessment.pk}/')

    def test_assessment_update_url(self):
        url = reverse('vta:assessment_update', kwargs={'pk': self.assessment.pk})
        self.assertEqual(url, f'/assessments/{self.assessment.pk}/edit/')

    def test_assessment_delete_url(self):
        url = reverse('vta:assessment_delete', kwargs={'pk': self.assessment.pk})
        self.assertEqual(url, f'/assessments/{self.assessment.pk}/delete/')

    def test_node_list_url(self):
        url = reverse('vta:node_list')
        self.assertEqual(url, '/nodes/')

    def test_node_create_url(self):
        url = reverse('vta:node_create')
        self.assertEqual(url, '/nodes/create/')

    def test_node_detail_url(self):
        url = reverse('vta:node_detail', kwargs={'pk': self.node.pk})
        self.assertEqual(url, f'/nodes/{self.node.pk}/')

    def test_node_update_url(self):
        url = reverse('vta:node_update', kwargs={'pk': self.node.pk})
        self.assertEqual(url, f'/nodes/{self.node.pk}/edit/')

    def test_node_delete_url(self):
        url = reverse('vta:node_delete', kwargs={'pk': self.node.pk})
        self.assertEqual(url, f'/nodes/{self.node.pk}/delete/')

    def test_node_search_url(self):
        url = reverse('vta:node_search')
        self.assertEqual(url, '/nodes/search/')

    def test_link_list_url(self):
        url = reverse('vta:link_list', kwargs={'assessment_id': self.assessment.pk})
        self.assertEqual(url, f'/assessments/{self.assessment.pk}/links/')

    def test_link_create_url(self):
        url = reverse('vta:link_create', kwargs={'assessment_id': self.assessment.pk})
        self.assertEqual(url, f'/assessments/{self.assessment.pk}/links/create/')

    def test_survey_response_url(self):
        an1 = add_node_to_assessment(self.assessment, self.node)
        node2 = create_node(self.profile, title='N2', short_name='N2')
        an2 = add_node_to_assessment(self.assessment, node2)
        link = create_link(an1, an2)
        url = reverse(
            'vta:survey_response',
            kwargs={'assessment_id': self.assessment.pk, 'link_id': link.pk},
        )
        self.assertEqual(url, f'/assessments/{self.assessment.pk}/respond/{link.pk}/')

    def test_assessment_complete_url(self):
        url = reverse('vta:assessment_complete', kwargs={'pk': self.assessment.pk})
        self.assertEqual(url, f'/assessments/{self.assessment.pk}/complete/')

    def test_sankey_visualization_url(self):
        url = reverse('vta:sankey_visualization', kwargs={'pk': self.assessment.pk})
        self.assertEqual(url, f'/assessments/{self.assessment.pk}/sankey/')

    def test_value_tree_json_url(self):
        url = reverse('vta:value_tree_json', kwargs={'pk': self.assessment.pk})
        self.assertEqual(url, f'/assessments/{self.assessment.pk}/tree-json/')

    def test_results_dashboard_url(self):
        url = reverse('vta:results_dashboard')
        self.assertEqual(url, '/results/')

    def test_user_profile_url(self):
        url = reverse('vta:user_profile')
        self.assertEqual(url, '/profile/')