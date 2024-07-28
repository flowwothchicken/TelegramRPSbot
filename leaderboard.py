class Leaderboard:
    __slots__ = ("stats", "chat_id")

    def __init__(self, stats: dict, chat_id: str) -> None:
        self.stats = stats
        self.chat_id = chat_id

    def to_dict(self):
        return {"stats" : self.stats, "chat_id" : self.chat_id}
    
