from typing import List

from django.core.management.base import BaseCommand

from team.models import Iteration
from team.views import Export


class Command(BaseCommand):
    help = 'Reports iterations export'

    def add_arguments(self, parser):
        parser.add_argument('iteration_ids', nargs='+', type=int)

    def handle(self, iteration_ids: List[int], *args, **options):
        iterations = Iteration.objects.filter(id__in=iteration_ids)
        for iteration in iterations:
            e = Export(iteration)
            content = e.render()
            self.stdout.write(f'Iteration {iteration}\n========\n')
            self.stdout.write(content)
