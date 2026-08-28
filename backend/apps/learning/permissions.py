def user_has_access_to_course(user, course) -> bool:
    """Un utilisateur a accès à une formation s'il y est inscrit (paiement confirmé ou licence)."""
    if not user or not user.is_authenticated:
        return False
    return course.enrollments.filter(user=user).exists()


def user_has_access_to_lesson(user, lesson) -> bool:
    if lesson.is_preview:
        return True
    return user_has_access_to_course(user, lesson.module.course)
