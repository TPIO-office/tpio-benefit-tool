"""Views for Node (Object Library) management."""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.urls import reverse_lazy
from django.http import JsonResponse

from vta.models import Node, NodeType


class NodeListView(LoginRequiredMixin, ListView):
    """List all nodes in the object library."""

    model = Node
    template_name = 'vta/node_list.html'
    context_object_name = 'nodes'
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset()
        node_type = self.request.GET.get('type')
        search = self.request.GET.get('search')
        if node_type:
            qs = qs.filter(type=node_type)
        if search:
            qs = qs.filter(title__icontains=search) | qs.filter(short_name__icontains=search)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['node_types'] = NodeType.choices
        return context


class NodeDetailView(LoginRequiredMixin, DetailView):
    """View node details."""

    model = Node
    template_name = 'vta/node_detail.html'
    context_object_name = 'node'


class NodeCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new node in the object library."""

    model = Node
    template_name = 'vta/node_form.html'
    fields = [
        'type', 'title', 'short_name', 'description',
        'organization', 'funder', 'funding_country', 'website',
        'contact_information', 'persistent_identifier', 'hypothetical',
        'framework_name', 'framework_url',
    ]
    success_url = reverse_lazy('vta:node_list')

    def test_func(self):
        return self.request.user.groups.filter(name__in=['Analyst', 'Admin']).exists()

    def form_valid(self, form):
        from vta.models import UserProfile
        try:
            form.instance.created_by = self.request.user.profile
        except UserProfile.DoesNotExist:
            profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
            form.instance.created_by = profile
        return super().form_valid(form)


class NodeUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Edit an existing node."""

    model = Node
    template_name = 'vta/node_form.html'
    fields = [
        'type', 'title', 'short_name', 'description',
        'organization', 'funder', 'funding_country', 'website',
        'contact_information', 'persistent_identifier', 'hypothetical',
        'framework_name', 'framework_url',
    ]
    success_url = reverse_lazy('vta:node_list')

    def test_func(self):
        return self.request.user.groups.filter(name__in=['Analyst', 'Admin']).exists()


class NodeDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a node."""

    model = Node
    template_name = 'vta/node_confirm_delete.html'
    success_url = reverse_lazy('vta:node_list')

    def test_func(self):
        return self.request.user.groups.filter(name__in=['Analyst', 'Admin']).exists()


class NodeSearchView(LoginRequiredMixin, ListView):
    """API-like view for searching nodes (used by assessment node assignment)."""

    model = Node
    template_name = 'vta/node_search_results.html'

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.GET.get('q', '')
        if search:
            qs = qs.filter(title__icontains=search) | qs.filter(short_name__icontains=search)
        return qs[:50]

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            nodes = self.get_queryset()
            return JsonResponse({
                'nodes': [
                    {'id': n.pk, 'title': n.title, 'type': n.get_type_display()}
                    for n in nodes
                ]
            })
        return super().render_to_response(context, **response_kwargs)