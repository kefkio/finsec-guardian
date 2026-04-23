from rest_framework import generics, status
from rest_framework.response import Response
from .serializers_auth import RegisterSerializer

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)
