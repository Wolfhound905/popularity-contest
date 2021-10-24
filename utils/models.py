# star_dict = {'star_id': '901950210912182302', 'message_id': '901948837315371058', 'author_id': '591899182793621527', 'star_count': 3}
class Star:
    def __init__(self, star_dict):
        self.star_id = star_dict['star_id']
        self.message_id = star_dict['message_id']
        self.guild_id = star_dict['guild_id']
        self.author_id = star_dict['author_id']
        self.star_count = star_dict['star_count']
