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

        # Create Arctic Report Card assessment if it doesn't exist
        if not Assessment.objects.filter(title='Physical Indicators: 20th Anniversary Arctic Report Card').exists():
            analyst_profile = UserProfile.objects.get(user__username='analyst')
            arc_assessment = Assessment.objects.create(
                title='Physical Indicators: 20th Anniversary Arctic Report Card',
                description='Evaluate the societal benefits of Arctic observing systems for the 20th Anniversary Arctic Report Card.',
                private=False,
                hypothetical=False,
                created_by=analyst_profile,
            )

            # Create 7 observing system nodes
            observing_systems = [
                'Surface Air Temp',
                'Lake Ice',
                'Sea Ice',
                'Precipitation',
                'Terrestrial Snow Cover',
                'Sea Surface Temp',
                'Greenland Ice Sheet',
            ]
            for title in observing_systems:
                Node.objects.get_or_create(
                    title=title,
                    defaults={
                        'type': NodeType.OBSERVING_SYSTEM,
                        'short_name': title.split()[0],
                        'description': f'{title} observation system for Arctic monitoring.',
                        'created_by': analyst_profile,
                    }
                )

            # Create 5 societal benefit area nodes
            societal_benefit_areas = [
                'Fundamental Understanding',
                'Terrestrial Freshwater',
                'Marine Coastal',
                'Environmental Quality',
                'Weather and Climate',
            ]
            for title in societal_benefit_areas:
                Node.objects.get_or_create(
                    title=title,
                    defaults={
                        'type': NodeType.SOCIETAL_BENEFIT_AREA,
                        'short_name': title.split()[0],
                        'description': f'{title} - societal benefit area for Arctic observations.',
                        'created_by': analyst_profile,
                        'framework_name': None,
                        'framework_url': None,
                    }
                )

            # Add all 12 nodes as AssessmentNodes
            for node in Node.objects.filter(title__in=observing_systems + societal_benefit_areas):
                AssessmentNode.objects.get_or_create(
                    assessment=arc_assessment,
                    node=node,
                )

            # Create 30 links between observing systems and SBAs with varied ratings
            link_data = [
                # Strong links with high ratings
                ('Sea Ice', 'Marine Coastal', 90, 10),
                ('Surface Air Temp', 'Weather and Climate', 95, 10),
                ('Greenland Ice Sheet', 'Weather and Climate', 85, 9),
                ('Lake Ice', 'Terrestrial Freshwater', 70, 7),
                ('Precipitation', 'Weather and Climate', 80, 8),
                ('Terrestrial Snow Cover', 'Terrestrial Freshwater', 65, 6),
                ('Sea Surface Temp', 'Marine Coastal', 75, 8),
                # Additional strong links
                ('Surface Air Temp', 'Fundamental Understanding', 92, 9),
                ('Sea Ice', 'Fundamental Understanding', 88, 8),
                ('Greenland Ice Sheet', 'Environmental Quality', 78, 7),
                # Medium performance links
                ('Lake Ice', 'Environmental Quality', 60, 5),
                ('Precipitation', 'Terrestrial Freshwater', 72, 6),
                ('Sea Surface Temp', 'Environmental Quality', 68, 6),
                ('Terrestrial Snow Cover', 'Weather and Climate', 74, 7),
                ('Precipitation', 'Marine Coastal', 55, 5),
                # Lower performance links
                ('Lake Ice', 'Fundamental Understanding', 50, 4),
                ('Sea Surface Temp', 'Fundamental Understanding', 45, 4),
                ('Terrestrial Snow Cover', 'Fundamental Understanding', 58, 5),
                # Links with null performance_rating (grey rendering)
                ('Lake Ice', 'Marine Coastal', None, 6),
                ('Precipitation', 'Environmental Quality', None, 5),
                ('Sea Surface Temp', 'Weather and Climate', None, 7),
                ('Terrestrial Snow Cover', 'Marine Coastal', None, 4),
                # Links with null criticality_rating (minimum thickness)
                ('Surface Air Temp', 'Environmental Quality', 82, None),
                ('Sea Ice', 'Environmental Quality', 76, None),
                ('Lake Ice', 'Weather and Climate', 63, None),
                ('Precipitation', 'Fundamental Understanding', 48, None),
                # Remaining links to reach 30
                ('Surface Air Temp', 'Terrestrial Freshwater', 70, 6),
                ('Sea Ice', 'Terrestrial Freshwater', 62, 5),
                ('Greenland Ice Sheet', 'Fundamental Understanding', 82, 8),
                ('Greenland Ice Sheet', 'Terrestrial Freshwater', 72, 7),
            ]

            for source_title, target_title, perf, crit in link_data:
                source_an = AssessmentNode.objects.filter(
                    assessment=arc_assessment,
                    node__title=source_title
                ).first()
                target_an = AssessmentNode.objects.filter(
                    assessment=arc_assessment,
                    node__title=target_title
                ).first()
                if source_an and target_an:
                    Link.objects.get_or_create(
                        source_assessment_node=source_an,
                        target_assessment_node=target_an,
                        defaults={
                            'performance_rating': perf,
                            'criticality_rating': crit,
                        }
                    )

            self.stdout.write(self.style.SUCCESS('Created Arctic Report Card assessment with 12 nodes and 30 links'))

        self.stdout.write(self.style.SUCCESS('Seeding complete.'))