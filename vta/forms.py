"""Django forms for VTA survey interaction and admin configuration."""

from django import forms

from .models import (
    Assessment,
    AssessmentNode,
    Link,
    Node,
    NodeType,
    UserProfile,
)


class AssessmentForm(forms.ModelForm):
    """Form for creating/editing assessments (analyst use)."""

    class Meta:
        model = Assessment
        fields = ['title', 'description', 'private', 'hypothetical', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'private': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'hypothetical': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class NodeForm(forms.ModelForm):
    """Form for creating/editing nodes in the object library.

    Dynamically shows/hides subtype-specific fields based on node type selection.
    """

    class Meta:
        model = Node
        fields = [
            'type', 'title', 'short_name', 'description',
            # Other subtype fields
            'organization', 'funder', 'funding_country', 'website',
            'contact_information', 'persistent_identifier', 'hypothetical',
            # SBA subtype fields
            'framework_name', 'framework_url',
        ]
        widgets = {
            'type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'short_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'organization': forms.TextInput(attrs={'class': 'form-control'}),
            'funder': forms.TextInput(attrs={'class': 'form-control'}),
            'funding_country': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'contact_information': forms.TextInput(attrs={'class': 'form-control'}),
            'persistent_identifier': forms.TextInput(attrs={'class': 'form-control'}),
            'hypothetical': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'framework_name': forms.TextInput(attrs={'class': 'form-control'}),
            'framework_url': forms.URLInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['organization'].required = False
        self.fields['funder'].required = False
        self.fields['funding_country'].required = False
        self.fields['contact_information'].required = False


class LinkForm(forms.ModelForm):
    """Form for creating/editing links (value tree edges) with ratings."""

    class Meta:
        model = Link
        fields = [
            'source_assessment_node',
            'target_assessment_node',
            'performance_rating',
            'criticality_rating',
            'performance_rating_rationale',
            'criticality_rating_rationale',
            'gaps_description',
            'attribute_description',
        ]
        widgets = {
            'source_assessment_node': forms.Select(attrs={'class': 'form-control'}),
            'target_assessment_node': forms.Select(attrs={'class': 'form-control'}),
            'performance_rating': forms.NumberInput(
                attrs={'class': 'form-control', 'min': 1, 'max': 100}
            ),
            'criticality_rating': forms.NumberInput(
                attrs={'class': 'form-control', 'min': 1, 'max': 10}
            ),
            'performance_rating_rationale': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
            ),
            'criticality_rating_rationale': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
            ),
            'gaps_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'attribute_description': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        source = cleaned_data.get('source_assessment_node')
        target = cleaned_data.get('target_assessment_node')
        if source and target and source.assessment_id != target.assessment_id:
            self.add_error(
                None,
                'Source and target nodes must belong to the same assessment.',
            )
        return cleaned_data


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile information."""

    class Meta:
        model = UserProfile
        fields = ['orcid', 'biography', 'affiliation']
        widgets = {
            'orcid': forms.TextInput(attrs={'class': 'form-control'}),
            'biography': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'affiliation': forms.TextInput(attrs={'class': 'form-control'}),
        }


class AssessmentNodeAddForm(forms.Form):
    """Form for adding nodes to an assessment."""

    node = forms.ModelChoiceField(
        queryset=Node.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Select Node',
    )

    def __init__(self, *args, assessment=None, **kwargs):
        super().__init__(*args, **kwargs)
        if assessment:
            existing_node_ids = assessment.assessment_nodes.values_list('node_id', flat=True)
            self.fields['node'].queryset = Node.objects.exclude(id__in=existing_node_ids)


class SurveyResponseForm(forms.Form):
    """Dynamic form for respondents to submit ratings on a specific link."""

    performance_rating = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=100,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 100}),
        label='Performance Rating (1-100)',
    )
    criticality_rating = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=10,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
        label='Criticality Rating (1-10)',
    )
    performance_rating_rationale = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label='Performance Rationale',
    )
    criticality_rating_rationale = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label='Criticality Rationale',
    )
    gaps_description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label='Gaps Description',
    )
    attribute_description = forms.CharField(
        required=False,
        max_length=512,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Attribute Description',
    )