"""Django admin configuration for analyst-facing management of VTA entities."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import (
    Assessment,
    AssessmentNode,
    Link,
    Node,
    UserProfile,
    NodeType,
)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'private', 'hypothetical', 'created_by', 'created_timestamp')
    list_filter = ('status', 'private', 'hypothetical')
    search_fields = ('title', 'description')
    readonly_fields = ('created_timestamp', 'updated_timestamp', 'created_by')
    date_hierarchy = 'created_timestamp'

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            try:
                obj.created_by = request.user.profile
            except UserProfile.DoesNotExist:
                pass
        super().save_model(request, obj, form, change)


@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'short_name', 'created_by', 'created_timestamp')
    list_filter = ('type', 'hypothetical')
    search_fields = ('title', 'short_name', 'description', 'organization')
    readonly_fields = ('created_timestamp', 'updated_timestamp')
    fieldsets = (
        ('Basic Information', {
            'fields': ('type', 'title', 'short_name', 'description'),
        }),
        ('Organization Details (for observing systems, data products, applications)', {
            'fields': ('organization', 'funder', 'funding_country', 'website',
                       'contact_information', 'persistent_identifier', 'hypothetical'),
            'classes': ('collapse',),
        }),
        ('Framework Details (for societal benefit areas)', {
            'fields': ('framework_name', 'framework_url'),
            'classes': ('collapse',),
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_timestamp', 'updated_timestamp'),
            'classes': ('collapse',),
        }),
    )


class AssessmentNodeInline(admin.TabularInline):
    model = AssessmentNode
    extra = 0
    autocomplete_fields = ('node',)


@admin.register(AssessmentNode)
class AssessmentNodeAdmin(admin.ModelAdmin):
    list_display = ('assessment', 'node', 'node_type_display')
    list_filter = ('assessment__status',)
    search_fields = ('node__title', 'assessment__title')
    autocomplete_fields = ('assessment', 'node')

    def node_type_display(self, obj):
        return obj.node.get_type_display()
    node_type_display.short_description = 'Node Type'


class LinkInline(admin.TabularInline):
    model = Link
    extra = 0
    autocomplete_fields = ('source_assessment_node', 'target_assessment_node')


@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = (
        'source_node_title',
        'target_node_title',
        'performance_rating',
        'criticality_rating',
        'assessment_title',
    )
    list_filter = ('source_assessment_node__assessment__status',)
    search_fields = (
        'source_assessment_node__node__title',
        'target_assessment_node__node__title',
    )
    autocomplete_fields = ('source_assessment_node', 'target_assessment_node')

    def source_node_title(self, obj):
        return obj.source_assessment_node.node.title
    source_node_title.short_description = 'Source'

    def target_node_title(self, obj):
        return obj.target_assessment_node.node.title
    target_node_title.short_description = 'Target'

    def assessment_title(self, obj):
        return obj.source_assessment_node.assessment.title
    assessment_title.short_description = 'Assessment'