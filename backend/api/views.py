from rest_framework import viewsets, status
from .serializers import (RecipeSerializer, IngredientSerializer,
                          UserSerializer, UserRegisterSerializer,
                          PasswordSetSerializer, FollowSerializer,
                          RecipeCreateSerializer, CuttedRecipesSerializer)
from recipes.models import Recipe, Ingredient, Favorite
from users.models import User, Follow
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from django.urls import reverse


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateSerializer
        return RecipeSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        if user.is_authenticated:
            context['favorited_ids'] = set(
                Favorite.objects.filter(user=user)
                .values_list('recipe_id', flat=True)
            )
        else:
            context['favorited_ids'] = set()
        return context

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        short_id = format(recipe.id, 'x')
        short_path = reverse('api:short-link', kwargs={'short_id': short_id})
        full_url = request.build_absolute_uri(short_path)

        return Response({'short-link': full_url}, status=status.HTTP_200_OK)

    def _handle_add_relation(self, request, model):
        recipe = self.get_object()
        user = request.user

        if model.objects.filter(user=user, recipe=recipe).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        model.objects.create(user=user, recipe=recipe)

        return Response(
            CuttedRecipesSerializer(recipe).data,
            status=status.HTTP_201_CREATED,
        )

    def _handle_remove_relation(self, request, model):
        recipe = self.get_object()
        user = request.user
        relation = model.objects.filter(user=user, recipe=recipe)

        if not relation.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        relation.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        return self._handle_add_relation(request, Favorite)

    @favorite.mapping.delete
    def remove_favorite(self, request, pk=None):
        return self._handle_remove_relation(request, Favorite)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegisterSerializer
        return UserSerializer

    def _get_follow_context(self, request):
        return {
            'request': request,
            'recipes_limit': request.query_params.get('recipes_limit')
        }

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path="me",
    )
    def me(self, request):
        serializer = self.get_serializer(
            request.user,
            context=self.get_serializer_context()
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='set_password',
    )
    def set_password(self, request):
        serializer = PasswordSetSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(
                    serializer.validated_data['current_password']):
                return Response(
                    {'current_password': ['Введён неправильный пароль!']},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, pk=None):
        user = request.user
        author = self.get_object()
        if author == user or \
                Follow.objects.filter(user=user, follower=author).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        Follow.objects.create(user=user, follower=author)
        serializer = FollowSerializer(
            author,
            context=self._get_follow_context(request),
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        user = request.user
        recipes_limit = request.query_params.get('recipes_limit')
        queryset = User.objects.filter(follower__user=user) \
            .annotate(recipes_count=Count('recipe'))
        page = self.paginate_queryset(queryset)
        context = self.get_serializer_context()
        context['recipes_limit'] = recipes_limit

        serializer = FollowSerializer(page, many=True, context=context)
        return self.get_paginated_response(serializer.data)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        user = request.user
        author = self.get_object()

        follow = Follow.objects.filter(user=user, follower=author)
        if not follow.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
