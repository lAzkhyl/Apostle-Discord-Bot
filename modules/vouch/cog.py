import discord
import asyncio
from discord import app_commands
from discord.ext import commands

from config import config
from modules.vouch.db import vouch_db
from modules.vouch.views import VouchView, SetupView, send_log
from modules.vouch.views.first_time_view import FirstTimeRedeemView
from modules.profile.service import ProfileService
from utils.id_generator import IDGenerator


class VouchCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        await vouch_db.setup()

        self.bot.add_view(SetupView())
        self.bot.add_view(FirstTimeRedeemView())

    @app_commands.command(
        name="vouch",
        description="Open the Vouch system menu",
    )
    @app_commands.guild_only()
    async def vouch_base(self, interaction: discord.Interaction):

        loading_emoji = "<a:discord_loading:1474248558776549427>"
        await interaction.response.send_message(
            content=f"{loading_emoji} **Establishing secure connection...**",
            ephemeral=True,
        )
        await asyncio.sleep(0.6)
        await interaction.edit_original_response(
            content=f"{loading_emoji} **Verifying credentials...**"
        )
        await asyncio.sleep(0.6)

        user_role_ids = {role.id for role in interaction.user.roles}
        has_member  = any(r_id in user_role_ids for r_id in config.MEMBER_ROLES)
        has_friends = any(r_id in user_role_ids for r_id in config.FRIENDS_ROLES)

        if has_member and has_friends:
            conflict_embed = discord.Embed(
                title="⚠️  Role Conflict Detected",
                description=(
                    "You have both **Member** and **Friends** roles simultaneously. "
                    "This is not allowed. Please contact an admin to resolve this conflict."
                ),
                color=discord.Color.red(),
            )
            await interaction.edit_original_response(
                content=None,
                embed=conflict_embed,
            )
            return

        vouch_tier = ProfileService.get_vouch_tier(interaction.user)
        can_generate = vouch_tier is not None
        can_redeem   = not (has_member or has_friends)

        main_role  = ProfileService.get_main_role(interaction.user)
        menu_embed = discord.Embed(
            title="🔐  Two Moon Vouch System",
            description="Manage credentials and access for your members here.",
            color=discord.Color.dark_theme(),
        )
        menu_embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url
                     if interaction.user.display_avatar else None,
        )

        if can_generate and vouch_tier:
            menu_embed.set_footer(
                text=f"Detected Tier: {vouch_tier['tier_name']} · "
                     f"Cooldown: {vouch_tier['cooldown']} minutes · "
                     f"Rep per Vouch: +{vouch_tier['rep']}"
            )

        await interaction.edit_original_response(
            content=None,
            embed=menu_embed,
            view=VouchView(can_generate=can_generate, can_redeem=can_redeem),
        )


    @app_commands.command(
        name="vouch_bulk",
        description="Generate multiple vouch codes for a specific user (Owner Only)",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def vouch_bulk(
        self,
        interaction: discord.Interaction,
        target: discord.Member,
        amount: int,
        role: discord.Role,
    ):
        user_role_ids = {r.id for r in interaction.user.roles}
        is_owner = any(r_id in user_role_ids for r_id in config.OWNER_ROLES)

        if not is_owner and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                content="⛔ You do not have permission to use bulk generate.",
                ephemeral=True,
            )
            return

        if not (1 <= amount <= 20):
            await interaction.response.send_message(
                content="⚠️ Amount of codes must be between **1** and **20**.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        vouch_tier = ProfileService.get_vouch_tier(target)
        rep_value  = vouch_tier["rep"] if vouch_tier else 0

        generated_codes = []
        for _ in range(amount):
            new_code = IDGenerator.generate()
            await vouch_db.create_vouch(
                code=new_code,
                guild_id=interaction.guild_id,
                role_id=role.id,
                creator_id=target.id,
                rep_value=rep_value,
            )
            generated_codes.append(new_code)

        formatted_codes = "\n".join(f"`{code}`" for code in generated_codes)
        dm_embed = discord.Embed(
            title="🎫  Bulk Vouch Codes Received",
            description=(
                f"You have received **{amount}** vouch codes for role **{role.name}** "
                f"from the server owner.\n\n{formatted_codes}"
            ),
            color=discord.Color.gold(),
        )
        dm_embed.set_footer(text="These codes are valid for 3 days.")

        try:
            await target.send(embed=dm_embed)
            await interaction.followup.send(
                content=(
                    f"✅ Successfully created **{amount}** codes for {target.mention}. "
                    f"Codes have been sent to their DM."
                ),
                ephemeral=True,
            )
        except discord.Forbidden:
            codes_block = "\n".join(generated_codes)
            await interaction.followup.send(
                content=(
                    f"⚠️ Successfully created **{amount}** codes for {target.mention}, "
                    f"but their DM is closed.\n```\n{codes_block}\n```"
                ),
                ephemeral=True,
            )

        log_embed = discord.Embed(title="📦  Bulk Vouch Generated", color=discord.Color.purple())
        log_embed.add_field(name="Authorized By", value=interaction.user.mention, inline=True)
        log_embed.add_field(name="Code Owner",    value=target.mention,           inline=True)
        log_embed.add_field(name="Amount",        value=str(amount),              inline=True)
        log_embed.add_field(name="Role",          value=role.mention,             inline=True)
        await send_log(interaction.guild, log_embed)

    @app_commands.command(
        name="update_vouch",
        description="Change who vouched a specific user (Owner Only)",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def update_vouch(
        self,
        interaction: discord.Interaction,
        target: discord.Member,
        new_voucher: discord.Member,
    ):
        user_role_ids = {r.id for r in interaction.user.roles}
        is_owner = any(r_id in user_role_ids for r_id in config.OWNER_ROLES)

        if not is_owner and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                content="⛔ You do not have permission to use this command.",
                ephemeral=True,
            )
            return

        await vouch_db.update_voucher_manual(target.id, new_voucher.id)
        await interaction.response.send_message(
            content=(
                f"✅ Successfully updated vouch record! "
                f"{target.mention} is now vouched by {new_voucher.mention}."
            ),
            ephemeral=True,
        )

    @app_commands.command(
        name="setup",
        description="Spawn the static Vouch Redemption panel (Admin Only)",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def setup_panel(self, interaction: discord.Interaction):
        panel_embed = discord.Embed(
            title="🔐  Two Moon Identity Verification",
            description=(
                "Welcome to the server.\n\n"
                "To gain access to restricted channels, "
                "you must verify your identity using a "
                "**Vouch Code** provided by an authorized member.\n\n"
                "Click the button below to enter your code."
            ),
            color=discord.Color.dark_grey(),
        )
        panel_embed.set_footer(text="Two Moon Clan — Security System")

        await interaction.channel.send(embed=panel_embed, view=SetupView())
        await interaction.response.send_message(
            content="✅ The verification panel has been successfully spawned.",
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(VouchCog(bot))