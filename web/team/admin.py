from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from team.models import Iteration, Report, Task, Tracker, Worker


class TrackerAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'created']
    search_fields = ('name',)


class WorkerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'created']
    search_fields = ('name', 'email')


class TaskAdmin(admin.ModelAdmin):
    list_display = ['number', 'title', 'url', 'comment']
    search_fields = ('number', 'title')
    list_select_related = ['tracker']
    list_filter = ['created']


class IterationAdmin(admin.ModelAdmin):
    list_display = ['start', 'stop', 'comment']
    list_filter = ['start']


def make_done(modeladmin, request, queryset):
    queryset.exclude(status=Report.DONE).update(status=Report.DONE)


make_done.short_description = _('Mark selected as done')


class ReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'iteration', 'worker', 'task', 'status', 'updated', 'created']
    search_fields = ('task__number', 'task__title', 'worker__name')
    list_filter = ['iteration__start', 'created', 'status']
    actions = [make_done]
    list_select_related = ['iteration', 'worker', 'task']
    list_per_page = 30


admin.site.register(Tracker, TrackerAdmin)
admin.site.register(Worker, WorkerAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(Report, ReportAdmin)
admin.site.register(Iteration, IterationAdmin)
