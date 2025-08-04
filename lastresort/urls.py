from django.urls import path
from . import views

app_name = 'lastresort'
urlpatterns = [
    path('', views.landing, name='landing'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('competition/<int:competition_id>/', views.competition, name='competition'),
    path('register-competition/<int:competition_id>/', views.register_competition, name='register_competition'),
    path('submit/<int:competition_id>/', views.submit, name='submit'),
    path('leaderboard/<int:competition_id>/', views.leaderboard, name='leaderboard'),
    path('output/<int:psa_group_id>/<int:competition_id>/', views.output, name='output'),
    path('check-outputs/<int:psa_group_id>/', views.check_outputs, name='check_outputs'),
    path('download-submission/<int:psa_group_id>/', views.download_submission, name='download_submission'),
    path('admin-review/<int:competition_id>/', views.admin_review, name='admin_review'),
]