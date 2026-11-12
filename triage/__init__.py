"""AI log triage: reads the app's telemetry and explains what broke.

Kept separate from the app (``src/``): it only reads telemetry, so it could
point at any service that emits the same events.
"""
