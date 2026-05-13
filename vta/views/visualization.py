"""Views for Sankey diagram and value tree visualization."""

import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, TemplateView
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from ..models import Assessment, Link


class SankeyVisualizationView(LoginRequiredMixin, DetailView):
    """Render the Sankey diagram visualization for an assessment."""

    model = Assessment
    template_name = 'vta/sankey_visualization.html'
    context_object_name = 'assessment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        links = (
            Link.objects.filter(source_assessment_node__assessment=self.object)
            .select_related(
                'source_assessment_node__node',
                'target_assessment_node__node',
            )
        )
        sankey_data = self._build_sankey_data(links)
        context['sankey_data'] = json.dumps(sankey_data)
        context['sankey_data_json'] = sankey_data
        return context

    def _build_sankey_data(self, links):
        """Build data structure for D3 Sankey diagram."""
        nodes = {}
        node_list = []
        link_list = []

        for link in links:
            source_node = link.source_assessment_node.node
            target_node = link.target_assessment_node.node

            if source_node.pk not in nodes:
                nodes[source_node.pk] = len(node_list)
                node_list.append({
                    'name': source_node.title,
                    'type': source_node.get_type_display(),
                })
            if target_node.pk not in nodes:
                nodes[target_node.pk] = len(node_list)
                node_list.append({
                    'name': target_node.title,
                    'type': target_node.get_type_display(),
                })

            value = link.performance_rating or 0
            link_list.append({
                'source': nodes[source_node.pk],
                'target': nodes[target_node.pk],
                'value': value,
                'criticality': link.criticality_rating or 0,
                'gaps': link.gaps_description or '',
                'id': link.pk,
            })

        return {'nodes': node_list, 'links': link_list}


class ValueTreeJsonView(LoginRequiredMixin, DetailView):
    """API endpoint returning value tree data as JSON for frontend visualization."""

    model = Assessment
    template_name = None  # Returns JSON only

    def render_to_response(self, context):
        links = (
            Link.objects.filter(source_assessment_node__assessment=self.object)
            .select_related(
                'source_assessment_node__node',
                'target_assessment_node__node',
            )
        )
        data = self._build_tree_data(links)
        return JsonResponse(data)

    def _build_tree_data(self, links):
        """Build hierarchical tree structure for visualization."""
        adjacency = {}
        all_nodes = set()

        for link in links:
            source_id = link.source_assessment_node.node.pk
            target_id = link.target_assessment_node.node.pk
            all_nodes.add(source_id)
            all_nodes.add(target_id)
            if source_id not in adjacency:
                adjacency[source_id] = []
            adjacency[source_id].append({
                'target_id': target_id,
                'performance_rating': link.performance_rating,
                'criticality_rating': link.criticality_rating,
                'link_id': link.pk,
            })

        nodes_data = {}
        for node_id in all_nodes:
            from ..models import Node
            try:
                node = Node.objects.get(pk=node_id)
                nodes_data[node_id] = {
                    'title': node.title,
                    'type': node.get_type_display(),
                    'short_name': node.short_name,
                }
            except Node.DoesNotExist:
                pass

        return {
            'nodes': nodes_data,
            'adjacency': adjacency,
        }


class ResultsDashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard view showing aggregate results across all assessments."""

    template_name = 'vta/results_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.db.models import Avg, Count, Q

        assessments = Assessment.objects.annotate(
            node_count=Count('assessment_nodes'),
            link_count=Count('assessment_nodes__output_links'),
        )
        context['assessments'] = assessments

        rating_stats = Link.objects.aggregate(
            avg_performance=Avg('performance_rating'),
            avg_criticality=Avg('criticality_rating'),
            total_links=Count('pk'),
            rated_links=Count('pk', filter=Q(performance_rating__isnull=False)),
        )
        context['rating_stats'] = rating_stats
        return context