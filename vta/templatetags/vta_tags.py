"""Custom template tags for role-based visibility in templates."""

from django import template

register = template.Library()


@register.filter
def has_group(user, group_name):
    """Check if user belongs to a specific group.

    Usage: {% if user|has_group:'Analyst' %}...{% endif %}
    """
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name=group_name).exists()


@register.filter
def has_any_group(user, group_names):
    """Check if user belongs to any of the specified groups (comma-separated).

    Usage: {% if user|has_any_group:'Analyst,Admin' %}...{% endif %}
    """
    if not user or not user.is_authenticated:
        return False
    groups = [g.strip() for g in group_names.split(',')]
    return user.groups.filter(name__in=groups).exists()


@register.simple_tag
def is_analyst_or_admin(user):
    """Return True if user is an analyst or admin."""
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name__in=['Analyst', 'Admin']).exists()