from itertools import groupby
from random import shuffle
from typing import Iterable, List, Tuple

from django.conf import settings
from django.contrib import messages
from django.db import models, transaction
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, reverse
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import DetailView, ListView, UpdateView

from team.forms import IterationForm, ReportCreateForm, ReportForm
from team.models import Iteration, iteration_dates, Report, Worker


class Export:
    """Export processor"""

    def __init__(self, iteration: Iteration, planned: bool = False):
        """
        :param iteration: iteration for export
        :param planned: move not done reports to planned
        """
        self.iteration = iteration
        self.planned = planned
        self.status_map = dict(Report.STATUS_CHOICES)

    def _show_comment(self, status: str) -> bool:
        if not self.planned:
            return True
        return status != Report.PLANNED

    def get_reports(self) -> List[Tuple[Worker, List[Tuple[str, bool, Tuple[Report]]]]]:
        result = []
        reports = self.iteration.reports.select_related(
            'worker', 'task__tracker'
        ).order_by(
            'worker', 'status', 'task'
        )
        for worker, items in groupby(reports, lambda x: x.worker):
            worker_reports = [
                (self.status_map[status], self._show_comment(status), tuple(task_items))
                for status, task_items in groupby(items, lambda y: y.status)
            ]
            result.append((worker, worker_reports))
        return result

    def get_planned_reports(self) -> List[Tuple[Worker, List[Tuple[str, bool, List[Report]]]]]:
        """It returns in_progress reports duplicated in planned section"""
        result = []
        reports = self.iteration.reports.select_related(
            'worker', 'task__tracker'
        ).order_by(
            'worker', 'status', 'task'
        )
        for worker, items in groupby(reports, lambda x: x.worker):
            worker_reports = {
                status: list(task_items)
                for status, task_items in groupby(items, lambda y: y.status)
            }
            in_progress = worker_reports.get(Report.IN_PROGRESS, [])
            worker_reports.setdefault(Report.PLANNED, []).extend(in_progress)

            reports = [
                (self.status_map[status], self._show_comment(status), items)
                for status, items in sorted(worker_reports.items(), key=lambda x: x[0])
            ]
            result.append((worker, reports))
        return result

    def render(self) -> str:
        reports = self.get_planned_reports() if self.planned else self.get_reports()
        return render_to_string('team/export.txt', {'result': reports, 'planned': self.planned})


class IterationListView(ListView):
    queryset = Iteration.objects.all()
    context_object_name = 'iterations'
    paginate_by = settings.OBJECTS_PER_PAGE
    template_name = 'team/iterations.html'


class IterationSearchListView(IterationListView):

    def get_context_data(self, *, object_list=None, **kwargs):
        context_data = super().get_context_data(object_list=object_list, **kwargs)
        context_data['search'] = self.request.GET.get('search')
        return context_data

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        if search is not None:
            reports = Report.objects.filter(
                models.Q(comment__icontains=search) |
                models.Q(task__number__icontains=search) |
                models.Q(task__title__icontains=search) |
                models.Q(iteration__comment__icontains=search)
            )
            reports = reports.filter(iteration__in=queryset)
            iteration_ids = set(reports.values_list('iteration_id', flat=True))
            if iteration_ids:
                queryset = queryset.filter(id__in=iteration_ids)
            else:
                queryset = Iteration.objects.none()
        return queryset


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
    def _prepare_data(cls, i: Iteration) -> List[Tuple[Worker, List[Report]]]:
        result = []
        i.form = IterationForm(instance=i)
        reports = i.reports.select_related('worker', 'task__tracker').order_by('worker', 'status', 'task')
        for worker, items in groupby(reports, lambda x: x.worker):
            worker.form = ReportCreateForm(iteration=i)
            result.append((worker, cls._set_reports_form(items)))
        return result

    @staticmethod
    def workers_order(worker_reports: List[Tuple[Worker, List[Report]]]) -> List[Worker]:
        workers = [worker for worker, _ in worker_reports]
        shuffle(workers)
        return workers

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.object:
            data['worker_reports'] = self._prepare_data(self.object)
            data['workers'] = self.workers_order(data['worker_reports'])
        return data


class PostUpdateView(UpdateView):

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed('failed request')


class IterationUpdateView(PostUpdateView):
    model = Iteration
    form_class = IterationForm

    def get_success_url(self):
        return reverse('iteration', kwargs={'pk': self.object.pk})


class ReportUpdateView(PostUpdateView):
    model = Report
    form_class = ReportForm

    def get_success_url(self):
        return self.object.anchor_url


def index(request):
    iteration = Iteration.objects.first()
    return IterationDetailView.as_view()(request, pk=iteration.pk)


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
        url = report.anchor_url
    else:
        msgs = [e for errors in form.errors.values() for e in errors]
        msg = _('report can not be created: {}')
        messages.error(request, msg.format(', '.join(msgs)))
        url = reverse('iteration', kwargs={'pk': iteration.pk})
    return redirect(url)


@require_POST
@transaction.atomic()
def report_delete(request, pk: int):
    report = get_object_or_404(Report, pk=pk)
    url = report.anchor_url
    msg = _('report #{} was successfully deleted')
    report.delete()
    messages.success(request, msg.format(pk))
    return redirect(url)


@require_POST
@transaction.atomic()
def iteration_create(request, pk: int):
    base_iteration = get_object_or_404(Iteration, pk=pk)
    if not base_iteration.is_last:
        messages.error(request, _('this iteration is not the latest'))
        return redirect('iteration', pk)

    start, stop = iteration_dates(base_iteration.start)

    iteration = Iteration.objects.create(start=start, stop=stop)
    base_reports = base_iteration.reports.filter(
        status__in=(Report.PLANNED, Report.IN_PROGRESS),
    )
    # reports migration to planned status
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


@require_GET
def iteration_export(request, pk: int):
    iteration = get_object_or_404(Iteration, pk=pk)
    exporter = Export(iteration)
    response = HttpResponse(exporter.render(), content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="iteration_{}_{}.txt"'.format(
        iteration.start.strftime('%Y%m%d'),
        iteration.stop.strftime('%Y%m%d'),
    )
    return response


@require_GET
def iteration_export_planned(request, pk: int):
    iteration = get_object_or_404(Iteration, pk=pk)
    exporter = Export(iteration, planned=True)
    response = HttpResponse(exporter.render(), content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="iteration_planned_{}_{}.txt"'.format(
        iteration.start.strftime('%Y%m%d'),
        iteration.stop.strftime('%Y%m%d'),
    )
    return response
