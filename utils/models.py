class Star:
    def __init__(self, star_dict):
        self.star_id = star_dict['star_id']
        self.message_id = star_dict['message_id']
        self.guild_id = star_dict['guild_id']
        self.author_id = star_dict['author_id']
        self.star_count = star_dict['star_count']
