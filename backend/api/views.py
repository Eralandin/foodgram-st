
from rest_framework import viewsets, status
from .serializers import (RecipeSerializer, IngredientSerializer,
                          UserSerializer, UserRegisterSerializer,
                          PasswordSetSerializer, FollowSerializer,
                          RecipeCreateSerializer, CuttedRecipesSerializer,
                          AvatarSerializer, ShoppingCartSerializer,
                          UsedIngredients)
from recipes.models import Recipe, Ingredient, Favorite, ShoppingCart
from users.models import User, Follow
from users.permissions import IsAuthorOrReadOnly
from rest_framework.permissions import (IsAuthenticated, AllowAny,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum
from django.http import FileResponse
from rest_framework.exceptions import NotFound
from django.shortcuts import get_object_or_404
import tempfile


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateSerializer
        return RecipeSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        if user.is_authenticated:
            context['is_favorited_ids'] = set(
                Favorite.objects.filter(user=user)
                .values_list('recipe_id', flat=True)
            )
        else:
            context['is_favorited_ids'] = set()
        return context

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=("post", "delete"),
        permission_classes=(IsAuthenticated,),
        url_path="shopping_cart",
        url_name="shopping_cart",
    )
    def shopping_cart(self, request, pk):
        if request.method == "POST":
            return self.recordUserToRecipe(
                request, pk, ShoppingCartSerializer
            )
        return self.deleteUserToRecipe(
            request, pk, "shoppingCart", ShoppingCart.DoesNotExist,
            "Рецепт отсутствует в списке покупок.",
        )

    def recordUserToRecipe(self, request, pk, serializerClass):
        if not Recipe.objects.filter(pk=pk).exists():
            raise NotFound(detail="Рецепт не найден")
        serializer = serializerClass(
            data={
                "user": request.user.id,
                "recipe": pk,
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def deleteUserToRecipe(self, request, pk, related_name_for_user,
                           notFoundException,
                           notFoundMessage,):
        get_object_or_404(Recipe, pk=pk)
        try:
            getattr(request.user, related_name_for_user).get(
                user=request.user, recipe_id=pk
            ).delete()
        except notFoundException:
            return Response(
                notFoundMessage,
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart',
        url_name='download_shopping_cart'
    )
    def download_shopping_cart(self, request):
        recipe_ids = ShoppingCart.objects.filter(
            user=request.user
        ).values_list('recipe_id', flat=True)

        ingredients = (
            UsedIngredients.objects.filter(recipe_id__in=recipe_ids)
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(totalSum=Sum("amount"))
        )

        if not ingredients:
            return Response(
                {"detail": "Ваша корзина пуста."},
                status=status.HTTP_400_BAD_REQUEST
            )
        txtContent = self.convertToTXT(ingredients)
        return self.responseFromFile(txtContent, filename='shoppingCart.txt')

    def convertToTXT(self, ingredients):
        lines = []
        for item in ingredients:
            name = item['ingredient__name']
            unit = item['ingredient__measurement_unit']
            amount = item['totalSum']
            line = f"{name} — {amount} ({unit})"
            lines.append(line)
        return "\n".join(lines)

    def responseFromFile(self, text, filename):
        tmp = tempfile.NamedTemporaryFile(mode='w+b',
                                          delete=False, suffix='.txt')
        tmp.write(text.encode('utf-8'))
        tmp.flush()
        tmp.seek(0)
        return FileResponse(
            tmp,
            as_attachment=True,
            filename=filename,
            content_type='text/plain')

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

    @action(
        detail=True,
        methods=("get",),
        permission_classes=(IsAuthenticatedOrReadOnly,),
        url_path="get-link",
        url_name="get-link",
    )
    def get_link(self, request, pk):
        instance = self.get_object()

        url = f"{request.get_host()}/s/{instance.id}"

        return Response(data={"short-link": url})

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
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
    )
    def avatar(self, request):
        return self.update_avatar(request) if request.method == "PUT" \
            else self.delete_avatar(request)

    def update_avatar(self, request):
        user = request.user
        serializer = AvatarSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            avatar_url = request.build_absolute_uri(user.avatar.url)
            return Response({"avatar": avatar_url},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)

    def delete_avatar(self, request):
        user = request.user
        if user.avatar:
            user.avatar.delete(save=False)
            user.avatar = None
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

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
