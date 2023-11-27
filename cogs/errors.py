import disnake
from disnake import NotFound
from disnake.ext import commands
from disnake.ext.commands import CommandInvokeError
import Logger

logger = Logger.Logger()


class Errors(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_slash_command_error")
    async def slash_command_error(self, inter: disnake.ApplicationCommandInteraction, error: Exception):
        if isinstance(error,  CommandInvokeError or NotFound):
            try:
                # print(CommandInvokeError.args or NotFound.args)
                logger.error(error)
                await inter.send("Всё что нам известно, так это то, что не удалось выполнить команду.\nВероятно это сбой сети, попробуй ввести команду/нажать на кнопку ещё раз", ephemeral=True)
            except:
                logger.error(error)
        else:
            logger.error(error)


def setup(bot):
    bot.add_cog(Errors(bot))
