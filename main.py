import os
import signal
import Logger
import disnake
from disnake.ext import commands
import config

logger = Logger.Logger()

intents = disnake.Intents.default()
intents.guilds = True
intents.members = True
intents.dm_messages = True
bot = commands.Bot(command_prefix=commands.when_mentioned, intents=intents, owner_id=1126269277293510699, chunk_guilds_at_startup=False)


@bot.listen("on_connect")
async def podkluchilsya():
    await bot.wait_until_ready()
    logger.warning("Бот подключен к API!")


@bot.listen("on_disconnect")
async def otklyuchilsya():
    logger.warning("Бот отключился от API!")


@bot.listen("on_resumed")
async def prodoljil():
    logger.warning("Бот переподключился к API!")


@bot.command()
async def reload(ctx, cog: str = None):
    if ctx.author.id == 1126269277293510699:
        if cog is None:
            for filename in os.listdir("./cogs"):
                if filename.endswith(".py"):
                    try:
                        bot.reload_extension(f"cogs.{filename[:-3]}")
                    except:
                        pass
            await ctx.send("Все модули перезагружены!", delete_after=10)
        else:
            try:
                bot.reload_extension(f"cogs.{cog}")
            except:
                pass
            await ctx.send(f"Модуль {cog} перезагружен!", delete_after=10)
        await ctx.message.delete()
    else:
        await ctx.message.delete()


@bot.command()
async def ds(ctx):
    if ctx.author.id != 1126269277293510699:
        pass
    else:
        await ctx.message.delete()
        await bot.close()
        os.kill(os.getpid(), signal.SIGINT)


@bot.listen("on_ready")
async def zapustilsya():
    await bot.wait_until_ready()
    logger.info(f"{bot.user} запущен!")


bot.remove_command("help")


def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            bot.load_extension(f"cogs.{filename[:-3]}")
            logger.info(f"Загрузил: {filename}")


load_extensions()
bot.run(config.config['token'])
