import discord
from config import config


async def send_log(guild: discord.Guild, embed: discord.Embed) -> None:
    if not config.VOUCH_LOG_CHANNEL_ID:
        return

    log_channel = guild.get_channel(config.VOUCH_LOG_CHANNEL_ID)
    if log_channel is None:
        return

    try:
        await log_channel.send(embed=embed)
    except discord.Forbidden:
        pass


def build_error_embed(title: str, description: str) -> discord.Embed:
    return discord.Embed(
        title=f"❌  {title}",
        description=description,
        color=discord.Color.red(),
    )


def build_success_embed(title: str, description: str) -> discord.Embed:
    return discord.Embed(
        title=f"✅  {title}",
        description=description,
        color=discord.Color.green(),
    )
