from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.timezone import now

class Instructor(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_time = models.BooleanField(default=True)
    total_learners = models.PositiveIntegerField(default=0)
    def __str__(self):
        return self.user.username

class Learner(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    occupation = models.CharField(max_length=20, default='student', choices=[
        ('student', 'Student'), ('developer', 'Developer'),
        ('data_scientist', 'Data Scientist'), ('dba', 'Database Admin')])
    social_link = models.URLField(blank=True)
    def __str__(self):
        return self.user.username

class Course(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='course_images/', blank=True)
    description = models.TextField()
    pub_date = models.DateField(default=now)
    instructors = models.ManyToManyField(Instructor, blank=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, through='Enrollment')
    total_enrollment = models.PositiveIntegerField(default=0)
    def __str__(self):
        return self.name

class Lesson(models.Model):
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    content = models.TextField()
    class Meta:
        ordering = ['order', 'pk']
    def __str__(self):
        return self.title

class Enrollment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date_enrolled = models.DateField(default=now)
    mode = models.CharField(max_length=5, default='honor', choices=[
        ('audit', 'Audit'), ('honor', 'Honor'), ('beta', 'Beta')])
    rating = models.FloatField(default=5.0)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'course'], name='unique_enrollment')]
    def __str__(self):
        return f'{self.user.username} — {self.course.name}'

class Question(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, blank=True, null=True)
    content = models.CharField(max_length=1000)
    grade = models.PositiveIntegerField(default=10)
    def clean(self):
        if self.lesson_id and self.course_id != self.lesson.course_id:
            raise ValidationError('The lesson must belong to the question course.')
    def is_get_score(self, selected_ids):
        # Require all correct choices and reject any incorrect selection.
        correct_ids = set(self.choice_set.filter(is_correct=True).values_list('pk', flat=True))
        question_ids = set(self.choice_set.values_list('pk', flat=True))
        return bool(correct_ids) and (set(selected_ids) & question_ids) == correct_ids
    def __str__(self):
        return self.content

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    content = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    def __str__(self):
        return self.content

class Submission(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    choices = models.ManyToManyField(Choice, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f'Submission {self.pk}: {self.enrollment}'
