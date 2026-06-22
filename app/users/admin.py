from django.contrib import admin

from .models import (
    VpnServerRunway,
    VpnProfile,
    VpnStatsSnapshot,
    VpnTrafficPeriod,
    VpnDonorPreference,
    VpnRunwayLedgerEntry,
    VpnFeedbackTicket,
)


@admin.register(VpnServerRunway)
class VpnServerRunwayAdmin(admin.ModelAdmin):
    list_display = ('label', 'prepaid_until', 'upcoming_payment_amount', 'currency', 'active')
    list_filter = ('active', 'currency')


@admin.register(VpnProfile)
class VpnProfileAdmin(admin.ModelAdmin):
    list_display = ('label', 'user', 'status', 'token_expires_at', 'last_fresh_status')
    list_filter = ('status', 'last_fresh_status')
    search_fields = ('label', 'user__username', 'user__first_name')
    readonly_fields = ('subscription_token', 'token_expires_at', 'artifact_label', 'last_refreshed_at')


@admin.register(VpnStatsSnapshot)
class VpnStatsSnapshotAdmin(admin.ModelAdmin):
    list_display = ('source_label', 'profile', 'captured_at', 'uplink_bytes', 'downlink_bytes')
    list_filter = ('source',)
    search_fields = ('source_label', 'profile__label', 'profile__user__username')


@admin.register(VpnTrafficPeriod)
class VpnTrafficPeriodAdmin(admin.ModelAdmin):
    list_display = ('profile', 'period_kind', 'period_start', 'uplink_bytes', 'downlink_bytes')
    list_filter = ('period_kind', 'period_start')
    search_fields = ('profile__label', 'profile__user__username')


@admin.register(VpnDonorPreference)
class VpnDonorPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_visible', 'public_name')
    list_filter = ('is_visible',)
    search_fields = ('user__username', 'user__first_name', 'public_name')


@admin.register(VpnRunwayLedgerEntry)
class VpnRunwayLedgerEntryAdmin(admin.ModelAdmin):
    list_display = ('entry_type', 'user', 'amount', 'currency', 'received_at', 'is_confirmed')
    list_filter = ('entry_type', 'currency', 'is_confirmed', 'received_at')
    search_fields = ('user__username', 'user__first_name', 'note')


@admin.register(VpnFeedbackTicket)
class VpnFeedbackTicketAdmin(admin.ModelAdmin):
    list_display = ('user', 'reason', 'artifact_label', 'status', 'insert_timestamp')
    list_filter = ('reason', 'status')
    search_fields = ('user__username', 'user__first_name', 'artifact_label', 'message')
