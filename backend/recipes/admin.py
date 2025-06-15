from django.contrib import admin
from .models import Recipe, Ingredient, UsedIngredients, Favorite, ShoppingCart
from django.db.models import Count


class InlineModelUsedIngredients(admin.TabularInline):
    model = UsedIngredients
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
        'favorites_count'
    )
    search_fields = (
        'name',
        'author__username',
        'author__email',
    )
    inlines = [InlineModelUsedIngredients]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(fav_count=Count('favorite'))

    @admin.display(description='Добавлений в избранное')
    def favorites_count(self, obj):
        return obj.fav_count


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(UsedIngredients)
class UsedIngredientsAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
