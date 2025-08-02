from django.urls import path
from . import views

app_name = 'main'
urlpatterns = [
    path('', views.process_query, name='process_query'),
    path('output/<int:query_id>/', views.output, name='output'),
    path('check-outputs/<int:query_id>/', views.check_outputs, name='check_outputs'),
]