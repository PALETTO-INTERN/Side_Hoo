# core/urls.py (최종 업데이트)

from django.urls import path
from . import views # core/views.py 파일의 함수들을 사용하기 위해 임포트

urlpatterns = [
    # 1. 메인 페이지 (심부름 목록이 됨)
    path('', views.task_list, name='home'), 
    
    # 2. 프로필 페이지
    path('profile/', views.profile, name='profile'),
    
    # 3. 회원가입 페이지
    path('signup/', views.signup, name='signup'),

    # --- 4. 심부름 관련 URL ---
    # 4. 심부름 등록
    path('task/new/', views.task_create, name='task_create'),
    # 5. 심부름 상세 보기
    path('task/<int:pk>/', views.task_detail, name='task_detail'),
    # 6. 심부름 지원 처리
    path('task/<int:pk>/apply/', views.task_apply, name='task_apply'),
    # 7. 심부름 완료 처리
    path('task/<int:pk>/complete/', views.task_complete, name='task_complete'),
    
    # 8. 심부름 리뷰 작성 페이지
    path('task/<int:pk>/review/', views.task_review, name='task_review'),
    
    # --- 5. 사용자 검색 및 일반 리뷰 URL ⭐ 새로 추가된 경로 ⭐ ---
    
    # 9. 사용자 검색 (리뷰 대상 찾기)
    path('users/search/', views.user_search, name='user_search'),
    
    # 10. 특정 사용자에게 리뷰 남기기
    path('users/<str:username>/review/', views.user_review, name='user_review'),
]