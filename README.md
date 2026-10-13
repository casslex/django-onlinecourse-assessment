# Online Course: Django Assessment Project

An implementation of the IBM Django final project assessment feature. The project layout follows the official IBM starter; assessment models, views, administration, templates, and tests were implemented for this submission.

## Run locally

Requires Python 3.10+.

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
```

Choose a demo password and set `DEMO_ADMIN_PASSWORD` in your terminal, then run:

```sh
python manage.py seed_demo
python manage.py runserver
```

Open http://127.0.0.1:8000/onlinecourse/ and log in as `demo_admin` with your chosen password. Enroll in the course and submit the exam. The administrator is available at http://127.0.0.1:8000/admin/.

`seed_demo` creates three lessons and three assessment questions, including a question with multiple correct choices. It is safe to run again without duplicating data.

## Assessment implementation

- `onlinecourse/models.py`: Course, Lesson, Instructor, Learner, Enrollment, Question, Choice, Submission.
- `onlinecourse/admin.py`: seven model imports, QuestionInline, ChoiceInline, QuestionAdmin, LessonAdmin, and model registrations.
- `onlinecourse/templates/onlinecourse/course_details_bootstrap.html`: course name, related lessons, Bootstrap styles, CSRF-protected exam form.
- `onlinecourse/views.py`: `submit` validates course choices and enrollment; `show_exam_result` calculates the score and protects result ownership.
- `onlinecourse/urls.py`: named routes for submission and exam results.
- Screenshots: `screenshots/03-admin-site.png`, `screenshots/07-final.png`.

Each question earns full credit only when the selected choices exactly match its correct answers. Passing requires at least 70%. Results show selected choices, correct answers, points, and a Congratulations message for a passing attempt.

## Validation

```sh
python manage.py check
python manage.py test onlinecourse
```

Tests cover passing/failing/empty submissions, multiple-answer grading, invalid choices, foreign-course choices, enrollment, request methods, ownership, and admin sections.

## Local settings

SQLite and local debug mode are used for development. For deployment set `DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY`, and `DJANGO_ALLOWED_HOSTS`, and configure a production web server. Database, passwords, and local environment files are excluded from version control. Bootstrap CSS is loaded from jsDelivr.

Official assignment starter: https://github.com/ibm-developer-skills-network/final-cloud-app-with-database (Apache-2.0; license retained).
