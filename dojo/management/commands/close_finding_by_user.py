from django.core.management.base import BaseCommand
from datetime import datetime, timedelta

from dojo.models import Finding, User, Notes
from django.utils import timezone

"""
Authors: pdmayoSFI
Sets Active Findings by a specified user that are X number of days old. Can be used to help 
alleviate findings now auto-closing after a set number of days has passed for CI/CD sourced 
findings that are part of an automated reporting cycle.
"""

class Command(BaseCommand):
    help = ''

    def add_arguments(self, parser):
        # # Mandatory positional argument
        parser.add_argument('username')

        # Named (optional) argument
        parser.add_argument(
            '--age',
            dest='age',
            type=int,
            default=7,
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
        target_age = (datetime.now() - timedelta(days=options['age'])).date()
        findings = Finding.objects.filter(active=True, verified=True, duplicate=False).order_by('numerical_severity')
        print "!! Checking for aged findings submitted by %s and older than %s." % (target_user, target_age)
        if options['dry-run']:
            print "-- Initiating Dry-Run Check"
        tracker = 0
        for finding in findings:
            duplicates = [d.date for d in finding.duplicate_finding_set().all()]
            dates = [finding.date] + duplicates
            if max(dates) < target_age and (str(finding.reporter) == target_user):
                tracker += 1
                if not options['dry-run']:
                    # Close Finding and increment tracker counter
                    finding.active = False
                    finding.save()

                    # Create Note to Record Automated Closure
                    now = timezone.now()
                    new_note = Notes()
                    new_note.entry = "Finding automatically closed by Ingestor_API Script due to no updated duplicate " \
                                     "findings within the %s day permitted threshold." % options['age']
                    new_note.author = User.objects.get(username='ingestor_api')
                    new_note.date = now
                    new_note.save()
                    finding.notes.add(new_note)
                    print "%s. Finding #%s \"%s\" closed." % (tracker, finding.id, finding)
                else:
                    print "%s. Finding #%s \"%s\" candidate due to closed." % (tracker, finding.id, finding)
        print "!! Finished checking for aged findings. %s aged findings found." % tracker
