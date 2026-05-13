"""Main views: home, login redirect, user profile."""

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, RedirectView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import render

from ..forms import UserProfileForm


class HomeView(TemplateView):
    """Home page with overview of available assessments."""

    template_name = 'vta/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from ..models import Assessment

        if self.request.user.is_authenticated:
            is_analyst = self.request.user.groups.filter(
                name__in=['Analyst', 'Admin']
            ).exists()
            if is_analyst:
                context['assessments'] = Assessment.objects.all().order_by('-created_timestamp')
            else:
                context['assessments'] = Assessment.objects.filter(
                    private=False, status='published'
                ).order_by('-created_timestamp')
        else:
            context['assessments'] = Assessment.objects.filter(
                private=False, status='published'
            ).order_by('-created_timestamp')
        return context


class LoginRedirectView(RedirectView):
    """Redirect to Django admin login page."""

    url = reverse_lazy('admin:login')


class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Allow users to update their profile information."""

    model = None  # We use UserProfileForm directly
    form_class = UserProfileForm
    template_name = 'vta/user_profile.html'
    success_url = reverse_lazy('vta:user_profile')

    def get_object(self, queryset=None):
        return self.request.user.profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context