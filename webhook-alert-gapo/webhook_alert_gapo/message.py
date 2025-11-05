from datetime import datetime


def create_message(config, template_manager, routing_value: str, firing_alerts, resolved_alerts) -> str:
    parts = []
    parts.append(f"🏷️ **{config.ROUTING_LABEL.title()}: {routing_value.upper()}**")
    summaries = []
    if firing_alerts:
        summaries.append(f"{len(firing_alerts)} firing")
    if resolved_alerts:
        summaries.append(f"{len(resolved_alerts)} resolved")
    if summaries:
        parts.append(f"📊 **Summary**: {', '.join(summaries)}\n")
    if firing_alerts:
        parts.append("🚨 **Alerts Firing** 🚨")
        for alert in firing_alerts:
            parts.append(template_manager.render_alert(alert, config.ROUTING_LABEL, routing_value))
        parts.append("")
    if resolved_alerts:
        parts.append("✅ **Alerts Resolved** ✅")
        for alert in resolved_alerts:
            parts.append(template_manager.render_alert(alert, config.ROUTING_LABEL, routing_value))
        parts.append("")
    parts.append(f"⏰ **Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return "\n".join(parts)