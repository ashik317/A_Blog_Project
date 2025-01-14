from django.contrib import admin
from .models import Post

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'author', 'publish', 'status')
    list_filter = ('status', 'publish', 'author', 'created')
    date_hierarchy = 'publish'
    search_fields = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('author',)
    ordering = ['publish']
    show_facets = admin.ShowFacets.ALWAYS

