# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatConversationViewSet, ChatMessageViewSet

router = DefaultRouter()
router.register(r'conversations', ChatConversationViewSet,
                basename='conversation')
router.register(r'messages', ChatMessageViewSet, basename='message')

urlpatterns = [
    path('chat/', include(router.urls)),
]
