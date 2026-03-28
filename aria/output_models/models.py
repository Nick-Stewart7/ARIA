from pydantic import BaseModel, Field

class Memory_Output(BaseModel):
    # list of memories to output
    memories: list[str] = Field(description = "A list of structured memory strings.")
