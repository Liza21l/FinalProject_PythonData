
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Operation(db.Model):
    __tablename__ = "operations"

    id = db.Column(db.Integer, primary_key=True)

    # Поля відповідно до вимог проєкту
    user_id = db.Column(db.Integer, nullable=True)
    structure = db.Column(db.String(50), nullable=True)

    operation_type = db.Column(
        db.String(50),
        nullable=False
    )

    value = db.Column(db.Text, nullable=True)

    timestamp = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=True
    )

    description = db.Column(db.Text, nullable=True)

    # Старі поля залишаємо для сумісності з наявним кодом
    details = db.Column(db.Text, nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "structure": self.structure,
            "operation_type": self.operation_type,
            "value": self.value,
            "timestamp": (
                self.timestamp.isoformat()
                if self.timestamp else None
            ),
            "description": self.description,
            "details": self.details,
            "created_at": self.created_at.isoformat()
        }
