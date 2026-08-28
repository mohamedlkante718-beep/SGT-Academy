from .models import Answer, Question, QuizResult


def _grade_question(question: Question, submission: dict):
    """
    Retourne (is_correct, points_awarded). Les questions à réponse courte ne
    sont pas corrigées automatiquement dans cette version (nécessitent une
    relecture humaine) — on ne fait jamais semblant de les corriger (§53).
    """
    if question.question_type == Question.SHORT_ANSWER:
        return False, 0

    answer_id = submission.get("answer_id")
    if not answer_id:
        return False, 0

    selected = Answer.objects.filter(id=answer_id, question=question).first()
    if selected and selected.is_correct:
        return True, question.points
    return False, 0


def grade_questions(questions, submissions_by_question_id: dict):
    """
    Corrige un ensemble de questions face aux réponses soumises.
    Retourne (score_percent, passed_details) où passed_details est une liste
    de tuples (question, is_correct, points_awarded, selected_answer_id).
    """
    max_points = sum(q.points for q in questions) or 0
    total_awarded = 0
    details = []

    for question in questions:
        submission = submissions_by_question_id.get(str(question.id), {})
        is_correct, points_awarded = _grade_question(question, submission)
        total_awarded += points_awarded
        details.append((question, is_correct, points_awarded, submission.get("answer_id")))

    score_percent = round((total_awarded / max_points) * 100) if max_points else 0
    return score_percent, details


def grade_quiz_attempt(attempt, submissions_by_question_id: dict):
    questions = list(attempt.quiz.questions.prefetch_related("answers"))
    score_percent, details = grade_questions(questions, submissions_by_question_id)

    QuizResult.objects.bulk_create(
        [
            QuizResult(
                attempt=attempt,
                question=question,
                selected_answer_id=answer_id,
                is_correct=is_correct,
                points_awarded=points_awarded,
            )
            for question, is_correct, points_awarded, answer_id in details
        ]
    )

    attempt.score_percent = score_percent
    attempt.passed = score_percent >= attempt.quiz.pass_score_percent
    return attempt


def grade_exam_attempt(attempt, submissions_by_question_id: dict):
    questions = list(attempt.exam.questions.prefetch_related("answers"))
    score_percent, _details = grade_questions(questions, submissions_by_question_id)

    attempt.score_percent = score_percent
    attempt.passed = score_percent >= attempt.exam.pass_score_percent
    return attempt
