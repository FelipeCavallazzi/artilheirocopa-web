from django.urls import path
from . import views

urlpatterns = [
    path("",          views.index,    name="index"),
    path("start/",    views.start,    name="start"),
    path("question/", views.question, name="question"),
    path("answer/",   views.answer,   name="answer"),
    path("result/",   views.result,   name="result"),
    path("gameover/", views.gameover, name="gameover"),
]