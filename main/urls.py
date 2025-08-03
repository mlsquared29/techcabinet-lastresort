from django.urls import path
from . import views

app_name = 'main'
urlpatterns = [
    path('', views.process_query, name='process_query'),
    path('output/<int:psa_group_id>/', views.output, name='output'),
    path('check-outputs/<int:psa_group_id>/', views.check_outputs, name='check_outputs'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
]