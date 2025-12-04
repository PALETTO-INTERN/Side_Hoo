from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q, Avg 

# ⭐ UserSearchForm 임포트 추가 ⭐
from .forms import TaskForm, TitleForm, ReviewForm, UserSearchForm 
from .models import UserProfile, Task, TaskApplication, TaskReview

User = get_user_model()

# -------------------- 회원가입 및 프로필 생성 자동화 --------------------

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

# -------------------- View 함수 정의 --------------------

# 2. 회원가입 View
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, '회원가입이 성공적으로 완료되었습니다. 로그인해주세요.')
            return redirect('login')
    else:
        form = UserCreationForm()
    
    return render(request, 'core/signup.html', {'form': form})


# 3. 프로필 View (로그인 필요)
@login_required 
def profile(request):
    profile = request.user.userprofile
    
    # 1. 획득 가능한 모든 칭호 목록 생성
    completed_count = profile.tasks_completed
    available_titles = ['🐣 새내기'] # 기본 칭호
    
    if completed_count >= 1:
        available_titles.append('🌱 심부름 초보')
    if completed_count >= 5:
        available_titles.append('🏅 숙련된 도우미')
    if completed_count >= 10:
        available_titles.append('👑 심부름 마스터')

    # 2. 폼 처리 (POST 요청 시 칭호 변경)
    if request.method == 'POST':
        # TitleForm은 instance를 인자로 받지 않는 일반 forms.Form이었으므로 ModelForm처럼 사용하는 부분을 수정합니다.
        # 이전 코드의 TitleForm이 forms.ModelForm이었다고 가정하고 유지합니다.
        form = TitleForm(request.POST, instance=profile, available_titles=available_titles)
        if form.is_valid():
            form.save()
            messages.success(request, f'칭호가 "{profile.selected_title}"로 변경되었습니다.')
            return redirect('profile')
    else:
        # GET 요청 시 폼 인스턴스 생성
        form = TitleForm(instance=profile, available_titles=available_titles)

    # 3. Context 구성
    context = {
        'username': request.user.username,
        'points': profile.points,
        'tasks_completed': profile.tasks_completed,
        'title_badge': profile.selected_title, 
        'title_form': form, 
        'average_rating': profile.average_rating, 
        # 자신이 받은 모든 리뷰 목록 (심부름 리뷰, 일반 리뷰 모두 포함)
        'received_reviews': profile.user.received_reviews.all().select_related('reviewer').order_by('-created_at'),
    }
    return render(request, 'core/profile.html', context)


# 4. 심부름 목록 (메인 페이지) - ⭐ 조건 필터링 로직 추가
def task_list(request):
    # 1. 기본 쿼리셋 설정 (open 상태 또는 등록자 심부름)
    if request.user.is_authenticated:
        tasks_queryset = Task.objects.filter(
            Q(status='open') | Q(registrant=request.user)
        )
    else:
        tasks_queryset = Task.objects.filter(status='open')
    
    # 2. 필터링 파라미터 확인 및 적용
    min_rating = request.GET.get('min_rating')
    required_gender = request.GET.get('gender')

    # 2-1. 최소 별점 필터링
    if min_rating and min_rating.isdigit() and int(min_rating) > 0:
        min_rating = int(min_rating)
        
        # 평균 별점이 min_rating 이상인 등록자(registrant)의 ID 목록을 가져옴
        users_with_high_rating = UserProfile.objects.annotate(
            avg_rating=Avg('user__received_reviews__rating')
        ).filter(avg_rating__gte=min_rating).values_list('user_id', flat=True)
        
        # tasks_queryset을 필터링된 등록자 ID 목록으로 제한
        tasks_queryset = tasks_queryset.filter(registrant__in=users_with_high_rating)
    else:
        min_rating = None
    
    # 2-2. 성별 필터링 (Task 모델의 required_gender 필드를 사용하여 목록을 필터링)
    # Task 모델에는 required_gender가 있으므로, 이를 이용해 목록을 필터링할 수 있습니다.
    if required_gender and required_gender != 'A':
        tasks_queryset = tasks_queryset.filter(required_gender=required_gender)
    else:
        required_gender = 'A'

    # 최종 정렬
    tasks = tasks_queryset.order_by('-created_at')
        
    context = {
        'tasks': tasks,
        # 템플릿에 현재 필터 값과 선택지 전달
        'current_min_rating': min_rating,
        'rating_choices': TaskReview.RATING_CHOICES, 
        'current_gender': required_gender,
        'gender_choices': Task.GENDER_CHOICES, # 모델에서 정의된 성별 선택지
    }
    return render(request, 'core/task_list.html', context)


