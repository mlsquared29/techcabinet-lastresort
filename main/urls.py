from django.urls import path
from . import views

app_name = 'main'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<int:id>/', views.question, name='detail'),
    path('ask/', views.ask, name='ask'),
    path('<int:id>/answer/', views.answer, name='answer'),
    path('<int:id>/answer/<int:answer_id>/upvote/', views.upvote, name='upvote'),
    path('<int:id>/answer/<int:answer_id>/downvote/', views.downvote, name='downvote'),
]