from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from movies.models import MovieNightInvitation
from movies.tasks import send_invitation, send_attendance_change

USE_CELERY = True


@receiver(post_save, sender=MovieNightInvitation, dispatch_uid="invitation_create")
def invitation_create(sender, created, instance, **kwargs):
    if created:
        if USE_CELERY:
            send_invitation.delay(instance.pk)
        else:
            send_invitation(instance.pk)


@receiver(pre_save, sender=MovieNightInvitation, dispatch_uid="invitation_update")
def invitation_update(sender, instance, **kwargs):
    if not instance.pk:
        # is a new one
        return

    previous_invitation = MovieNightInvitation.objects.get(pk=instance.pk)
    instance.attendance_confirmed = True

    # only notify if there is a change in attendance
    if previous_invitation.is_attending != instance.is_attending:
        if USE_CELERY:
            send_attendance_change.delay(instance.pk, instance.is_attending)
        else:
            send_attendance_change(instance.pk, instance.is_attending)
