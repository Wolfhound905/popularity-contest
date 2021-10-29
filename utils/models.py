class Star:
    def __init__(self, star_dict:dict, msg_id:int):
        self.__message_id = msg_id
        self.star_id = star_dict['star_id']
        self.message_id = star_dict['message_id']
        self.guild_id = star_dict['guild_id']
        self.author_id = star_dict['author_id']
        self.star_count = star_dict['star_count']
        self.type = self.getType()
        """ 0 = Starred Msg | 1 = Starboard Msg"""
    
    def getType(self):
        if self.__message_id == self.message_id:
            return 0
        elif self.__message_id == self.star_id:
            return 1