# 5. 심부름 등록 (로그인 필요)
@login_required
def task_create(request):
    if request.method == 'POST':
        # TaskForm이 required_gender 및 min_rating_required 필드를 처리합니다.
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.registrant = request.user
            task.save()
            messages.success(request, '심부름 공고가 성공적으로 등록되었습니다.')
            return redirect('task_detail', pk=task.pk)
    else:
        form = TaskForm()
        
    return render(request, 'core/task_form.html', {'form': form, 'page_title': '새 심부름 등록'})


# 6. 심부름 상세 보기
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    
    has_applied = False
    if request.user.is_authenticated:
        has_applied = TaskApplication.objects.filter(task=task, applicant=request.user).exists()
        
    # 지원자에 대한 정보에 평균 별점을 추가하기 위해 select_related('applicant__userprofile')을 사용합니다.
    applications = TaskApplication.objects.filter(task=task).select_related('applicant__userprofile')
    
    # ⭐ 리뷰 작성 가능 여부 확인
    review_possible = False
    if task.status == 'completed' and task.registrant == request.user and not hasattr(task, 'review'):
        review_possible = True
        
    context = {
        'task': task,
        'has_applied': has_applied,
        'applications': applications,
        'is_registrant': task.registrant == request.user,
        'review_possible': review_possible,
    }
    return render(request, 'core/task_detail.html', context)


# 7. 심부름 지원 처리 (로그인 필요)
@login_required
@transaction.atomic
def task_apply(request, pk):
    task = get_object_or_404(Task, pk=pk)
    
    if task.registrant == request.user:
        messages.error(request, '본인이 등록한 심부름에는 지원할 수 없습니다.')
        return redirect('task_detail', pk=pk)
    
    # ⭐ 2-1. 지원자가 심부름의 최소 별점 조건을 충족하는지 확인합니다.
    min_rating_required = task.min_rating_required
    if min_rating_required > 0:
        applicant_profile = request.user.userprofile
        if applicant_profile.average_rating < min_rating_required:
            messages.error(request, f'심부름을 수행하려면 최소 별점 {min_rating_required}점 이상이 필요합니다. 현재 별점: {applicant_profile.average_rating}점')
            return redirect('task_detail', pk=pk)

    # ⭐ 2-2. 지원자가 심부름의 성별 조건을 충족하는지 확인합니다.
    # (현재 UserProfile에 성별 필드가 없으므로, 이 기능은 임시로 건너뛰거나, 성별 필드가 있다고 가정하고 주석 처리합니다.)
    # required_gender = task.required_gender
    # if required_gender != 'A' and required_gender != request.user.userprofile.gender:
    #     messages.error(request, '성별 조건이 맞지 않아 지원할 수 없습니다.')
    #     return redirect('task_detail', pk=pk)
    
    if TaskApplication.objects.filter(task=task, applicant=request.user).exists():
        messages.error(request, '이미 이 심부름에 지원했습니다.')
        return redirect('task_detail', pk=pk)

    if task.status != 'open':
        messages.error(request, '모집 중인 심부름이 아닙니다.')
        return redirect('task_detail', pk=pk)
        
    TaskApplication.objects.create(
        task=task,
        applicant=request.user,
        status='pending'
    )
    messages.success(request, f'"{task.title}" 심부름에 지원이 완료되었습니다! 공고주의 선택을 기다려주세요.')
    return redirect('task_detail', pk=pk)


