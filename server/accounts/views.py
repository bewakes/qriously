from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UserSerializer
from .services import create_anonymous_session


class DeviceAuthView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        label = (request.data.get("label") or "")[:200]
        user, _session, token = create_anonymous_session(label=label)
        return Response(
            {
                "token": token,
                "user": UserSerializer(user).data,
            },
            status=201,
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"user": UserSerializer(request.user).data})
