import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from onlinecourse.models import Choice, Course, Instructor, Learner, Lesson, Question


class Command(BaseCommand):
    help = 'Create a reproducible demonstration course. Set DEMO_ADMIN_PASSWORD first.'

    def handle(self, *args, **options):
        password = os.environ.get('DEMO_ADMIN_PASSWORD')
        if not password:
            raise CommandError('Set DEMO_ADMIN_PASSWORD to your chosen local demo password.')
        User = get_user_model()
        admin, created = User.objects.get_or_create(username='demo_admin', defaults={
            'is_staff': True, 'is_superuser': True})
        if created:
            admin.set_password(password)
            admin.save()
        instructor, _ = Instructor.objects.get_or_create(user=admin)
        Learner.objects.get_or_create(user=admin)
        course, _ = Course.objects.get_or_create(name='Django Application Development', defaults={
            'description': 'Learn Django models, templates, and views. Complete the lessons and test your knowledge with the course assessment.'})
        course.instructors.add(instructor)
        lessons = [
            ('Models and databases', 'Django models define database tables. ForeignKey creates a many-to-one relationship; ManyToManyField connects multiple records on both sides.'),
            ('Views and templates', 'Views process requests and return responses. Templates present data using Django tags, such as for loops and URL reversal.'),
            ('Assessment and results', 'A submission belongs to an enrollment. Each question earns points only when all correct choices, and no incorrect choices, are selected.'),
        ]
        lesson_objects = []
        for order, (title, content) in enumerate(lessons, start=1):
            lesson, _ = Lesson.objects.get_or_create(course=course, order=order, defaults={'title': title, 'content': content})
            lesson_objects.append(lesson)
        questions = [
            ('Which Django field defines a many-to-one relationship?', [('ForeignKey', True), ('CharField', False), ('BooleanField', False)]),
            ('Which Django features help render a course page? Select all correct answers.', [('Template for loops', True), ('URL template tags', True), ('Deleting the database', False)]),
            ('What does an exam Submission record store?', [('The enrollment and selected choices', True), ('Only a course image', False), ('The browser password', False)]),
        ]
        for lesson, (content, choices) in zip(lesson_objects, questions):
            question, _ = Question.objects.get_or_create(course=course, content=content, defaults={'lesson': lesson, 'grade': 10})
            for text, correct in choices:
                Choice.objects.get_or_create(question=question, content=text, defaults={'is_correct': correct})
        self.stdout.write(self.style.SUCCESS('Demo ready: demo_admin; one course, three lessons, three questions.'))
