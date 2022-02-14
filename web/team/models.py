from datetime import date, timedelta
from typing import Optional, Tuple
from urllib.parse import urljoin

from django.db import models
from django.shortcuts import reverse
from django.utils.translation import gettext_lazy as _


def iteration_dates(dt: Optional[date] = None) -> Tuple[date, date]:
    """
    Iteration start and stop dates.
    By default returns next iteration ones.

    >>> iteration_dates(date(2020, 1, 20))
    (datetime.date(2020, 1, 21), datetime.date(2020, 1, 27))
    >>> iteration_dates(date(2020, 1, 21))
    (datetime.date(2020, 1, 28), datetime.date(2020, 2, 3))
    >>> iteration_dates(date(2020, 1, 24))
    (datetime.date(2020, 1, 28), datetime.date(2020, 2, 3))
    """
    dt = dt or date.today()
    _, offset = divmod(6 - dt.weekday() + 2, 7)
    start = dt + timedelta(days=offset or 7)
    return start, start + timedelta(days=6)


def iteration_start(dt: Optional[date] = None) -> date:
    start, _ = iteration_dates(dt)
    return start


def iteration_stop(dt: Optional[date] = None) -> date:
    _, stop = iteration_dates(dt)
    return stop


# ----------- abstract models -----------

class CreatedUpdatedModel(models.Model):
    created = models.DateTimeField(_('created'), auto_now_add=True, blank=True)
    updated = models.DateTimeField(_('updated'), auto_now=True, blank=True)

    class Meta:
        abstract = True


class CommentModel(models.Model):
    comment = models.TextField(_('comment'), default='', blank=True)

    class Meta:
        abstract = True


class NameModel(models.Model):
    name = models.CharField(_('name'), max_length=255, unique=True)

    class Meta:
        abstract = True
        ordering = ('name',)

    def __str__(self) -> str:
        return self.name


# ----------- real models -----------

class Tracker(CreatedUpdatedModel, NameModel):
    url = models.URLField(_('url'), db_index=True)


class Worker(CreatedUpdatedModel, NameModel):
    email = models.EmailField(_('email'))
    dashboard = models.URLField(_('dashboard'), default='')
    no_export = models.BooleanField(_('no export'), default=False)

    @property
    def has_dashboard(self) -> bool:
        return self.dashboard != ''


class Task(CreatedUpdatedModel, CommentModel):
    tracker = models.ForeignKey(Tracker, verbose_name=_('tracker'), on_delete=models.CASCADE)
    number = models.CharField(_('number'), max_length=255, unique=True)
    title = models.CharField(_('title'), max_length=4096, db_index=True)

    class Meta:
        ordering = ('number',)

    def __str__(self) -> str:
        return self.number

    @property
    def url(self) -> str:
        return urljoin(self.tracker.url, self.number)

    @property
    def full_name(self) -> str:
        return f'{self.number} {self.title}'


class Iteration(CreatedUpdatedModel, CommentModel):
    start = models.DateField(_('start'), default=iteration_start)
    stop = models.DateField(_('stop'), default=iteration_stop)

    class Meta:
        ordering = ('-start',)
        index_together = ('start', 'stop')

    def __str__(self) -> str:
        return '{start} / {stop}'.format(
            start=self.start.strftime('%Y-%m-%d'),
            stop=self.stop.strftime('%Y-%m-%d'),
        )

    @property
    def is_last(self):
        return not self._meta.model.objects.filter(start__gt=self.start).exists()


class Report(CreatedUpdatedModel, CommentModel):
    PLANNED = 'planned'
    IN_PROGRESS = 'in_progress'
    DONE = 'done'
    STATUS_CHOICES = (
        (PLANNED, _('Planned')),
        (IN_PROGRESS, _('In progress')),
        (DONE, _('Done')),
    )
    # delegation poker status
    DELEGATION_CHOICES = (
        ('tell', _('Tell')),  # I will tell them
        ('sell', _('Sell')),  # I will try and sell to them
        ('consult', _('Consult')),  # I will consult and then decide
        ('agree', _('Agree')),  # We will agree together
        ('advise', _('Advise')),  # We will advice but they decide
        ('inquire', _('Inquire')),  # I will inquire after they decide
        ('delegate', _('Delegate')),  # I will fully delegate
    )

    iteration = models.ForeignKey(
        Iteration, verbose_name=_('iteration'),
        on_delete=models.CASCADE, related_name='reports',
    )
    worker = models.ForeignKey(Worker, verbose_name=_('worker'), on_delete=models.CASCADE)
    task = models.ForeignKey(Task, verbose_name=_('task'), on_delete=models.CASCADE)
    status = models.CharField(_('status'), max_length=32, choices=STATUS_CHOICES, default=PLANNED, db_index=True)
    delegation = models.CharField(
        _('delegation'), max_length=32, choices=DELEGATION_CHOICES,
        default=DELEGATION_CHOICES[3][0],  # agree
    )

    class Meta:
        ordering = ('iteration', 'worker', 'status')
        unique_together = ('iteration', 'task')

    def __str__(self) -> str:
        return '{iteration} / {task} / {worker} / {status}'.format(
            iteration=self.iteration,
            task=self.task,
            worker=self.worker,
            status=self.status,
        )

    @property
    def is_done(self):
        return self.status == self.DONE

    @property
    def is_in_progress(self):
        return self.status == self.IN_PROGRESS

    @property
    def is_planned(self):
        return self.status == self.PLANNED

    @property
    def anchor_url(self) -> str:
        url = reverse('iteration', kwargs={'pk': self.iteration_id})
        return f'{url}#worker_{self.worker_id}'
