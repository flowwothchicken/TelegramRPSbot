class Game:
    __slots__ = ("players_values", "chat_id")

    def __init__(self, players_values: dict, chat_id: str) -> None:
        self.players_values = players_values
        self.chat_id = chat_id
    
    def __repr__(self) -> str:
        return f"chat: {self.chat_id}\ndict: {self.players_values}"