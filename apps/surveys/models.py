from django.db import models
from django.conf import settings

# Custom manager to prevent leaking CUI, CTI, or CDI (Controlled Unclassified Info)
class PublicAccessManager(models.Manager):
    def get_queryset(self):
        # Exclude any records flagged with sensitive classifications
        return super().get_queryset().exclude(
            security_classification__in=['CUI', 'CTI', 'CDI']
        )

class ClassifiedModel(models.Model):
    CLASSIFICATION_CHOICES = [
        ('PUBLIC', 'Public / Unclassified'),
        ('CUI', 'Controlled Unclassified Information (CUI)'),
        ('CTI', 'Controlled Technical Information (CTI)'),
        ('CDI', 'Covered Defense Information (CDI)'),
    ]

    security_classification = models.CharField(
        max_length=10,
        choices=CLASSIFICATION_CHOICES,
        default='PUBLIC',
        help_text='Determine if this data contains sensitive government/defense information'
    )

    # Managers
    objects = models.Manager()              # Default manager for internal use
    public_objects = PublicAccessManager()   # Safety manager for public views

    class Meta:
        abstract = True


class Survey(ClassifiedModel):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} [{self.get_security_classification_display()}]"


class Question(ClassifiedModel):
    QUESTION_TYPES = [
        ('TEXT', 'Single Line Text'),
        ('PARAGRAPH', 'Multiple Line Paragraph'),
        ('CHOICE', 'Single Selection (Radio Button)'),
    ]

    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=500)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='TEXT')
    required = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.text} ({self.get_question_type_display()})"


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text


class Submission(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='submissions')
    submitted_at = models.DateTimeField(auto_now_add=True)
    # Optional link to user if logged in
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    def __str__(self):
        return f"Submission for {self.survey.title} at {self.submitted_at}"


class Answer(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    value = models.TextField()

    def __str__(self):
        return f"Answer to: {self.question.text[:30]}"
