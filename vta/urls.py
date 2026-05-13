"""URL routing for VTA app."""

from django.urls import path

from vta.views.assessments import (
    AssessmentCreateView,
    AssessmentDeleteView,
    AssessmentDetailView,
    AssessmentListView,
    AssessmentUpdateView,
)
from vta.views.links import (
    AssessmentCompleteView,
    LinkCreateView,
    LinkDeleteView,
    LinkListView,
    LinkUpdateView,
    SurveyResponseView,
)
from vta.views.main import HomeView, UserProfileUpdateView
from vta.views.nodes import (
    NodeCreateView,
    NodeDeleteView,
    NodeDetailView,
    NodeListView,
    NodeSearchView,
    NodeUpdateView,
)
from vta.views.visualization import (
    ResultsDashboardView,
    SankeyVisualizationView,
    ValueTreeJsonView,
)

app_name = 'vta'

urlpatterns = [
    # Home
    path('', HomeView.as_view(), name='home'),

    # Assessments
    path('assessments/', AssessmentListView.as_view(), name='assessment_list'),
    path('assessments/create/', AssessmentCreateView.as_view(), name='assessment_create'),
    path('assessments/<int:pk>/', AssessmentDetailView.as_view(), name='assessment_detail'),
    path('assessments/<int:pk>/edit/', AssessmentUpdateView.as_view(), name='assessment_update'),
    path('assessments/<int:pk>/delete/', AssessmentDeleteView.as_view(), name='assessment_delete'),

    # Nodes (Object Library)
    path('nodes/', NodeListView.as_view(), name='node_list'),
    path('nodes/create/', NodeCreateView.as_view(), name='node_create'),
    path('nodes/<int:pk>/', NodeDetailView.as_view(), name='node_detail'),
    path('nodes/<int:pk>/edit/', NodeUpdateView.as_view(), name='node_update'),
    path('nodes/<int:pk>/delete/', NodeDeleteView.as_view(), name='node_delete'),
    path('nodes/search/', NodeSearchView.as_view(), name='node_search'),

    # Links (within an assessment)
    path(
        'assessments/<int:assessment_id>/links/',
        LinkListView.as_view(),
        name='link_list',
    ),
    path(
        'assessments/<int:assessment_id>/links/create/',
        LinkCreateView.as_view(),
        name='link_create',
    ),
    path('links/<int:pk>/edit/', LinkUpdateView.as_view(), name='link_update'),
    path('links/<int:pk>/delete/', LinkDeleteView.as_view(), name='link_delete'),

    # Survey response (respondent-facing)
    path(
        'assessments/<int:assessment_id>/respond/<int:link_id>/',
        SurveyResponseView.as_view(),
        name='survey_response',
    ),
    path('assessments/<int:pk>/complete/', AssessmentCompleteView.as_view(), name='assessment_complete'),

    # Visualization
    path(
        'assessments/<int:pk>/sankey/',
        SankeyVisualizationView.as_view(),
        name='sankey_visualization',
    ),
    path(
        'assessments/<int:pk>/tree-json/',
        ValueTreeJsonView.as_view(),
        name='value_tree_json',
    ),
    path('results/', ResultsDashboardView.as_view(), name='results_dashboard'),

    # User profile
    path('profile/', UserProfileUpdateView.as_view(), name='user_profile'),
]