from dataclasses import dataclass
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, ListAttribute


class Apartment(Model):
    class Meta:
        table_name = 'apartments'
        region = 'us-east-1'
        host = 'http://localhost:4800'
    
    name = UnicodeAttribute(hash_key=True)
    address = UnicodeAttribute()
    url = UnicodeAttribute()
    notes = UnicodeAttribute()
    features = ListAttribute(default=list)


@dataclass
class Feature():
    name: str
    value: str | bool | int
