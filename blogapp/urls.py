from django.urls import path

from .views import (
    ListArticlesView,
    ArticleDetailView,
    LatestArticlesFeed,
)


app_name = 'blogapp'

urlpatterns = [
    path("articles/", ListArticlesView.as_view(), name="articles_list"),
    path("articles/<int:pk>/", ArticleDetailView.as_view(), name="article"),
    path("articles/latest/feed/", LatestArticlesFeed(), name="articles-feed"),
]
