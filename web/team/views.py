from itertools import groupby
from typing import Iterable, List, Tuple

from django.conf import settings
from django.forms import models as model_forms
from django.shortcuts import render
from django.views.generic import DetailView, ListView, UpdateView

from team.models import Iteration, Report, Worker


class IterationListView(ListView):
    queryset = Iteration.objects.all()
    context_object_name = 'iterations'
    paginate_by = settings.OBJECTS_PER_PAGE
    template_name = 'team/iterations.html'


class IterationDetailView(DetailView):
    queryset = Iteration.objects.all()
    context_object_name = 'iteration'
    template_name = 'team/iteration.html'

    @staticmethod
    def _set_reports_form(reports: Iterable[Report]) -> List[Report]:
        result = []
        f = model_forms.modelform_factory(Report, fields=['status'])
        for r in reports:
            r.form = f(instance=r)
            result.append(r)
        return result

    @classmethod
    def _prepare_data(cls, i: Iteration) -> List[Tuple[Worker, List[Tuple[str, List[Report]]]]]:
        result = []
        reports = i.reports.select_related('worker', 'task__tracker').order_by('worker', 'status', 'task')
        for worker, items in groupby(reports, lambda x: x.worker):
            worker_reports = [
                (status, cls._set_reports_form(task_items))
                for status, task_items in groupby(items, lambda y: y.get_status_display())
            ]
            result.append((worker, worker_reports))
        return result

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.object:
            data['worker_reports'] = self._prepare_data(self.object)
        return data


class ReportUpdateView(UpdateView):
    model = Report
    fields = ['status']


def index(request):
    return render(request, 'team/iteration.html')