# 8. 심부름 완료 처리 (로그인 및 공고주 권한 필요)
@login_required
@transaction.atomic
def task_complete(request, pk):
    task = get_object_or_404(Task, pk=pk)

    if task.registrant != request.user:
        messages.error(request, '심부름 완료는 등록자만 처리할 수 있습니다.')
        return redirect('task_detail', pk=pk)

    if task.status != 'assigned':
        messages.error(request, '아직 도우미가 할당되지 않았거나 이미 완료된 심부름입니다.')
        return redirect('task_detail', pk=pk)

    # 포인트 지급 및 완료 수 증가
    assigned_user = task.assigned_to
    reward = task.reward_points
    
    assigned_profile = assigned_user.userprofile
    assigned_profile.points += reward
    assigned_profile.tasks_completed += 1
    assigned_profile.save()

    task.status = 'completed'
    task.save()

    messages.success(request, f'"{task.title}" 심부름 완료! 도우미({assigned_user.username}님)에게 {reward} P가 지급되었습니다. 이제 리뷰를 남겨주세요.')
    # 리뷰 페이지로 리다이렉트
    return redirect('task_review', pk=task.pk)

# 9. 심부름 리뷰 및 별점 작성 (로그인 및 공고주 권한 필요)
@login_required
@transaction.atomic
def task_review(request, pk):
    task = get_object_or_404(Task, pk=pk)
    
    if task.registrant != request.user:
        messages.error(request, '리뷰는 등록자만 작성할 수 있습니다.')
        return redirect('task_detail', pk=pk)
    
    if task.status != 'completed':
        messages.error(request, '완료된 심부름에만 리뷰를 작성할 수 있습니다.')
        return redirect('task_detail', pk=pk)
        
    if hasattr(task, 'review'):
        messages.error(request, '이미 이 심부름에 대한 리뷰가 작성되었습니다.')
        return redirect('task_detail', pk=pk)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.task = task
            review.reviewer = request.user
            review.reviewed_user = task.assigned_to # 도우미에게 리뷰를 남김
            review.save()
            
            messages.success(request, f'{task.assigned_to.username}님께 성공적으로 리뷰를 남겼습니다.')
            return redirect('profile')
    else:
        form = ReviewForm()
        
    context = {
        'task': task,
        'form': form,
        'reviewed_user': task.assigned_to,
    }
    return render(request, 'core/review_form.html', context)


# -------------------- ⭐ 사용자 검색 및 일반 리뷰 기능 (새로 추가) ⭐ --------------------

# 10. 사용자 검색 및 리뷰 시작
@login_required
def user_search(request):
    """ 리뷰 대상 사용자를 검색하는 뷰 """
    form = UserSearchForm(request.GET)
    users = User.objects.none() # 기본적으로 빈 쿼리셋
    search_query = None

    if form.is_valid():
        search_query = form.cleaned_data['search_query']
        if search_query:
            # 현재 사용자 자신을 제외하고, 검색어에 이름이 포함된 사용자만 필터링
            users = User.objects.filter(
                username__icontains=search_query
            ).exclude(pk=request.user.pk).select_related('userprofile')
    
    context = {
        'form': form,
        'users': users,
        'search_query': search_query,
    }
    return render(request, 'core/user_search.html', context)

# 11. 사용자에게 리뷰 남기기 (심부름과 무관하게)
@login_required
@transaction.atomic
def user_review(request, username):
    """ 심부름과 관계없이 사용자에게 리뷰를 남기는 뷰 """
    reviewed_user = get_object_or_404(User, username=username)

    if reviewed_user == request.user:
        messages.error(request, '자기 자신에게 리뷰를 남길 수 없습니다.')
        return redirect('user_search')

    # 이미 일반 리뷰를 남겼는지 확인 (task 필드가 null인 리뷰)
    if TaskReview.objects.filter(reviewer=request.user, reviewed_user=reviewed_user, task__isnull=True).exists():
        messages.warning(request, f'{reviewed_user.username}님에게 이미 일반 리뷰를 작성하셨습니다.')
        return redirect('user_search')

    if request.method == 'POST':
        # ReviewForm을 재사용
        form = ReviewForm(request.POST) 
        
        if form.is_valid():
            review = form.save(commit=False)
            review.task = None # 심부름과 연결되지 않음 (TaskReview 모델에서 null=True 허용)
            review.reviewer = request.user
            review.reviewed_user = reviewed_user
            review.save()
            
            messages.success(request, f'{reviewed_user.username}님에게 성공적으로 리뷰를 남겼습니다. 감사합니다!')
            return redirect('profile')
    else:
        form = ReviewForm()
        
    context = {
        'form': form,
        'reviewed_user': reviewed_user,
    }
    return render(request, 'core/user_review_form.html', context)