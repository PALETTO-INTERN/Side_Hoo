from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q, Avg # Avg 임포트 유지

# Django의 기본 사용자(User) 모델을 가져옵니다.
User = get_user_model()

# --- 1. 사용자 프로필 및 재화 (포인트) 모델 (변경 없음) ---

class UserProfile(models.Model):
    """
    사용자의 추가 정보와 재화(포인트)를 관리하는 모델입니다.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    points = models.IntegerField(default=0, verbose_name="재화 (포인트)")
    tasks_completed = models.IntegerField(default=0, verbose_name="완료한 심부름 수")
    selected_title = models.CharField(max_length=50, default='🐣 새내기', verbose_name="선택된 칭호")
    bio = models.TextField(blank=True, verbose_name="간단 소개")

    @property
    def average_rating(self):
        """ 자신이 받은 모든 리뷰의 평균 별점을 계산합니다. """
        avg_rating = self.user.received_reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg_rating, 1) if avg_rating is not None else 0.0
    
    @property
    def get_title_badge(self):
        count = self.tasks_completed
        
        if count >= 10:
            return "👑 심부름 마스터"
        elif count >= 5:
            return "🏅 숙련된 도우미"
        elif count >= 1:
            return "🌱 심부름 초보"
        else:
            return "🐣 새내기"

    def __str__(self):
        return f"{self.user.username} - 프로필"

# --- 2. 심부름 (Task) 모델 (조건 필드 추가) ---

class Task(models.Model):
    """
    사용자가 등록하는 심부름 공고를 저장하는 모델입니다.
    """
    STATUS_CHOICES = [
        ('open', '모집 중'),
        ('assigned', '진행 중'),
        ('completed', '완료됨'),
        ('expired', '마감됨'),
    ]
    
    # ⭐ 새로운 심부름 조건 필드 정의 ⭐
    GENDER_CHOICES = [
        ('A', '성별 무관'), # All
        ('M', '남성'),     # Male
        ('F', '여성'),     # Female
    ]

    # 1. 공고 정보
    title = models.CharField(max_length=100, verbose_name="제목")
    content = models.TextField(verbose_name="상세 내용")
    reward_points = models.IntegerField(verbose_name="요구 재화(포인트)")
    location = models.CharField(max_length=200, verbose_name="심부름 위치")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open', verbose_name="상태")

    # 2. 도우미 조건 필드 추가
    required_gender = models.CharField(
        max_length=1, 
        choices=GENDER_CHOICES, 
        default='A', 
        verbose_name="필수 성별 조건"
    )
    min_rating_required = models.IntegerField(
        default=0, 
        choices=[(i, f'{i}점 이상') for i in range(6)], # 0점은 조건 없음
        verbose_name="최소 별점 조건"
    )
    # ---------------------------------------------------
    
    # 3. 시간 정보
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="등록일")
    due_date = models.DateTimeField(verbose_name="마감 기한") 

    # 4. 사용자 연결
    registrant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registered_tasks', verbose_name="등록자")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='assigned_tasks', null=True, blank=True, verbose_name="할당된 도우미")

    def __str__(self):
        return f"[{self.get_status_display()}] {self.title} by {self.registrant.username}"
    
    class Meta:
        ordering = ['-created_at']


# --- 3. 심부름 지원 (Task Application) 모델 (변경 없음) ---

class TaskApplication(models.Model):
    """
    도우미가 특정 심부름에 지원한 기록을 저장하는 모델입니다.
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='applications', verbose_name="심부름 공고")
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applied_tasks', verbose_name="지원자")
    
    APPLICATION_STATUS_CHOICES = [
        ('pending', '대기 중'),
        ('accepted', '수락됨'),
        ('rejected', '거절됨'),
    ]
    status = models.CharField(max_length=10, choices=APPLICATION_STATUS_CHOICES, default='pending', verbose_name="지원 상태")
    
    applied_at = models.DateTimeField(auto_now_add=True, verbose_name="지원 시간")

    def __str__(self):
        return f"{self.applicant.username}의 {self.task.title} 지원 - {self.get_status_display()}"

    class Meta:
        unique_together = ('task', 'applicant')


# --- 4. 심부름 리뷰 (Task Review) 모델 (Task 필드 수정) ---

class TaskReview(models.Model):
    """
    심부름 완료 후 도우미에게 남기는 리뷰 (평가) 모델입니다.
    """
    RATING_CHOICES = [
        (1, '⭐'), (2, '⭐⭐'), (3, '⭐⭐⭐'), (4, '⭐⭐⭐⭐'), (5, '⭐⭐⭐⭐⭐'),
    ]

    # ⭐ task 필드 수정: null=True, blank=True 추가 ⭐
    # (심부름 리뷰 외에 일반 사용자 리뷰도 가능하도록 설정)
    task = models.OneToOneField(
        Task, 
        on_delete=models.CASCADE, 
        related_name='review', 
        verbose_name="심부름 공고", 
        null=True, 
        blank=True # Task와 연결되지 않은 리뷰 허용
    )
    
    # 리뷰 작성자 (공고주 또는 일반 사용자)
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_reviews', verbose_name="리뷰 작성자")
    
    # 리뷰 대상자 (도우미)
    reviewed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_reviews', verbose_name="리뷰 대상자")
    
    # 별점 (1점 ~ 5점)
    rating = models.IntegerField(choices=RATING_CHOICES, verbose_name="별점")
    
    # 리뷰 내용
    comment = models.TextField(blank=True, verbose_name="리뷰 내용")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성일")

    def __str__(self):
        task_title = self.task.title if self.task else "일반 리뷰"
        return f"{task_title} - {self.reviewed_user.username}에게 {self.rating}점"