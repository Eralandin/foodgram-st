from rest_framework import serializers
from recipes.models import (Recipe, Ingredient,
                            UsedIngredients, Favorite,
                            ShoppingCart)
from users.models import User, Follow
from drf_extra_fields.fields import Base64ImageField


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Ingredient


class UsedIngredientsSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(
        source='ingredient.id')
    name = serializers.ReadOnlyField(
        source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = UsedIngredients
        fields = (
            'id', 'name',
            'measurement_unit', 'amount',
        )


class RecipeSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField(
        read_only=True,
    )
    is_favorited = serializers.SerializerMethodField()
    ingredients = UsedIngredientsSerializer(source='recipeName',
                                            many=True, read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_author(self, obj):
        return UserSerializer(obj.author, context=self.context).data

    def get_is_favorited(self, obj):
        return obj.id in self.context.get('is_favorited_ids', set())

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()

    class Meta:
        fields = (
            'id',
            'author',
            'name',
            'image',
            'text',
            'cooking_time',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
        )
        model = Recipe


class UsedIngredientsCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient')

    class Meta:
        model = UsedIngredients
        fields = (
            'id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = UsedIngredientsCreateSerializer(
        many=True
    )
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = (
            'name', 'image', 'text',
            'cooking_time', 'ingredients',
        )

    def validate_image(self, image):
        if not image:
            raise serializers.ValidationError("Картинка обязательна.")
        return image

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError()
        ids = [item['ingredient'].id for item in ingredients]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError()
        return ingredients

    def create_ingredients(self, recipe, ingredients):
        UsedIngredients.objects.bulk_create([
            UsedIngredients(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount']
            ) for item in ingredients
        ])

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if ingredients_data is not None:
            instance.recipeName.all().delete()
            self.create_ingredients(instance, ingredients_data)
            return instance
        else:
            raise serializers.ValidationError()

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data


class CuttedRecipesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = (
            'id', 'name',
            'image', 'cooking_time',
        )


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Follow.objects.filter(user=request.user, follower=obj).exists()


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class PasswordSetSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)


class FollowSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name',
            'is_subscribed', 'recipes',
            'recipes_count', 'avatar',
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and \
            obj.follower.filter(user=user).exists()

    def get_recipes(self, obj):
        limit = self.context.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj)
        if limit is not None and limit.isdigit():
            recipes = recipes[:int(limit)]
        return CuttedRecipesSerializer(
            recipes,
            many=True,
            context=self.context,
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class FavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorite
        fields = '__all__'


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class UserToRecipeSerializer(serializers.Serializer):

    class Meta:
        fields = ('user', 'recipe')

    def validate(self, data, related_name):
        user = data.get("user")
        recipe = data.get("recipe")

        if getattr(user, related_name).filter(recipe__id=recipe.id).exists():
            raise serializers.ValidationError(
                "Список покупок уже содержит данный рецепт!} "
            )

        return data

    def to_representation(self, instance):
        serializer = CuttedRecipesSerializer(
            instance.recipe,
            context=self.context
        )
        return serializer.data


class ShoppingCartSerializer(UserToRecipeSerializer,
                             serializers.ModelSerializer):

    class Meta(UserToRecipeSerializer.Meta):
        model = ShoppingCart

    def validate(self, data):
        return super().validate(data, "shoppingCart")
