import os
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render
from .models import ChatSession, Message
from .serializers import (
    ChatSessionSerializer,
    ChatSessionDetailSerializer,
    MessageSerializer,
)

from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def home(request):
    return render(request, "index.html")
@api_view(["POST"])
def chat_view(request):
    data = request.data
    user_message = data.get("message")
    session_id = data.get("session_id")

    if not user_message:
        return Response({"error": "message is required"}, status=status.HTTP_400_BAD_REQUEST)

    if session_id:
        session = get_object_or_404(ChatSession, id=session_id)
        is_new = False
    else:
        session = ChatSession.objects.create(title=user_message[:40])
        is_new = True

    Message.objects.create(session=session, role="user", content=user_message)

    history_text = []
    for msg in session.messages.all():
        role = "User" if msg.role == "user" else "Assistant"
        history_text.append(f"{role}: {msg.content}")
    prompt = "\n".join(history_text) + "\nAssistant:"

    if not client:
        assistant_reply = "Gemini API key is not configured."
    else:
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            assistant_reply = response.text
        except Exception as e:
            return Response(
                {"error": "Gemini API error", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    Message.objects.create(session=session, role="assistant", content=assistant_reply)

    session_serializer = ChatSessionDetailSerializer(session)
    return Response(
        {
            "session_id": str(session.id),
            "is_new_session": is_new,
            "session": session_serializer.data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
def chat_sessions_list(request):
    sessions = ChatSession.objects.order_by("-updated_at")
    serializer = ChatSessionSerializer(sessions, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def chat_session_detail(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id)
    serializer = ChatSessionDetailSerializer(session)
    return Response(serializer.data)


@api_view(["GET"])
def chat_history_all(request):
    messages = Message.objects.select_related("session").order_by("created_at")
    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)
