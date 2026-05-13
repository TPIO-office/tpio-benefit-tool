"""Django ORM models for the Value Tree Analysis survey platform.

Maps the original Flask/SQLAlchemy data model from usaon-benefit-tool to Django ORM.
Uses built-in django.contrib.auth.User instead of custom User model.
All node subtype fields are kept in a single Node table (like the original SQLAlchemy design)
to avoid multi-table inheritance complications with shared PKs.
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class AssessmentStatus(models.TextChoices):
    """Assessment lifecycle statuses."""

    WORK_IN_PROGRESS = 'work_in_progress', 'Work In Progress'
    PUBLISHED = 'published', 'Published'
    CLOSED = 'closed', 'Closed'
    ARCHIVED = 'archived', 'Archived'


class NodeType(models.TextChoices):
    """Types of nodes in the value tree."""

    OBSERVING_SYSTEM = 'observing_system', 'Observing System'
    DATA_PRODUCT = 'data_product', 'Data Product'
    APPLICATION = 'application', 'Application'
    SOCIETAL_BENEFIT_AREA = 'societal_benefit_area', 'Societal Benefit Area'


class UserProfile(models.Model):
    """Extended profile for django.contrib.auth.User.

    Replaces the original custom User + Role tables with Django's built-in auth system.
    Roles are managed via Django Groups.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    orcid = models.CharField(max_length=64, blank=True, null=True)
    biography = models.TextField(blank=True, null=True)
    affiliation = models.CharField(max_length=256, blank=True, null=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username}'


class Assessment(models.Model):
    """A Value Tree Analysis survey/assessment configuration.

    Created by analysts, filled by respondents. Contains a collection of nodes
    and links that form the value tree structure.
    """

    title = models.CharField(max_length=128)
    description = models.TextField(max_length=4096, blank=True, null=True)
    private = models.BooleanField(default=False)
    hypothetical = models.BooleanField(default=False)
    status = models.CharField(
        max_length=32,
        choices=AssessmentStatus.choices,
        default=AssessmentStatus.WORK_IN_PROGRESS,
    )
    created_by = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='created_assessments',
    )
    created_timestamp = models.DateTimeField(auto_now_add=True)
    updated_timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Assessment'
        verbose_name_plural = 'Assessments'
        ordering = ['-created_timestamp']

    def __str__(self):
        return self.title

    @property
    def is_active(self):
        """Check if assessment is in work-in-progress or published state."""
        return self.status in (
            AssessmentStatus.WORK_IN_PROGRESS,
            AssessmentStatus.PUBLISHED,
        )


class Node(models.Model):
    """Node in the Object Library.

    Represents an entity in the value tree: observing systems, data products,
    applications, or societal benefit areas. All subtype-specific fields are
    included directly (mirroring SQLAlchemy polymorphic approach with discriminator).
    """

    type = models.CharField(max_length=32, choices=NodeType.choices)
    title = models.CharField(max_length=128)
    short_name = models.CharField(max_length=256)
    description = models.TextField(max_length=4096, blank=True, null=True)
    created_by = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='created_nodes',
    )
    created_timestamp = models.DateTimeField(auto_now_add=True)
    updated_timestamp = models.DateTimeField(auto_now=True)

    # Fields from NodeSubtypeOther (observing_system, data_product, application)
    organization = models.CharField(max_length=256, blank=True, null=True)
    funder = models.CharField(max_length=256, blank=True, null=True)
    funding_country = models.CharField(max_length=256, blank=True, null=True)
    website = models.URLField(max_length=256, blank=True, null=True)
    contact_information = models.CharField(max_length=256, blank=True, null=True)
    persistent_identifier = models.CharField(max_length=256, blank=True, null=True)
    hypothetical = models.BooleanField(default=False)

    # Fields from NodeSubtypeSocietalBenefitArea
    framework_name = models.CharField(max_length=256, blank=True, null=True)
    framework_url = models.URLField(max_length=512, blank=True, null=True)

    class Meta:
        verbose_name = 'Node'
        verbose_name_plural = 'Nodes (Object Library)'
        ordering = ['type', 'title']

    def __str__(self):
        return f'{self.get_type_display()}: {self.title}'

    @property
    def is_other_subtype(self):
        """Check if this node uses the 'other' subtype fields."""
        return self.type in (
            NodeType.OBSERVING_SYSTEM,
            NodeType.DATA_PRODUCT,
            NodeType.APPLICATION,
        )

    @property
    def is_sba_subtype(self):
        """Check if this node is a societal benefit area."""
        return self.type == NodeType.SOCIETAL_BENEFIT_AREA


class AssessmentNode(models.Model):
    """Instance of a Node within a specific Assessment.

    Junction entity that links Nodes to Assessments and serves as the anchor
    for Link relationships within an assessment context.
    """

    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name='assessment_nodes',
    )
    node = models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        related_name='assessment_instances',
    )

    class Meta:
        verbose_name = 'Assessment Node'
        verbose_name_plural = 'Assessment Nodes'
        unique_together = ('assessment', 'node')
        ordering = ['node__type', 'node__title']

    def __str__(self):
        return f'{self.assessment.title} -> {self.node.title}'

    @property
    def is_application(self):
        """Check if this assessment node is an application type."""
        return self.node.type == NodeType.APPLICATION


class Link(models.Model):
    """Directed edge between two AssessmentNodes within an Assessment.

    Represents the value flow connection in the value tree, with performance
    and criticality ratings provided by respondents.
    """

    source_assessment_node = models.ForeignKey(
        AssessmentNode,
        on_delete=models.CASCADE,
        related_name='output_links',
    )
    target_assessment_node = models.ForeignKey(
        AssessmentNode,
        on_delete=models.CASCADE,
        related_name='input_links',
    )
    performance_rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text='Rating from 1-100',
    )
    criticality_rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text='Rating from 1-10',
    )
    performance_rating_rationale = models.TextField(
        max_length=8192,
        blank=True,
        null=True,
    )
    criticality_rating_rationale = models.TextField(
        max_length=8192,
        blank=True,
        null=True,
    )
    gaps_description = models.TextField(max_length=8192, blank=True, null=True)
    attribute_description = models.CharField(max_length=512, blank=True, null=True)

    class Meta:
        verbose_name = 'Link'
        verbose_name_plural = 'Links (Value Tree Edges)'
        unique_together = ('source_assessment_node', 'target_assessment_node')

    def __str__(self):
        return f'{self.source_assessment_node.node.title} -> {self.target_assessment_node.node.title}'

    def clean(self):
        """Validate that source and target belong to the same assessment."""
        if (
            self.source_assessment_node_id
            and self.target_assessment_node_id
            and self.source_assessment_node.assessment_id != self.target_assessment_node.assessment_id
        ):
            from django.core.exceptions import ValidationError

            raise ValidationError(
                'Source and target nodes must belong to the same assessment.'
            )