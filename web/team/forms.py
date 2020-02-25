from django.forms import CharField, ModelForm, Select, TextInput, ValidationError
from django.utils.translation import gettext_lazy as _

from team.models import Iteration, Report, Task, Tracker


class ReportForm(ModelForm):
    class Meta:
        model = Report
        fields = ['status', 'comment', 'delegation']
        widgets = {
            'status': Select(attrs={
                'class': 'form-control my-1 mr-sm-2'
            }),
            'comment': TextInput(attrs={
                'class': 'form-control mb-2 mr-sm-2',
                'placeholder': _('Comment'),
            }),
            'delegation': Select(attrs={
                'class': 'form-control my-1 mr-sm-2'
            }),
        }


class ReportCreateForm(ModelForm):
    number = CharField(
        label=_('Task number'),
        max_length=255,
        widget=TextInput(attrs={
            'class': 'form-control mb-2 mr-sm-2',
            'placeholder': _('Task URL'),
        })
    )
    title = CharField(
        label=_('Task title'),
        max_length=4096,
        widget=TextInput(attrs={
            'class': 'form-control mb-2 mr-sm-2',
            'placeholder': _('Task title'),
        })
    )

    class Meta:
        model = Report
        fields = ['comment', 'delegation', 'status']
        widgets = {
            'comment': TextInput(attrs={
                'class': 'form-control mb-2 mr-sm-2',
                'placeholder': _('Comment'),
            }),
            'delegation': Select(attrs={
                'class': 'form-control my-1 mr-sm-2'
            }),
            'status': Select(attrs={
                'class': 'form-control my-1 mr-sm-2'
            }),
        }

    def __init__(self, iteration: Iteration, *args, **kwargs):
        self.iteration = iteration
        super().__init__(*args, **kwargs)

    def clean(self):
        data = super().clean()
        if data:
            if data.get('number') and data.get('title'):
                task_values = data['number'].rsplit('/', 1)
                if len(task_values) != 2:
                    raise ValidationError(_('failed task URL'))
                try:
                    tracker = Tracker.objects.get(url__startswith=task_values[0])
                except (Tracker.DoesNotExist, Tracker.MultipleObjectsReturned):
                    raise ValidationError(_('can not find tracker'))

                task, created = Task.objects.get_or_create(
                    number=task_values[1],
                    defaults={
                        'title': data['title'],
                        'tracker': tracker,
                    },
                )
                if not created:
                    if self.iteration.reports.filter(task=task).exists():
                        raise ValidationError(_('task is already exists in this iteration'))
                data['task'] = task
        return data


class IterationForm(ModelForm):
    class Meta:
        model = Iteration
        fields = ['comment']
        widgets = {
            'comment': TextInput(attrs={
                'class': 'form-control mb-2 mr-sm-2',
                'placeholder': _('Comment'),
            })
        }
