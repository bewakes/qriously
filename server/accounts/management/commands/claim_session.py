from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction

from accounts.models import User
from learning.models import Thread


class Command(BaseCommand):
    help = (
        "Attach threads owned by anonymous sessions to a registered account, "
        "preserving notebooks and session history. Offline counterpart to the "
        "in-place claim a login performs; useful when several anonymous sessions "
        "hold history for one person. Nodes, spans and notes follow their thread."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--email", required=True, help="Target account email.")
        parser.add_argument(
            "--from",
            dest="source",
            default=None,
            help="Move threads from this one anonymous user id.",
        )
        parser.add_argument(
            "--all-anonymous",
            action="store_true",
            help="Move threads from every anonymous session.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would move without changing anything.",
        )

    @transaction.atomic
    def handle(self, *args: object, **options: object) -> None:
        if not options["source"] and not options["all_anonymous"]:
            raise CommandError("Pass --from <id> or --all-anonymous.")

        email = options["email"].strip().lower()
        try:
            target = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise CommandError(f"No account with email {email!r}.") from None
        if target.is_anonymous_device:
            raise CommandError("Target account is still anonymous; log in first.")

        sources = User.objects.filter(is_anonymous_device=True).exclude(id=target.id)
        if options["source"]:
            sources = sources.filter(id=options["source"])
            if not sources.exists():
                raise CommandError("No matching anonymous session.")

        total = 0
        for src in sources:
            threads = Thread.objects.filter(user=src)
            count = threads.count()
            if not count:
                continue
            self.stdout.write(f"  {str(src.id)[:8]}  {count} session(s)")
            if not options["dry_run"]:
                threads.update(user=target)
            total += count

        verb = "Would attach" if options["dry_run"] else "Attached"
        self.stdout.write(
            self.style.SUCCESS(f"{verb} {total} session(s) to {email}.")
        )
