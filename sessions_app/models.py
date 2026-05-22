from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Session(models.Model):
    """A lab study session, modeled as a half-open interval [start_at, end_at).

    `end_at` is NULL while the session is open. A partial unique index in the
    migration enforces that each user has at most one open (NULL-ended) session
    at a time, without any application-level locking.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lab_sessions",
    )
    start_at = models.DateTimeField()
    end_at = models.DateTimeField(null=True, blank=True)
    notes = models.CharField(max_length=280, blank=True)

    class Meta:
        ordering = ("-start_at",)
        indexes = [
            models.Index(fields=("user", "start_at")),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_at__isnull=True) | models.Q(end_at__gt=models.F("start_at")),
                name="session_end_after_start",
            ),
        ]

    def __str__(self) -> str:
        state = "open" if self.end_at is None else "closed"
        return f"Session<{self.user_id} {self.start_at:%Y-%m-%d %H:%M} {state}>"

    @property
    def is_open(self) -> bool:
        return self.end_at is None

    @property
    def duration_hours(self) -> float:
        end = self.end_at or timezone.now()
        return (end - self.start_at).total_seconds() / 3600.0

    def clean(self) -> None:
        super().clean()
        if self.end_at is not None and self.end_at <= self.start_at:
            raise ValidationError({"end_at": "end_at must be strictly after start_at."})
