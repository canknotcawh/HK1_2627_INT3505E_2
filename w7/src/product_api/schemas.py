from marshmallow import Schema, fields, validate, validates, ValidationError


class ProductOut(Schema):
    id = fields.Int()
    sku = fields.Str()
    name = fields.Str()
    description = fields.Str(allow_none=True)
    price_cents = fields.Int()
    qty_in_stock = fields.Int()
    archived = fields.Bool()


class ProductIn(Schema):
    sku = fields.Str(required=True, validate=validate.Length(min=3, max=32))
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    description = fields.Str(allow_none=True, load_default=None, validate=validate.Length(max=2000))
    price_cents = fields.Int(required=True, strict=True, validate=validate.Range(min=0))
    qty_in_stock = fields.Int(load_default=0, strict=True, validate=validate.Range(min=0))

    @validates("sku")
    def sku_not_blank(self, value, **kwargs):
        if not value.strip():
            raise ValidationError("sku must not be blank")

    @validates("name")
    def name_not_blank(self, value, **kwargs):
        if not value.strip():
            raise ValidationError("name must not be blank")


class ProductPatch(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=255))
    description = fields.Str(allow_none=True, validate=validate.Length(max=2000))
    price_cents = fields.Int(strict=True, validate=validate.Range(min=0))
    qty_in_stock = fields.Int(strict=True, validate=validate.Range(min=0))

    @validates("name")
    def name_not_blank(self, value, **kwargs):
        if not value.strip():
            raise ValidationError("name must not be blank")


class ReserveIn(Schema):
    qty = fields.Int(required=True, strict=True, validate=validate.Range(min=1))
