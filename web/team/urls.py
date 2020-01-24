from django.urls import path

from team.views import (
    IterationDetailView,
    IterationListView,
    IterationUpdateView,
    ReportUpdateView,
    index,
    iteration_create,
    report_create,
)

urlpatterns = [
    path('', index, name='index'),
    path('iterations/', IterationListView.as_view(), name='iterations'),
    path('iterations/<int:pk>/', IterationDetailView.as_view(), name='iteration'),
    path('iterations/<int:pk>/create/', iteration_create, name='iteration_create'),
    path('iterations/<int:pk>/update/', IterationUpdateView.as_view(), name='iteration_update'),
    path('reports/<int:pk>/update/', ReportUpdateView.as_view(), name='report_update'),
    path('reports/create/<int:iteration_id>/<int:worker_id>/', report_create, name='report_create'),
    # iteration/export/ID/FORMAT
]
