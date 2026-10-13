from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.db.models import F
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .models import Choice, Course, Enrollment, Submission

def index(request):
    return render(request, 'onlinecourse/course_list_bootstrap.html', {
        'course_list': Course.objects.order_by('-pub_date')})

def course_details(request, pk):
    course = get_object_or_404(Course, pk=pk)
    enrolled = request.user.is_authenticated and Enrollment.objects.filter(
        course=course, user=request.user).exists()
    return render(request, 'onlinecourse/course_details_bootstrap.html', {
        'course': course, 'is_enrolled': enrolled,
        'questions': course.question_set.prefetch_related('choice_set').order_by('pk')})

def registration(request):
    form = UserCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.save())
        return redirect('onlinecourse:index')
    return render(request, 'onlinecourse/registration.html', {'form': form})

@login_required
@require_POST
def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    with transaction.atomic():
        _, created = Enrollment.objects.get_or_create(user=request.user, course=course)
        if created:
            Course.objects.filter(pk=course.pk).update(total_enrollment=F('total_enrollment') + 1)
    return redirect('onlinecourse:course_details', pk=course.pk)

def extract_answers(request):
    selected = set()
    for key in request.POST:
        if key.startswith('choice_'):
            selected.update(int(value) for value in request.POST.getlist(key))
    return selected

@login_required
@require_POST
def submit(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    enrollment = get_object_or_404(Enrollment, user=request.user, course=course)
    try:
        selected_ids = extract_answers(request)
    except (ValueError, TypeError):
        return HttpResponseBadRequest('Invalid choice identifier.')
    choices = Choice.objects.filter(pk__in=selected_ids, question__course=course)
    if set(choices.values_list('pk', flat=True)) != selected_ids:
        return HttpResponseBadRequest('Choices must belong to this course.')
    with transaction.atomic():
        submission = Submission.objects.create(enrollment=enrollment)
        submission.choices.set(choices)
    return redirect('onlinecourse:show_exam_result', course_id=course.pk, submission_id=submission.pk)

@login_required
def show_exam_result(request, course_id, submission_id):
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, pk=submission_id,
        enrollment__course=course, enrollment__user=request.user)
    selected_ids = set(submission.choices.values_list('pk', flat=True))
    results = []
    earned = total = 0
    for question in course.question_set.prefetch_related('choice_set').order_by('pk'):
        correct = question.is_get_score(selected_ids)
        total += question.grade
        earned += question.grade if correct else 0
        results.append({'question': question, 'correct': correct, 'choices': [
            {'choice': choice, 'selected': choice.pk in selected_ids}
            for choice in question.choice_set.all()]})
    score = round(100 * earned / total, 2) if total else 0
    return render(request, 'onlinecourse/exam_result_bootstrap.html', {
        'course': course, 'submission': submission, 'results': results,
        'earned': earned, 'total': total, 'score': score, 'passed': total > 0 and score >= 70})
