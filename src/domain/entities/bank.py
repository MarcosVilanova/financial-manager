from dataclasses import dataclass
from uuid import UUID, uuid4

@dataclass
class Bank:
    name: str
    id: UUID

    @staticmethod
    def create(name: str):
        if not name or not name.strip():
            raise ValueError("O nome do banco é obrigatório.")

        return Bank(
            id=uuid4(),
            name=name.strip()
        )
