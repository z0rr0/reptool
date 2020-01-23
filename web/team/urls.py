from django.urls import path

from team.views import index

urlpatterns = [
    path('', index, name='index'),
    # iterations
    # iteration/ID
    # iteration/create/ID
    # iteration/export/ID/FORMAT
    # report/edit/ID
    # report/create
]
