"""Views for Link management and survey response collection."""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

from vta.models import Assessment, AssessmentNode, Link, NodeType
from vta.forms import LinkForm, SurveyResponseForm


class LinkListView(LoginRequiredMixin, ListView):
    """List all links within an assessment."""

    template_name = 'vta/link_list.html'
    context_object_name = 'links'

    def get_queryset(self):
        assessment_id = self.kwargs['assessment_id']
        return (
            Link.objects.filter(source_assessment_node__assessment_id=assessment_id)
            .select_related(
                'source_assessment_node__node',
                'target_assessment_node__node',
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assessment'] = get_object_or_404(Assessment, pk=self.kwargs['assessment_id'])
        return context


class LinkCreateView(LoginRequiredMixin, CreateView):
    """Create a new link between assessment nodes."""

    model = Link
    form_class = LinkForm
    template_name = 'vta/link_form.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        assessment_id = self.kwargs.get('assessment_id')
        if assessment_id:
            form.fields['source_assessment_node'].queryset = AssessmentNode.objects.filter(
                assessment_id=assessment_id
            )
            form.fields['target_assessment_node'].queryset = AssessmentNode.objects.filter(
                assessment_id=assessment_id
            )
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assessment'] = get_object_or_404(Assessment, pk=self.kwargs.get('assessment_id'))
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Link created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'vta:assessment_detail',
            kwargs={'pk': self.object.source_assessment_node.assessment_id},
        )


class LinkUpdateView(LoginRequiredMixin, UpdateView):
    """Edit an existing link (ratings and rationale)."""

    model = Link
    form_class = LinkForm
    template_name = 'vta/link_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assessment'] = self.object.source_assessment_node.assessment
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Link updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'vta:assessment_detail',
            kwargs={'pk': self.object.source_assessment_node.assessment_id},
        )


class LinkDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a link."""

    model = Link
    template_name = 'vta/link_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy(
            'vta:assessment_detail',
            kwargs={'pk': self.object.source_assessment_node.assessment_id},
        )


class SurveyResponseView(LoginRequiredMixin, UpdateView):
    """Respondent-facing view for submitting ratings on a link."""

    model = Link
    form_class = SurveyResponseForm
    template_name = 'vta/survey_response.html'

    def get_form(self, form_class=None):
        form_class = self.get_form_class()
        if self.request.method == 'POST':
            return form_class(self.request.POST)
        return form_class()

    def get_object(self, queryset=None):
        return get_object_or_404(
            Link,
            pk=self.kwargs['link_id'],
            source_assessment_node__assessment__pk=self.kwargs['assessment_id'],
        )

    def form_valid(self, form):
        self.object.performance_rating = form.cleaned_data.get('performance_rating')
        self.object.criticality_rating = form.cleaned_data.get('criticality_rating')
        self.object.performance_rating_rationale = form.cleaned_data.get('performance_rating_rationale')
        self.object.criticality_rating_rationale = form.cleaned_data.get('criticality_rating_rationale')
        self.object.gaps_description = form.cleaned_data.get('gaps_description')
        self.object.attribute_description = form.cleaned_data.get('attribute_description')
        self.object.save()
        messages.success(self.request, 'Your response has been submitted.')
        return redirect(self.get_success_url())

    def get_success_url(self):
        assessment_id = self.kwargs['assessment_id']
        links = Link.objects.filter(
            source_assessment_node__assessment_id=assessment_id
        ).order_by('pk')
        try:
            next_link = links.get(pk__gt=self.object.pk)
            return reverse_lazy(
                'vta:survey_response',
                kwargs={'assessment_id': assessment_id, 'link_id': next_link.pk},
            )
        except Link.DoesNotExist:
            return reverse_lazy(
                'vta:assessment_complete',
                kwargs={'pk': assessment_id},
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['source_node'] = self.object.source_assessment_node.node
        context['target_node'] = self.object.target_assessment_node.node
        context['assessment'] = self.object.source_assessment_node.assessment
        return context


class AssessmentCompleteView(LoginRequiredMixin, DetailView):
    """Confirmation view shown after completing all survey responses."""

    model = Assessment
    template_name = 'vta/assessment_complete.html'
    context_object_name = 'assessment'