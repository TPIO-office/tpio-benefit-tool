"""Management command to seed reference data and demo content."""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

from vta.models import (
    Assessment,
    AssessmentNode,
    Link,
    Node,
    NodeType,
    UserProfile,
)


class Command(BaseCommand):
    help = 'Seed the database with reference data and demo content'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing data first')

    def handle(self, *args, **options):
        self.stdout.write('Seeding reference data...')

        # Create groups (roles)
        for group_name in ['Admin', 'Analyst', 'Respondent']:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created group: {group_name}'))

        # Create demo admin user
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@usaon.org',
                password='admin123',
                first_name='Admin',
                last_name='User',
            )
            UserProfile.objects.get_or_create(user=admin_user)
            admin_user.groups.add(Group.objects.get(name='Admin'))
            self.stdout.write(self.style.SUCCESS('Created admin user (password: admin123)'))

        # Create demo analyst user
        if not User.objects.filter(username='analyst').exists():
            analyst_user = User.objects.create_user(
                username='analyst',
                email='analyst@usaon.org',
                password='analyst123',
                first_name='Analyst',
                last_name='User',
            )
            UserProfile.objects.create(
                user=analyst_user,
                affiliation='USAON Research Team',
            )
            analyst_user.groups.add(Group.objects.get(name='Analyst'))
            self.stdout.write(self.style.SUCCESS('Created analyst user (password: analyst123)'))

        # Create demo respondent user
        if not User.objects.filter(username='respondent').exists():
            respondent_user = User.objects.create_user(
                username='respondent',
                email='respondent@usaon.org',
                password='respondent123',
                first_name='Respondent',
                last_name='User',
            )
            UserProfile.objects.get_or_create(user=respondent_user)
            respondent_user.groups.add(Group.objects.get(name='Respondent'))
            self.stdout.write(self.style.SUCCESS('Created respondent user (password: respondent123)'))

        # Create demo nodes if none exist
        if Node.objects.count() == 0:
            analyst_profile = UserProfile.objects.get(user__username='analyst')

            # Observing system node
            Node.objects.create(
                type=NodeType.OBSERVING_SYSTEM,
                title='ICESat-2',
                short_name='ICESat-2',
                description='NASA ice, cloud, and land elevation satellite.',
                created_by=analyst_profile,
                organization='NASA',
                funder='NASA/Earth Science Division',
                funding_country='USA',
                website='https://icesat-2.gsfc.nasa.gov/',
                contact_information='ICESat-2 Team',
            )

            # Data product node
            Node.objects.create(
                type=NodeType.DATA_PRODUCT,
                title='ATL08 Land Ice Height',
                short_name='ATL08',
                description='Land ice height data product from ICESat-2.',
                created_by=analyst_profile,
                organization='NSIDC',
                funder='NASA',
                funding_country='USA',
                website='https://nsidc.org/data/atl08',
                contact_information='NSIDC Help Desk',
            )

            # Application node
            Node.objects.create(
                type=NodeType.APPLICATION,
                title='Sea Level Rise Monitoring',
                short_name='SLRM',
                description='Monitoring ice sheet mass balance for sea level projections.',
                created_by=analyst_profile,
                organization='IPCC Working Group I',
                funder='WMO',
                funding_country='International',
                contact_information='IPCC Secretariat',
                hypothetical=False,
            )

            # Societal benefit area node
            Node.objects.create(
                type=NodeType.SOCIETAL_BENEFIT_AREA,
                title='Climate Change Mitigation',
                short_name='CCM',
                description='Societal benefit of reducing climate change impacts through observation.',
                created_by=analyst_profile,
                framework_name='SDG 13: Climate Action',
                framework_url='https://sdgs.un.org/goals/goal13',
            )

            self.stdout.write(self.style.SUCCESS('Created 4 demo nodes'))

        # Create demo assessment if none exist
        if Assessment.objects.count() == 0:
            analyst_profile = UserProfile.objects.get(user__username='analyst')
            assessment = Assessment.objects.create(
                title='Arctic Ice Monitoring Benefit Assessment',
                description='Evaluate the societal benefits of Arctic ice observing systems.',
                private=False,
                hypothetical=False,
                created_by=analyst_profile,
            )

            # Add all nodes to this assessment
            for node in Node.objects.all():
                AssessmentNode.objects.create(assessment=assessment, node=node)

            self.stdout.write(self.style.SUCCESS('Created demo assessment with all nodes'))

            # Create links between assessment nodes (observing_system -> data_product -> application -> societal_benefit)
            anodes = {n.node.type: n for n in AssessmentNode.objects.filter(assessment=assessment)}
            link_data = [
                (anodes[NodeType.OBSERVING_SYSTEM], anodes[NodeType.DATA_PRODUCT], 80, 8),
                (anodes[NodeType.DATA_PRODUCT], anodes[NodeType.APPLICATION], 70, 7),
                (anodes[NodeType.APPLICATION], anodes[NodeType.SOCIETAL_BENEFIT_AREA], 60, 9),
            ]
            for source, target, perf, crit in link_data:
                Link.objects.create(
                    source_assessment_node=source,
                    target_assessment_node=target,
                    performance_rating=perf,
                    criticality_rating=crit,
                )
            self.stdout.write(self.style.SUCCESS('Created demo links between assessment nodes'))

        self.stdout.write(self.style.SUCCESS('Seeding complete.'))