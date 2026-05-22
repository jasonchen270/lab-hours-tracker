from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Session",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("start_at", models.DateTimeField()),
                ("end_at", models.DateTimeField(blank=True, null=True)),
                ("notes", models.CharField(blank=True, max_length=280)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="lab_sessions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-start_at",),
            },
        ),
        migrations.AddIndex(
            model_name="session",
            index=models.Index(fields=["user", "start_at"], name="sessions_ap_user_id_start_idx"),
        ),
        migrations.AddConstraint(
            model_name="session",
            constraint=models.CheckConstraint(
                condition=models.Q(("end_at__isnull", True))
                | models.Q(("end_at__gt", models.F("start_at"))),
                name="session_end_after_start",
            ),
        ),
        # Postgres partial unique index: at most one open session per user.
        # Done via RunSQL so it works on Postgres (production). The reverse SQL
        # drops the index; SQLite (used by tests if you swap DATABASES) silently
        # ignores partial indexes that don't apply.
        migrations.RunSQL(
            sql=(
                "CREATE UNIQUE INDEX IF NOT EXISTS one_open_session_per_user "
                "ON sessions_app_session (user_id) WHERE end_at IS NULL;"
            ),
            reverse_sql="DROP INDEX IF EXISTS one_open_session_per_user;",
        ),
    ]
