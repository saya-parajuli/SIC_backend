import json
from datetime import date, timedelta
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncDate

from properties.models import Property, SmartMeter
from demand_response.models import DRResult, PeakEvent
from forecasting.models import LoadReading

User = get_user_model()


@staff_member_required
def admin_dashboard(request):
    """Custom admin dashboard view — feeds all chart and table data."""

    # ── KPI stats ────────────────────────────────────────────────
    total_users      = User.objects.filter(is_active=True).count()
    total_meters     = SmartMeter.objects.filter(is_active=True).count()
    total_properties = Property.objects.filter(is_active=True).count()
    # active_alerts    = PeakEvent.objects.filter(is_resolved=False).count()

    # dr_agg = DRResult.objects.aggregate(
    #     total_savings=Sum('cost_saving_gbp'),
    #     total_co2=Sum('carbon_reduced_kg'),
    # )
    # total_savings = round(dr_agg['total_savings'] or 0, 2)
    # total_co2     = round(dr_agg['total_co2']     or 0, 2)

    # ── Daily consumption — last 30 days ─────────────────────────
    thirty_days_ago = date.today() - timedelta(days=30)
    daily_qs = (
        LoadReading.objects
        .filter(datetime__date__gte=thirty_days_ago)
        .annotate(day=TruncDate('datetime'))
        .values('day')
        .annotate(total=Sum('load_kwh'))
        .order_by('day')
    )
    daily_labels = [str(r['day']) for r in daily_qs]
    daily_kwh    = [round(r['total'], 2) for r in daily_qs]

    # ── Per-user summary table ────────────────────────────────────
    users = User.objects.filter(is_active=True).prefetch_related(
        'owned_properties', 'dr_results', 'peak_events'
    )

    user_summaries = []
    user_names     = []
    user_savings   = []

    for u in users:
        # dr_data = DRResult.objects.filter(user=u).aggregate(
        #     savings=Sum('cost_saving_gbp'),
        #     co2=Sum('carbon_reduced_kg'),
        # )
        has_risk = PeakEvent.objects.filter(user=u, is_resolved=False).exists()

        user_summaries.append({
            'name':           u.full_name or u.email,
            'email':          u.email,
            'role':           u.role,
            'property_count': Property.objects.filter(owner=u).count(),
            'meter_count':    SmartMeter.objects.filter(property__owner=u).count(),
            # 'total_savings':  round(dr_data['savings'] or 0, 2),
            # 'total_co2':      round(dr_data['co2']     or 0, 2),
            'has_risk':       has_risk,
        })
        user_names.append(u.full_name or u.email.split('@')[0])
        # user_savings.append(round(dr_data['savings'] or 0, 2))

    # ── Hourly average load ───────────────────────────────────────
    hourly_qs = (
        LoadReading.objects
        .values('hour')
        .annotate(avg_kwh=Avg('load_kwh'))
        .order_by('hour')
    )
    hourly_labels = [str(r['hour']).zfill(2) + ':00' for r in hourly_qs]
    hourly_avg    = [round(r['avg_kwh'], 3) for r in hourly_qs]

    # ── DR pie chart ──────────────────────────────────────────────
    users_with_dr    = DRResult.objects.values('user').distinct().count()
    users_without_dr = max(0, total_users - users_with_dr)

    # ── Recent alerts ─────────────────────────────────────────────
    recent_alerts = DRResult.objects.filter(
        has_risk=True
    ).order_by('-generated_at')[:10]

    context = {
        # KPIs
        'total_users':       total_users,
        'total_meters':      total_meters,
        'total_properties':  total_properties,
        # 'total_savings':     total_savings,
        # 'total_co2':         total_co2,
        # 'active_alerts':     active_alerts,

        # Charts — serialized to JSON for Chart.js
        'daily_labels':      json.dumps(daily_labels),
        'daily_kwh':         json.dumps(daily_kwh),
        'user_names':        json.dumps(user_names),
        'user_savings':      json.dumps(user_savings),
        'hourly_labels':     json.dumps(hourly_labels),
        'hourly_avg':        json.dumps(hourly_avg),
        'dr_optimized_count': users_with_dr,
        'dr_not_run_count':   users_without_dr,

        # Table and alerts
        'user_summaries':    user_summaries,
        'recent_alerts':     recent_alerts,
    }

    return render(request, 'admin/index.html', context)