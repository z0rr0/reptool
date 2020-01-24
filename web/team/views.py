from itertools import groupby
from typing import Iterable, List, Tuple

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, reverse
from django.views.decorators.http import require_POST
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from team.forms import ReportCreateForm, ReportForm
from team.lib import iteration_dates
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
        for r in reports:
            r.form = ReportForm(instance=r)
            result.append(r)
        return result

    @classmethod
    def _prepare_data(cls, i: Iteration) -> List[Tuple[Worker, List[Tuple[str, List[Report]]]]]:
        result = []
        reports = i.reports.select_related('worker', 'task__tracker').order_by('worker', 'status', 'task')
        for worker, items in groupby(reports, lambda x: x.worker):
            worker.form = ReportCreateForm(iteration=i)
            worker_reports = [
                (status, cls._set_reports_form(task_items))
                for status, task_items in groupby(items, lambda y: y.get_status_display())
            ]
            result.append((worker, worker_reports))
        return result

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.object:
            last = self.queryset.only('pk').first()
            data['last_iteration'] = last.pk
            data['worker_reports'] = self._prepare_data(self.object)
        return data


class ReportUpdateView(UpdateView):
    model = Report
    form_class = ReportForm

    def get_success_url(self):
        return reverse('iteration', kwargs={'pk': self.object.iteration_id})


class ReportCreateView(CreateView):
    model = Report
    form_class = ReportForm


def index(request):
    i = Iteration.objects.first()
    return IterationDetailView.as_view()(request, pk=i.pk)


@require_POST
@transaction.atomic()
def report_create(request, iteration_id: int, worker_id: int):
    iteration = get_object_or_404(Iteration, pk=iteration_id)
    worker = get_object_or_404(Worker, pk=worker_id)

    form = ReportCreateForm(iteration=iteration, data=request.POST or None)
    if form.is_valid():
        report = form.save(commit=False)
        report.task = form.cleaned_data['task']
        report.iteration = iteration
        report.worker = worker
        report.save()
        msg = _('report #{} was successfully created')
        messages.success(request, msg.format(report.id))
    else:
        msgs = [e for errors in form.errors.values() for e in errors]
        msg = _('report can not be created: {}')
        messages.error(request, msg.format(', '.join(msgs)))
    return redirect('iteration', iteration_id)


@require_POST
@transaction.atomic()
def iteration_create(request, pk: int):
    base_iteration = get_object_or_404(Iteration, pk=pk)
    start, stop = iteration_dates(base_iteration.start)
    iteration = Iteration.objects.create(
        start=start,
        stop=stop,
    )
    base_reports = base_iteration.reports.filter(
        status__in=(Report.PLANNED, Report.IN_PROGRESS),
    )
    reports = [
        Report(
            iteration=iteration,
            worker_id=r.worker_id,
            task_id=r.task_id,
            status=Report.PLANNED,
        )
        for r in base_reports
    ]
    items = Report.objects.bulk_create(reports, batch_size=100)
    msg = _('iteration #{} was created with {} new reports')
    messages.success(request, msg.format(iteration.id, len(items)))
    return redirect('index')
