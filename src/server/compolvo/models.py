from enum import IntEnum

from tortoise.models import Model
from tortoise.fields import UUIDField, TextField, CharField, IntEnumField, FloatField, IntField, DatetimeField, BooleanField, ForeignKeyField


class Customer(Model):
    id = UUIDField(pk=True)
    name = TextField(null=True)
    email = CharField(255, unique=True)
    password_hash = TextField(null=True)

class Service(Model):
    class RetrievalMethod(IntEnum):
        COMMAND = 1
        APT = 2
        COMPOLVO_PACKAGE = 3

    id = UUIDField(pk=True)
    retrieval_method = IntEnumField(RetrievalMethod)
    retrieval_data = TextField()
    latest_version = TextField(null=True)

class ServiceOffering(Model):
    id = UUIDField(pk=True)
    name = TextField()
    service = ForeignKeyField("models.Service", "service_offerings")
    description = TextField(null=True)
    price = FloatField()
    duration_days = IntField()

class ServicePlan(Model):
    id = UUIDField(pk=True)
    service_offering = ForeignKeyField("models.ServiceOffering", "service_plans")
    customer = ForeignKeyField("models.Customer")
    start_date = DatetimeField()
    end_date = DatetimeField(null=True)
    canceledByUser = BooleanField(default=False)

class Payment(Model):
    id = UUIDField(pk=True)
    service_plan = ForeignKeyField("models.ServicePlan", "payments")
    amount = FloatField()
    date = DatetimeField()

class Agent(Model):
    id = UUIDField(pk=True)
    customer = ForeignKeyField("models.Customer", "agents")
    last_connection_start = DatetimeField(null=True)

class AgentSoftware(Model):
    id = UUIDField(pk=True)
    agent = ForeignKeyField("models.Agent", "agent_softwares")
    service_plan = ForeignKeyField("models.ServicePlan", "agent_softwares")
    installed_version = TextField(null=True)
    corrupt = BooleanField(default=False)