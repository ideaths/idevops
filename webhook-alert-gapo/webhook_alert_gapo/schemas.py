from marshmallow import Schema, fields, ValidationError, validates_schema, EXCLUDE


class AlertSchema(Schema):
    status = fields.Str(required=True, validate=lambda x: x in ['firing', 'resolved'])
    labels = fields.Dict(required=True)
    annotations = fields.Dict(load_default={})
    startsAt = fields.DateTime(load_default=None)
    endsAt = fields.DateTime(load_default=None)
    generatorURL = fields.Str(load_default="")
    fingerprint = fields.Str(load_default="")

    class Meta:
        unknown = EXCLUDE


class AlertmanagerWebhookSchema(Schema):
    version = fields.Str(load_default="4")
    groupKey = fields.Str(load_default="")
    status = fields.Str(load_default="firing")
    receiver = fields.Str(load_default="")
    groupLabels = fields.Dict(load_default={})
    commonLabels = fields.Dict(load_default={})
    commonAnnotations = fields.Dict(load_default={})
    externalURL = fields.Str(load_default="")
    alerts = fields.List(fields.Nested(AlertSchema), required=True)
    truncatedAlerts = fields.Boolean(load_default=False)

    class Meta:
        unknown = EXCLUDE

    @validates_schema
    def validate_alerts(self, data, **kwargs):
        if not data.get('alerts'):
            raise ValidationError('Alerts list cannot be empty')