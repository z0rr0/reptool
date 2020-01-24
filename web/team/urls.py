from django.urls import path

from team.views import index, IterationListView, IterationDetailView, ReportUpdateView

urlpatterns = [
    path('', index, name='index'),
    path('iterations/', IterationListView.as_view(), name='iterations'),
    path('iterations/<int:pk>/', IterationDetailView.as_view(), name='iteration'),
    path('reports/<int:pk>/update/', ReportUpdateView.as_view(), name='report_update'),
    # iteration/create/ID
    # iteration/export/ID/FORMAT
    # report/edit/ID
    # report/create
]
