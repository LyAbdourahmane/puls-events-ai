from pydantic import BaseModel, Field

# definition du model de donnée pour les questions
class QueryRequest(BaseModel):
    question : str = Field(description='Merci de mettre la question ici', max_length=500)
    model_size: str = Field(description='Choix du model Small ou Large', pattern="^(small|large)$")