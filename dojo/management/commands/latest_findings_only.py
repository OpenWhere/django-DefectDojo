from django.core.management.base import BaseCommand
from datetime import datetime, timedelta

from dojo.models import Finding, User, Notes, Engagement, Product, Test
from django.utils import timezone
from django.shortcuts import get_object_or_404

"""
Authors: pdmayoSFI
Closes or opens findings based on the latest CI/CD engagement results
"""

class Command(BaseCommand):
    help = ''

    def add_arguments(self, parser):
        # Mandatory positional argument
        parser.add_argument('username')

        # Named (optional) argument
        parser.add_argument(
            '--age',
            dest='age',
            type=int,
            default=14,
            help='Maximum allowed age to close a finding (Default 7)',
        )

        # Named (optional) argument
        parser.add_argument(
            '--dry-run',
            dest='dry-run',
            action='store_true',
            help='Complete a dry-run to report applicable findings but not set active to False.'
        )


    def handle(self, *args, **options):
        target_user = options['username']
        for product in Product.objects.all():
            findings = Finding.objects.filter(test__engagement__product=product, active=True)
            findings = [finding.id for finding in findings]
            product_findings = []

            # Get all current findings for product, traversing duplicates to the first instance
            for finding_id in findings:
                finding = get_object_or_404(Finding, id=finding_id)
                if finding.duplicate:
                    finding = get_object_or_404(Finding, id=finding.duplicate_finding_id)
                product_findings.append(finding.id)

            # Close findings for product if last engagement is more than X days old
            eng = Engagement.objects.filter(product=product, engagement_type='CI/CD').order_by('-target_end')[0]
            target_age = (datetime.now() - timedelta(days=options['age'])).date()
            if eng.target_end < target_age:
                for finding_id in product_findings:
                    finding = get_object_or_404(Finding, id=finding_id)
                    if finding.duplicate:
                        finding = get_object_or_404(Finding, id=finding.duplicate_finding_id)
                    if not options['dry-run']:
                        finding.active = False
                        finding.save()
                        new_note = Notes()
                        new_note.entry = "Product engagement older than %s days. Automatically closing \
                                          associated findings by Ingestor_API script." % options['age']
                        new_note.author = User.objects.get(username=target_user)
                        new_note.date = timezone.now()
                        new_note.save()
                        finding.notes.add(new_note)
                    print('Finding %s [%s] "%s" closed due to last engagement being more than %s days ago.' %
                          (finding.id, finding.severity, finding, options['age']))
                # Continue to next product if it has no engagements within X days
                continue

            # Get the lastest test findings for latest engagement and set active if not FP
            tests = Test.objects.filter(engagement=eng).order_by('test_type__name', '-updated')
            eng_findings = []
            for test in tests:
                findings = Finding.objects.filter(test=test).order_by('numerical_severity')
                for finding in findings:
                    if finding.duplicate:
                        finding = get_object_or_404(Finding, id=finding.duplicate_finding_id)
                    if finding not in eng_findings:
                        eng_findings.append(finding)
            for finding in eng_findings:
                if not finding.active and not finding.false_p:
                    if not options['dry-run']:
                        finding.active = True
                        finding.save()
                        new_note = Notes()
                        new_note.entry = "Finding identified on current engagement and automatically " \
                                         "opened by Ingestor_API script."
                        new_note.author = User.objects.get(username=target_user)
                        new_note.date = timezone.now()
                        new_note.save()
                        finding.notes.add(new_note)
                    print('Finding %s [%s] "%s" opened due to being listed in last engagement.' %
                          (finding.id, finding.severity, finding))

            # Close findings open in the product but not found in engagement tests
            findings = Finding.objects.filter(test__engagement__product=product, active=True)
            findings = [finding.id for finding in findings]
            prod_findings = []
            for finding_id in findings:
                finding = get_object_or_404(Finding, id=finding_id)
                if finding.duplicate:
                    finding = get_object_or_404(Finding, id=finding.duplicate_finding_id)
                prod_findings.append(finding)
            close_in_prod = [finding for finding in prod_findings if finding not in eng_findings]

            for finding in close_in_prod:
                if not options['dry-run']:
                    finding.active = False
                    finding.save()
                    new_note = Notes()
                    new_note.entry = "Finding not identiified on current engagement and automatically " \
                                     "closed by Ingestor_API script."
                    new_note.author = User.objects.get(username=target_user)
                    new_note.date = timezone.now()
                    new_note.save()
                    finding.notes.add(new_note)
                print('Finding %s [%s] "%s" closed due to not being listed in last engagement.' %
                      (finding.id, finding.severity, finding))
