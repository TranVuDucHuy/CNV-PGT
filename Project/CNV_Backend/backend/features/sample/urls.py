from django.urls import path
from . import views

urlpatterns = [
    path('samples', views.create_sample, name='create_sample'),
    path('samples/', views.list_samples, name='list_samples'),
    path('samples/<str:sample_id>/delete', views.delete_sample, name='delete_sample'),
    path('samples/<str:sample_id>/file', views.download_sample_file, name='download_sample_file'),
    path('samples/<str:sample_id>', views.read_sample, name='read_sample'),
]

