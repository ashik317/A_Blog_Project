from django.db.models.expressions import result
from django.shortcuts import render, get_object_or_404
from django.template.defaultfilters import title
from django.template.defaulttags import comment
from django.views.generic import ListView
from pyexpat.errors import messages

from .forms import EmailPostForm, CommentForm, SearchForm
from .models import Post
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from taggit.models import Tag
from django.db.models import Count
from django.contrib.postgres.search import (SearchVector, SearchQuery, SearchRank, TrigramSimilarity)
def post_list(request, tag_slug=None):
    posts_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        posts_list = posts_list.filter(tags__in=[tag])

    # Pagination with 3 posts per page
    paginator = Paginator(posts_list, 3)
    page_number = request.GET.get('page', 1)
    try:
        posts = paginator.page(page_number)
    # If page_number is not an integer get the first page
    except PageNotAnInteger:
        posts = paginator.page(1)
    # If page_number is out of range get last page of results
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    return render(request, 'blog/list.html', {'posts': posts, 'tag': tag})

'''class PostListView(ListView):
    model = Post
    template_name = 'blog/list.html'
    context_object_name = 'posts'
    paginate_by = 3

    def get_queryset(self):
        return Post.published.all()'''


def post_detail(request, year, month, day, post):
    post = get_object_or_404(
        Post,
        status = Post.Status.PUBLISHED,
        slug=post, publish__year=year, publish__month=month, publish__day=day
    )
    # List of active comments for this post
    comments = post.comments.filter(active=True)
    # Form for users to comment
    form = CommentForm()

    # List of similar posts
    post_tag_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tag_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]

    return render(request, 'blog/detail.html', context={'post': post, 'comments': comments, 'form': form, 'similar_posts': similar_posts})

def post_share(request, post_id):
    post = get_object_or_404(Post, pk = post_id, status = Post.Status.PUBLISHED)
    sent = False
    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = (
                f"{cd['name']} ({cd['email']})"
                f"recommends you read: {post.title}"
            )
            message = (
                f"Read {post.title} at {post_url}\n\n"
                f"{cd['name']}\'s comments: {cd['comments']}"
            )
            send_mail(
                subject=subject,
                message=message,
                from_email=None,
                recipient_list=[cd['to']],
            )
            sent = True
    else:
        form = EmailPostForm()
    return render(request, 'blog/post_share.html', {'post': post, 'form': form, 'sent': sent})

@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post, pk = post_id, status = Post.Status.PUBLISHED)
    comment = None
    form = CommentForm(data=request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()
    return render(request, 'blog/comment.html', context={'post': post, 'form':form, 'comment':comment})

def post_search(request):
    form = SearchForm()
    query = None
    results = []

    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            results = (
                Post.published.annotate(
                    similarity=TrigramSimilarity('title', query),
                ).filter(similarity__gte=0.1)
                .order_by('-similarity')
            )
    return render(request, 'blog/search.html', context={'form':form, 'results':results, 'query':query})
