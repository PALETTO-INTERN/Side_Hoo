# core/forms.py

from django import forms
from django.forms import DateTimeInput
from django.utils import timezone
from .models import Task, UserProfile, TaskReview # TaskReview 모델 임포트 유지

# --- DateTimeInput 설정 ---
class TaskDateTimeInput(DateTimeInput):
    input_type = 'datetime-local'
    format = '%Y-%m-%dT%H:%M' 

# --- 1. TaskForm 관련 클래스 (조건 필드 추가) ---
class TaskForm(forms.ModelForm):
    # due_date 필드 위젯 설정을 폼 필드로 직접 정의합니다.
    due_date = forms.DateTimeField(
        label='마감 기한',
        input_formats=['%Y-%m-%d %H:%M'], # Python 코드에서 처리할 형식
        widget=TaskDateTimeInput() # 위에서 정의한 위젯 사용
    )

    class Meta:
        model = Task
        # ⭐ fields에 required_gender와 min_rating_required 추가 ⭐
        fields = ['title', 'content', 'reward_points', 'location', 'due_date', 'required_gender', 'min_rating_required']
        
        labels = {
            'title': '심부름 제목',
            'content': '상세 내용',
            'reward_points': '요구 포인트',
            'location': '위치/장소',
            'due_date': '마감 기한',
            # ⭐ 추가된 필드의 라벨 ⭐
            'required_gender': '필수 성별 조건',
            'min_rating_required': '최소 별점 조건 (0점은 무관)',
        }
        
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'reward_points': forms.NumberInput(attrs={'class': 'form-control', 'min': 10}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            # 성별 및 별점 필드에 부트스트랩 클래스 적용
            'required_gender': forms.Select(attrs={'class': 'form-select'}),
            'min_rating_required': forms.Select(attrs={'class': 'form-select'}),
        }
    
    # 마감 기한 검증 로직 추가 (필요한 경우)
    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date <= timezone.now():
            raise forms.ValidationError("마감 기한은 현재 시각보다 미래여야 합니다.")
        return due_date

# --- 2. TitleForm 관련 클래스 (칭호 선택) ---

class TitleForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['selected_title']
    
    def __init__(self, *args, **kwargs):
        available_titles = kwargs.pop('available_titles', []) 
        super().__init__(*args, **kwargs)

        # 획득 가능한 칭호 목록으로 드롭다운 선택지를 구성합니다.
        choices = [(title, title) for title in available_titles]
        self.fields['selected_title'].widget = forms.Select(choices=choices, attrs={'class': 'form-select'})
        self.fields['selected_title'].label = "선택 가능한 칭호"

# --- 3. ReviewForm 관련 클래스 (리뷰 작성) ---

class ReviewForm(forms.ModelForm):
    class Meta:
        model = TaskReview
        # 뷰에서 처리할 필드 (task, reviewer, reviewed_user)는 제외하고 사용자 입력 필드만 남김
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'rating': '별점',
            'comment': '리뷰 내용',
        }

# --- 4. UserSearchForm 관련 클래스 (사용자 검색) ⭐ 새로 추가 ⭐
class UserSearchForm(forms.Form):
    """ 리뷰 대상 사용자를 검색하는 폼 """
    search_query = forms.CharField(
        max_length=150, 
        required=False,
        label='사용자 이름 검색',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '리뷰 대상자의 사용자 이름을 입력하세요'})
    )