from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from .models import Choice, Course, Enrollment, Question, Submission


class AssessmentTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('learner', password='test-pass-123')
        self.other = get_user_model().objects.create_user('other', password='test-pass-456')
        self.course = Course.objects.create(name='Django', description='Demo')
        self.enrollment = Enrollment.objects.create(user=self.user, course=self.course)
        self.question = Question.objects.create(course=self.course, content='Select both correct choices', grade=10)
        self.a = Choice.objects.create(question=self.question, content='A', is_correct=True)
        self.b = Choice.objects.create(question=self.question, content='B', is_correct=True)
        self.wrong = Choice.objects.create(question=self.question, content='Wrong')
        self.submit_url = reverse('onlinecourse:submit', args=[self.course.pk])
        self.client.force_login(self.user)

    def test_exact_multiple_choice_grading(self):
        self.assertTrue(self.question.is_get_score([self.a.pk, self.b.pk]))
        self.assertFalse(self.question.is_get_score([self.a.pk]))
        self.assertFalse(self.question.is_get_score([self.a.pk, self.b.pk, self.wrong.pk]))
        self.assertFalse(self.question.is_get_score([]))

    def test_pass_and_fail_results(self):
        for selected, score, passed in [([self.a.pk, self.b.pk], 100, True), ([self.wrong.pk], 0, False), ([], 0, False)]:
            response = self.client.post(self.submit_url, {f'choice_{self.question.pk}': selected}, follow=True)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['score'], score)
            self.assertEqual(response.context['passed'], passed)
        self.assertEqual(Submission.objects.count(), 3)

    def test_reject_other_course_and_invalid_choices(self):
        other_course = Course.objects.create(name='Other', description='Other course')
        other_question = Question.objects.create(course=other_course, content='Other')
        alien = Choice.objects.create(question=other_question, content='Alien', is_correct=True)
        for value in [str(alien.pk), 'not-a-number', '999999']:
            self.assertEqual(self.client.post(self.submit_url, {'choice_1': value}).status_code, 400)
        self.assertEqual(Submission.objects.count(), 0)

    def test_result_is_private_and_course_scoped(self):
        submission = Submission.objects.create(enrollment=self.enrollment)
        result_url = reverse('onlinecourse:show_exam_result', args=[self.course.pk, submission.pk])
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(result_url).status_code, 404)
        self.client.force_login(self.user)
        other_course = Course.objects.create(name='Other', description='Other')
        self.assertEqual(self.client.get(reverse('onlinecourse:show_exam_result', args=[other_course.pk, submission.pk])).status_code, 404)

    def test_enrollment_and_post_are_required(self):
        self.assertEqual(self.client.get(self.submit_url).status_code, 405)
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(self.submit_url).status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.post(self.submit_url).status_code, 302)

    def test_enroll_once_and_render_course(self):
        self.client.force_login(self.other)
        enroll_url = reverse('onlinecourse:enroll', args=[self.course.pk])
        self.client.post(enroll_url)
        self.client.post(enroll_url)
        self.course.refresh_from_db()
        self.assertEqual(self.course.total_enrollment, 1)
        self.assertEqual(Enrollment.objects.filter(user=self.other, course=self.course).count(), 1)
        response = self.client.get(reverse('onlinecourse:course_details', args=[self.course.pk]))
        self.assertContains(response, 'Course assessment')

    def test_admin_lists_expected_sections(self):
        self.user.is_staff = self.user.is_superuser = True
        self.user.save()
        response = self.client.get('/admin/')
        self.assertContains(response, 'Authentication and Authorization')
        self.assertContains(response, 'OnlineCourse')

    def test_empty_exam_does_not_pass(self):
        self.question.delete()
        response = self.client.post(self.submit_url, follow=True)
        self.assertFalse(response.context['passed'])
