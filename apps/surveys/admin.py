from django.contrib import admin
from .models import Survey, Question, Choice, Submission, Answer

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3

class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    show_change_link = True

@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ('title', 'security_classification', 'is_active', 'created_at')
    list_filter = ('security_classification', 'is_active', 'created_at')
    search_fields = ('title', 'description')
    inlines = [QuestionInline]

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'survey', 'question_type', 'security_classification', 'required', 'order')
    list_filter = ('survey', 'question_type', 'security_classification', 'required')
    search_fields = ('text',)
    inlines = [ChoiceInline]

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ('question', 'value')
    can_delete = False

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('survey', 'user', 'submitted_at')
    list_filter = ('survey', 'submitted_at')
    inlines = [AnswerInline]
    readonly_fields = ('survey', 'user', 'submitted_at')

    def has_add_permission(self, request):
        return False
