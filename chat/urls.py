from django.urls import path
from . import views

urlpatterns = [
    path("chat/", views.chat_view, name="chat"),
    path("chat-sessions/", views.chat_sessions_list, name="chat_sessions_list"),
    path("chat-sessions/<uuid:session_id>/", views.chat_session_detail, name="chat_session_detail"),
    path("chat-history/", views.chat_history_all, name="chat_history_all"),
]
