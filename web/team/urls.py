from django.urls import path

from team.views import (
    index,
    iteration_create,
    iteration_export,
    iteration_export_planned,
    IterationDetailView,
    IterationListView,
    IterationSearchListView,
    IterationUpdateView,
    report_create,
    report_delete,
    ReportUpdateView,
)

urlpatterns = [
    path('', index, name='index'),
    path('iterations/', IterationListView.as_view(), name='iterations'),
    path('iterations/search/', IterationSearchListView.as_view(), name='iteration_search'),
    path('iterations/<int:pk>/', IterationDetailView.as_view(), name='iteration'),
    path('iterations/<int:pk>/create/', iteration_create, name='iteration_create'),
    path('iterations/<int:pk>/update/', IterationUpdateView.as_view(), name='iteration_update'),
    path('iterations/<int:pk>/export/', iteration_export, name='iteration_export'),
    path('iterations/<int:pk>/export/planned/', iteration_export_planned, name='iteration_export_planned'),
    path('reports/<int:pk>/update/', ReportUpdateView.as_view(), name='report_update'),
    path('reports/<int:pk>/delete/', report_delete, name='report_delete'),
    path('reports/create/<int:iteration_id>/<int:worker_id>/', report_create, name='report_create'),
]
