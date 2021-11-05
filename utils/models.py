class Star:
    def __init__(self, star_dict: dict, star_channel_id: int, msg_id: int):
        self.__message_id = msg_id
        self.star_id = star_dict["star_id"]
        self.message_id = star_dict["message_id"]
        self.guild_id = star_dict["guild_id"]
        self.author_id = star_dict["author_id"]
        self.star_count = star_dict["star_count"]
        self.msg_channel_id = star_dict["message_channel_id"]
        self.star_channel_id = star_channel_id
        self.type = self.getType()
        self.msg_jump_url = f"https://discordapp.com/channels/{self.guild_id}/{self.msg_channel_id}/{self.message_id}"
        self.star_jump_url = f"https://discordapp.com/channels/{self.guild_id}/{self.star_channel_id}/{self.star_id}"
        """ 0 = Starred Msg | 1 = Starboard Msg"""

    def getType(self):
        if self.__message_id == self.message_id:
            return 0
        elif self.__message_id == self.star_id:
            return 1


class MostPopular:
    class Person:
        def __init__(self, person_dict: dict):
            self.id = person_dict["id"]
            self.name = person_dict["name"]
            self.count = person_dict["count"]
