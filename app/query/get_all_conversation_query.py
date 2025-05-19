

from app.utils.pagination import Pagination


class GetAllConversationQuery:
    def __init__(self, pagination: Pagination):
        self.pagination = pagination
        self.from_user_id = None
        self.to_user_id = None
        self.type = None
    
