from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from products.models import Product
from .models import Review, ReviewHelpful
from .forms import ReviewForm


@login_required
def add_review(request, product_id):
    """Add a review for a product"""
    product = get_object_or_404(Product, id=product_id)
    
    # Check if user already reviewed this product
    if Review.objects.filter(product=product, user=request.user).exists():
        messages.warning(request, 'You have already reviewed this product.')
        return redirect('products:product_detail', id=product.id, slug=product.slug)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, 'Your review has been added successfully!')
            return redirect('products:product_detail', id=product.id, slug=product.slug)
    else:
        form = ReviewForm()
    
    return render(request, 'reviews/add_review.html', {
        'form': form,
        'product': product
    })


@login_required
def edit_review(request, review_id):
    """Edit user's own review"""
    review = get_object_or_404(Review, id=review_id, user=request.user)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your review has been updated successfully!')
            return redirect('products:product_detail', 
                          id=review.product.id, 
                          slug=review.product.slug)
    else:
        form = ReviewForm(instance=review)
    
    return render(request, 'reviews/edit_review.html', {
        'form': form,
        'review': review
    })


@login_required
def delete_review(request, review_id):
    """Delete user's own review"""
    review = get_object_or_404(Review, id=review_id, user=request.user)
    product = review.product
    
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Your review has been deleted.')
        return redirect('products:product_detail', id=product.id, slug=product.slug)
    
    return render(request, 'reviews/delete_review.html', {'review': review})


def product_reviews(request, product_id):
    """Display all reviews for a product"""
    product = get_object_or_404(Product, id=product_id)
    reviews_list = Review.objects.filter(product=product, active=True)
    
    # Pagination
    paginator = Paginator(reviews_list, 10)  # 10 reviews per page
    page_number = request.GET.get('page')
    reviews = paginator.get_page(page_number)
    
    return render(request, 'reviews/product_reviews.html', {
        'product': product,
        'reviews': reviews
    })


@login_required
@require_POST
def mark_helpful(request, review_id):
    """Mark a review as helpful"""
    review = get_object_or_404(Review, id=review_id)
    
    # Don't allow users to mark their own reviews as helpful
    if review.user == request.user:
        return JsonResponse({'success': False, 'error': 'Cannot mark your own review as helpful'})
    
    helpful_vote, created = ReviewHelpful.objects.get_or_create(
        review=review,
        user=request.user
    )
    
    if not created:
        # User already marked this review as helpful, remove the vote
        helpful_vote.delete()
        is_helpful = False
    else:
        is_helpful = True
    
    helpful_count = review.helpful_votes.count()
    
    return JsonResponse({
        'success': True,
        'is_helpful': is_helpful,
        'helpful_count': helpful_count
    })


@login_required
def user_reviews(request):
    """Display user's own reviews"""
    reviews = Review.objects.filter(user=request.user)
    
    paginator = Paginator(reviews, 10)
    page_number = request.GET.get('page')
    reviews = paginator.get_page(page_number)
    
    return render(request, 'reviews/user_reviews.html', {'reviews': reviews})