from django.contrib.syndication.views import Feed
from django.views.generic import ListView, DetailView
from django.urls import reverse, reverse_lazy

from .models import Article


class ListArticlesView(ListView):
    template_name = "blogapp/articles-list.html"
    context_object_name = "articles"
    queryset = (
        Article.objects
        .filter(pub_date__isnull=False)
        .order_by("-pub_date")
        .defer("body")
        .select_related("author", "category")
        .prefetch_related("tags")
    )


class ArticleDetailView(DetailView):
    model = Article


class LatestArticlesFeed(Feed):
    title = "Blog articles (Latest)"
    description = "Updates on changes and addition blog articles"
    link = reverse_lazy("blogapp:articles_list")

    def items(self):
        return (
            Article.objects
            .filter(pub_date__isnull=False)
            .order_by("-pub_date")[:5]
        )

    def item_title(self, item: Article):
        return item.title

    def item_description(self, item: Article):
        return item.body[:200]

