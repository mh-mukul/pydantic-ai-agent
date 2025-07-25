from sqlalchemy.types import TypeDecorator, Text
from sqlalchemy.dialects import postgresql, mysql
import json

class JSONType(TypeDecorator):
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(postgresql.JSONB(astext_type=Text()))
        elif dialect.name == 'mysql':
            return dialect.type_descriptor(mysql.JSON())
        else:  # SQLite fallback
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value
