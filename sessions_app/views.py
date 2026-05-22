import csv
from collections import defaultdict
from datetime import timedelta

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db import IntegrityError, transaction
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Session


def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = UserCreationForm()
    return render(request, "signup.html", {"form": form})


@login_required
def dashboard(request):
    sessions_qs = Session.objects.filter(user=request.user)
    open_session = sessions_qs.filter(end_at__isnull=True).first()

    # Weekly chart data: hours per day-of-week over the last 8 weeks.
    # Aggregation is done in Python (post-fetch) so we can render durations of
    # the currently-open session against `timezone.now()`.
    cutoff = timezone.now() - timedelta(weeks=8)
    recent = sessions_qs.filter(start_at__gte=cutoff)

    # Day-of-week buckets respect the user's TIME_ZONE because USE_TZ=True
    # makes Django convert aware datetimes via .astimezone(current_tz) when
    # we call .weekday() on a localized value.
    current_tz = timezone.get_current_timezone()
    weekday_hours: dict[int, float] = defaultdict(float)
    for s in recent:
        local_start = s.start_at.astimezone(current_tz)
        weekday_hours[local_start.weekday()] += s.duration_hours

    weekday_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    chart_data = [round(weekday_hours.get(i, 0.0), 2) for i in range(7)]

    total_hours = round(sum(s.duration_hours for s in sessions_qs), 2)
    recent_sessions = list(sessions_qs[:20])

    return render(
        request,
        "dashboard.html",
        {
            "open_session": open_session,
            "recent_sessions": recent_sessions,
            "weekday_labels": weekday_labels,
            "chart_data": chart_data,
            "total_hours": total_hours,
        },
    )


@login_required
@require_POST
def start_session(request):
    note = (request.POST.get("notes") or "").strip()[:280]
    try:
        with transaction.atomic():
            Session.objects.create(
                user=request.user,
                start_at=timezone.now(),
                notes=note,
            )
    except IntegrityError:
        # The partial unique index rejected a second open session.
        return HttpResponseBadRequest("You already have an open session. Stop it first.")
    return redirect("dashboard")


@login_required
@require_POST
def stop_session(request):
    open_session = (
        Session.objects.filter(user=request.user, end_at__isnull=True).first()
    )
    if open_session is None:
        return HttpResponseBadRequest("No open session to stop.")
    open_session.end_at = timezone.now()
    open_session.full_clean()
    open_session.save(update_fields=["end_at"])
    return redirect("dashboard")


@login_required
def export_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="lab_sessions.csv"'
    writer = csv.writer(response)
    writer.writerow(["start_at_utc", "end_at_utc", "duration_hours", "notes"])
    for s in Session.objects.filter(user=request.user).order_by("start_at"):
        writer.writerow([
            s.start_at.isoformat(),
            s.end_at.isoformat() if s.end_at else "",
            f"{s.duration_hours:.4f}" if s.end_at else "",
            s.notes,
        ])
    return response
