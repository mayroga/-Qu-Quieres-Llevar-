# schemas.py - Modelos Pydantic y Categorías Visuales
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List

class CategoryVisualEnum(str, Enum):
    PUEDES_LLEVARLO = "PUEDES LLEVARLO"
    PUEDES_LLEVARLO_PERO = "PUEDES LLEVARLO, PERO..."
    NO_PUEDES_LLEVARLO = "NO PUEDES LLEVARLO"
    NECESITO_MAS_INFORMACION = "NECESITO MÁS INFORMACIÓN"

class ItemCheckInput(BaseModel):
    session_token: str
    item_description: str
    airline: Optional[str] = None
    destination: str
