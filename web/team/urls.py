from django.urls import path

from team.views import index

urlpatterns = [
    path('', index, name='index'),
]
