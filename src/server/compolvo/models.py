from tortoise.models import Model
from tortoise import fields


class Customer(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()
    email = fields.CharField(255, unique=True)
    password_hash = fields.TextField(null=True)

