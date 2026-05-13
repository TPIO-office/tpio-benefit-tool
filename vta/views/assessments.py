"""Views for Assessment CRUD and management."""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.urls import reverse_lazy

from ..models import Assessment


class AssessmentListView(LoginRequiredMixin, ListView):
    """List all assessments (public ones for respondents, all for analysts)."""

    model = Assessment
    template_name = 'vta/assessment_list.html'
    context_object_name = 'assessments'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.groups.filter(name__in=['Analyst', 'Admin']).exists():
            return qs
        return qs.filter(private=False, status='published')


class AssessmentDetailView(LoginRequiredMixin, DetailView):
    """View assessment details including nodes and links."""

    model = Assessment
    template_name = 'vta/assessment_detail.html'
    context_object_name = 'assessment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nodes'] = self.object.assessment_nodes.select_related('node').all()
        context['links'] = (
            self.object.assessment_nodes
            .select_related('node')
            .prefetch_related(
                'output_links',
                'output_links__target_assessment_node__node',
                'output_links__source_assessment_node__node',
                'input_links',
            )
            .all()
        )
        return context


class AssessmentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new assessment (analysts only)."""

    model = Assessment
    template_name = 'vta/assessment_form.html'
    fields = ['title', 'description', 'private', 'hypothetical', 'status']
    success_url = reverse_lazy('vta:assessment_list')

    def test_func(self):
        return self.request.user.groups.filter(name__in=['Analyst', 'Admin']).exists()

    def form_valid(self, form):
        try:
            form.instance.created_by = self.request.user.profile
        except Exception:
            pass
        return super().form_valid(form)


class AssessmentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Edit an existing assessment (analysts only)."""

    model = Assessment
    template_name = 'vta/assessment_form.html'
    fields = ['title', 'description', 'private', 'hypothetical', 'status']
    success_url = reverse_lazy('vta:assessment_list')

    def test_func(self):
        return self.request.user.groups.filter(name__in=['Analyst', 'Admin']).exists()


class AssessmentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete an assessment (analysts only)."""

    model = Assessment
    template_name = 'vta/assessment_confirm_delete.html'
    success_url = reverse_lazy('vta:assessment_list')

    def test_func(self):
        return self.request.user.groups.filter(name__in=['Analyst', 'Admin']).exists()