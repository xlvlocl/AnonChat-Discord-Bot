import re
import disnake
from disnake.ext import commands
from pymongo import MongoClient
import Logger
import config

logger = Logger.Logger()


class Controller(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cluster = MongoClient(config.config["database"])
        self.collection = self.cluster.AnonChat.anon
        self.search = self.cluster.AnonChat.search
        self.stats = self.cluster.AnonChat.stats
        self.guild = self.cluster.AnonChat.guilds

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.type != disnake.ChannelType.private:
            return
        if message.author.bot:
            return
        else:
            try:
                comp = self.collection.find_one({'_id': message.author.id})['comp']
                guild = self.collection.find_one({'_id': comp})['guild']
                g = await self.bot.fetch_guild(guild)
                member = await g.fetch_member(int(comp))
            except:
                comp = 0
                member = None
            if comp != 0 and member is not None:
                msg = message.content.replace(" ", "").replace("\n", "")
                discordInviteFilter = re.compile("(...)?(?:https?://)?discord(?:(?:app)?\.com/invite|\.gg)/?[a-zA-Z\d]+/?")
                lol = re.search(discordInviteFilter, msg)
                if lol:
                    return
                else:
                    pass
                msg = message.content

                if message.attachments:
                    files = [await attch.to_file() for attch in message.attachments]
                    try:
                        ref = message.reference.message_id
                    except:
                        ref = None
                    if ref is not None:
                        try:
                            comp = self.collection.find_one({'_id': message.author.id})['comp']
                            history = self.collection.find_one({'_id': comp})['history']
                        except:
                            comp = None
                            history = []
                        msg_id = None
                        for i in history:
                            if i[1] == ref:
                                msg_id = i[0]
                            else:
                                continue
                        else:
                            try:
                                id_c = self.collection.find_one({'_id': comp})['channel']
                                channel = await self.bot.fetch_channel(id_c)
                                msgg = await channel.fetch_message(msg_id)
                                msg = await msgg.reply(msg)
                            except:
                                try:
                                    history = self.collection.find_one({'_id': message.author.id})['history']
                                except:
                                    pass
                                msg_id = None
                                for i in history:
                                    if i[0] == ref:
                                        msg_id = i[1]
                                    else:
                                        continue
                                else:
                                    try:
                                        id_c = self.collection.find_one({'_id': comp})['channel']
                                        channel = await self.bot.fetch_channel(id_c)
                                        msgg = await channel.fetch_message(msg_id)
                                        msg = await msgg.reply(msg, files=files)
                                    except:
                                        try:
                                            msg = await member.send(msg, files=files)
                                        except:
                                            pass
                    else:
                        try:
                            msg = await member.send(msg, files=files)
                        except:
                            pass
                    if msg is None:
                        pass
                    else:
                        try:
                            list = self.collection.find_one({'_id': message.author.id})['history']
                        except:
                            list = []
                        try:
                            list.append([message.id, msg.id])
                            # if len(list) > 15:
                            #     list.pop(0)
                            self.collection.update_one({"_id": message.author.id}, {"$set": {'history': list}})
                        except:
                            pass
                        try:
                            messages = self.stats.find_one({'_id': message.author.id})['messages']
                            self.stats.update_one({"_id": message.author.id}, {"$set": {'messages': messages + 1}})
                        except:
                            pass

                else:
                    try:
                        ref = message.reference.message_id
                    except:
                        ref = None
                    if ref is not None:
                        try:
                            comp = self.collection.find_one({'_id': message.author.id})['comp']
                            history = self.collection.find_one({'_id': comp})['history']
                        except:
                            history = []
                            comp = None
                        msg_id = None
                        for i in history:
                            if i[1] == ref:
                                msg_id = i[0]
                            else:
                                continue
                        else:
                            try:
                                id_c = self.collection.find_one({'_id': comp})['channel']
                                channel = await self.bot.fetch_channel(id_c)
                                msgg = await channel.fetch_message(msg_id)
                                msg = await msgg.reply(msg)
                            except:
                                try:
                                    history = self.collection.find_one({'_id': message.author.id})['history']
                                except:
                                    history = []
                                msg_id = None
                                for i in history:
                                    if i[0] == ref:
                                        msg_id = i[1]
                                    else:
                                        continue
                                else:
                                    try:
                                        id_c = self.collection.find_one({'_id': comp})['channel']
                                        channel = await self.bot.fetch_channel(id_c)
                                        msgg = await channel.fetch_message(msg_id)
                                        msg = await msgg.reply(msg)
                                    except:
                                        try:
                                            msg = await member.send(msg)
                                        except:
                                            pass
                    else:
                        try:
                            msg = await member.send(msg)
                        except:
                            pass
                    if msg is None:
                        pass
                    else:
                        try:
                            list = self.collection.find_one({'_id': message.author.id})['history']
                        except:
                            list = []
                        try:
                            list.append([message.id, msg.id])
                            # if len(list) > 15:
                            #     list.pop(0)
                            self.collection.update_one({"_id": message.author.id}, {"$set": {'history': list}})
                        except:
                            pass

                        try:
                            messages = self.stats.find_one({'_id': message.author.id})['messages']
                            self.stats.update_one({"_id": message.author.id}, {"$set": {'messages': messages + 1}})
                        except:
                            pass
                try:
                    gg = self.collection.find_one({'_id': message.author.id})['guild']
                    messages = self.guild.find_one({'_id': gg})['messages']
                    self.guild.update_one({"_id": gg}, {"$set": {"messages": messages + 1}})
                except:
                    pass

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot:
            return
        if before.channel.type != disnake.ChannelType.private:
            return
        else:
            try:
                comp = self.collection.find_one({'_id': before.author.id})['comp']
                guild = self.collection.find_one({'_id': comp})['guild']
                g = await self.bot.fetch_guild(guild)
                member = await g.fetch_member(int(comp))
            except:
                comp = 0
                member = None
            if comp != 0 and member is not None:
                try:
                    comp = self.collection.find_one({'_id': before.author.id})['comp']
                    id_c = self.collection.find_one({'_id': comp})['channel']
                    channel = await self.bot.fetch_channel(id_c)
                except:
                    channel = None
                try:
                    history = self.collection.find_one({'_id': before.author.id})['history']
                except:
                    history = []
                msg_id = None
                for i in history:
                    if i[0] == before.id:
                        msg_id = i[1]
                    else:
                        continue
                if msg_id is None:
                    try:
                        await before.add_reaction("❌")
                    except:
                        pass
                else:
                    try:
                        message = await channel.fetch_message(msg_id)
                        await message.edit(f"{after.content}")
                        await before.add_reaction("✅")
                    except:
                        try:
                            await before.add_reaction("❌")
                        except:
                            pass

    @commands.Cog.listener()
    async def on_message_delete(self, before):
        if before.author.bot:
            return
        if before.channel.type != disnake.ChannelType.private:
            return
        else:
            try:
                comp = self.collection.find_one({'_id': before.author.id})['comp']
                guild = self.collection.find_one({'_id': comp})['guild']
                g = await self.bot.fetch_guild(guild)
                member = await g.fetch_member(int(comp))
            except:
                comp = 0
                member = None
            if comp != 0 and member is not None:
                comp = self.collection.find_one({'_id': before.author.id})['comp']
                id_c = self.collection.find_one({'_id': comp})['channel']
                channel = await self.bot.fetch_channel(id_c)
                history = self.collection.find_one({'_id': before.author.id})['history']
                msg_id = None
                for i in history:
                    if i[0] == before.id:
                        msg_id = i[1]
                    else:
                        continue
                if msg_id is None:
                    pass
                else:
                    message = await channel.fetch_message(msg_id)
                    await message.delete()

    @commands.Cog.listener()
    async def on_typing(self, channel, user, when):
        if user.bot:
            return
        if channel.type != disnake.ChannelType.private:
            return
        else:
            try:
                comp = self.collection.find_one({'_id': user.id})['comp']
                guild = self.collection.find_one({'_id': comp})['guild']
                g = await self.bot.fetch_guild(guild)
                member = await g.fetch_member(int(comp))
            except:
                comp = 0
                member = None
            if comp != 0 and member is not None:
                try:
                    comp = self.collection.find_one({'_id': user.id})['comp']
                    channell = self.collection.find_one({'_id': comp})['channel']
                    channel = await self.bot.fetch_channel(channell)
                    async with channel.typing():
                        pass
                except:
                    pass


def setup(bot):
    bot.add_cog(Controller(bot))
