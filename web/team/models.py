from urllib.parse import urljoin

from django.db import models
from django.utils.translation import gettext_lazy as _

from team.lib import iteration_start, iteration_stop


# ----------- abstract models -----------

class CreatedUpdatedModel(models.Model):
    created = models.DateTimeField(_('created'), auto_now_add=True, blank=True)
    updated = models.DateTimeField(_('updated'), auto_now=True, blank=True)

    class Meta:
        abstract = True


class CommentModel(models.Model):
    comment = models.TextField(_('comment'), default='', null=False, blank=True)

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


class Task(CreatedUpdatedModel, CommentModel):
    tracker = models.ForeignKey(Tracker, on_delete=models.CASCADE)
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

    iteration = models.ForeignKey(Iteration, on_delete=models.CASCADE, related_name='reports')
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    status = models.CharField(_('status'), max_length=32, choices=STATUS_CHOICES, default=PLANNED, db_index=True)

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
