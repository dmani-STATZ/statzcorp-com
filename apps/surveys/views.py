from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib import messages
from .models import Survey, Question, Submission, Answer, Choice

class SurveyListView(ListView):
    model = Survey
    template_name = 'surveys/survey_list.html'
    context_object_name = 'surveys'

    def get_queryset(self):
        # Safety check: ONLY fetch active public objects (no CUI/CTI/CDI)
        return Survey.public_objects.filter(is_active=True)


def survey_detail_view(request, pk):
    # Safety check: ONLY fetch public objects (no CUI/CTI/CDI)
    survey = get_object_or_404(Survey.public_objects, pk=pk, is_active=True)
    questions = survey.questions.all()  # Also public manager implicitly handles this? Wait, survey is already filtered.

    if request.method == 'POST':
        # Create submission
        submission = Submission.objects.create(
            survey=survey,
            user=request.user if request.user.is_authenticated else None
        )

        for question in questions:
            # Skip if the question itself is classified
            if question.security_classification in ['CUI', 'CTI', 'CDI']:
                continue

            field_name = f'question_{question.pk}'
            value = request.POST.get(field_name, '').strip()

            if question.required and not value:
                messages.error(request, f"The question '{question.text}' is required.")
                submission.delete()
                return redirect('surveys:detail', pk=pk)

            Answer.objects.create(
                submission=submission,
                question=question,
                value=value
            )

        messages.success(request, "Thank you for completing the survey!")
        return redirect('surveys:list')

    return render(request, 'surveys/survey_detail.html', {
        'survey': survey,
        'questions': questions
    })
