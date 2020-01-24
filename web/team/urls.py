from django.urls import path

from team.views import index, iteration_create, IterationDetailView, IterationListView, report_create, ReportUpdateView

urlpatterns = [
    path('', index, name='index'),
    path('iterations/', IterationListView.as_view(), name='iterations'),
    path('iterations/<int:pk>/', IterationDetailView.as_view(), name='iteration'),
    path('iterations/<int:pk>/create/', iteration_create, name='iteration_create'),
    path('reports/<int:pk>/update/', ReportUpdateView.as_view(), name='report_update'),
    path('reports/create/<int:iteration_id>/<int:worker_id>/', report_create, name='report_create'),
    # iteration/export/ID/FORMAT
]
