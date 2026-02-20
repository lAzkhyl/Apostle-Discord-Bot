import discord
from config import config
from modules.vouch.db import vouch_db
from modules.vouch.views.modals import RedeemModal
from modules.vouch.views.manage_view import ManageVouchView
from modules.vouch.views.helpers import send_log
from modules.profile.service import ProfileService
from modules.profile.views import ProfileConfirmPostView
from utils.id_generator import IDGenerator


class VouchView(discord.ui.View):

    def __init__(self, can_generate: bool, can_redeem: bool):
        super().__init__(timeout=None)

        if can_generate:
            btn_generate = discord.ui.Button(
                label="Generate Vouch",
                style=discord.ButtonStyle.primary,
                custom_id="vouch_btn_generate",
                emoji="🎫",
                row=0,
            )
            btn_generate.callback = self._generate_callback
            self.add_item(btn_generate)

            btn_manage = discord.ui.Button(
                label="Manage / Revoke",
                style=discord.ButtonStyle.secondary,
                custom_id="vouch_btn_manage",
                emoji="📋",
                row=0,
            )
            btn_manage.callback = self._manage_callback
            self.add_item(btn_manage)

        if can_redeem:
            btn_redeem = discord.ui.Button(
                label="Redeem Vouch",
                style=discord.ButtonStyle.success,
                custom_id="vouch_btn_redeem",
                emoji="🎟️",
                row=1,
            )
            btn_redeem.callback = self._redeem_callback
            self.add_item(btn_redeem)

        btn_profile = discord.ui.Button(
            label="My Profile",
            style=discord.ButtonStyle.secondary,
            custom_id="vouch_btn_profile",
            emoji="👤",
            row=1,
        )
        btn_profile.callback = self._profile_callback
        self.add_item(btn_profile)


    async def _profile_callback(
        self,
        interaction: discord.Interaction,
    ):

        preview_embed = await ProfileService.build_embed(
            interaction.user,
            interaction.guild,
        )

        confirm_embed = discord.Embed(
            title="📢  Post Profile to Channel?",
            description=(
                "Your profile preview will look like the one below.\n"
                "Click **Post to Channel** to publish it."
            ),
            color=discord.Color.blurple(),
        )

        await interaction.response.send_message(
            embeds=[confirm_embed, preview_embed],
            view=ProfileConfirmPostView(target=interaction.user),
            ephemeral=True,
        )

    async def _generate_callback(
        self,
        interaction: discord.Interaction,
    ):
        from modules.profile.service import ProfileService

        vouch_tier = ProfileService.get_vouch_tier(interaction.user)

        if vouch_tier is None:
            await interaction.response.send_message(
                content="⛔ You do not have a tier that can generate a vouch code.",
                ephemeral=True,
            )
            return

        cooldown_minutes = vouch_tier["cooldown"]
        rep_value        = vouch_tier["rep"]
        tier_name        = vouch_tier["tier_name"]
        embed_color      = vouch_tier["color"]

        can_gen = await vouch_db.can_generate(
            interaction.user.id, cooldown_minutes
        )
        if not can_gen:
            await interaction.response.send_message(
                content=(
                    f"⏳ You are currently in cooldown.\n"
                    f"Tier **{tier_name}** only allows generating "
                    f"**1 code every {cooldown_minutes} minutes**."
                ),
                ephemeral=True,
            )
            return

        user_role_ids = {role.id for role in interaction.user.roles}

        role_to_grant_id = None
        for role_id in config.MEMBER_ROLES:
            if role_id in user_role_ids:
                role_to_grant_id = role_id
                break

        if not role_to_grant_id:
            for role_id in config.FRIENDS_ROLES:
                if role_id in user_role_ids:
                    role_to_grant_id = role_id
                    break

        if not role_to_grant_id:
            if config.MEMBER_ROLES:
                role_to_grant_id = config.MEMBER_ROLES[0]
            else:
                await interaction.response.send_message(
                    content="⚠️ Server configuration error: `ROLE_MEMBER_ID` not found in .env.",
                    ephemeral=True,
                )
                return

        new_code = IDGenerator.generate()
        await vouch_db.create_vouch(
            code=new_code,
            guild_id=interaction.guild_id,
            role_id=role_to_grant_id,
            creator_id=interaction.user.id,
            rep_value=rep_value,
        )

        role_obj = interaction.guild.get_role(role_to_grant_id)
        role_display = role_obj.name if role_obj else "Unknown Role"

        dm_embed = discord.Embed(
            title="🎫  Vouch Code Receipt",
            description="Save this code securely. **Valid for 3 days.**",
            color=embed_color,
        )
        dm_embed.add_field(name="Code",      value=f"```\n{new_code}\n```", inline=False)
        dm_embed.add_field(name="Reward",    value=role_display,            inline=True)
        dm_embed.add_field(name="Tier",      value=tier_name,               inline=True)
        dm_embed.add_field(name="Rep Grant", value=f"+{rep_value} Rep",     inline=True)

        try:
            await interaction.user.send(embed=dm_embed)
            await interaction.response.send_message(
                content="✅ Vouch code successfully created and sent to your DM.",
                ephemeral=True,
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                content=(
                    f"⚠️ **Your DM is closed!** The code below is only shown once — "
                    f"please copy it now:\n```\n{new_code}\n```"
                ),
                ephemeral=True,
            )

    async def _manage_callback(
        self,
        interaction: discord.Interaction,
    ):
        vouches = await vouch_db.get_creator_vouches(interaction.user.id)

        if not vouches:
            await interaction.response.send_message(
                content="📭 You haven't created any vouch code yet.",
                ephemeral=True,
            )
            return

        manage_embed = discord.Embed(
            title="📋  Manage Vouch Codes",
            description="Select a code from the menu below to view details or remove it.",
            color=discord.Color.dark_grey(),
        )
        await interaction.response.send_message(
            embed=manage_embed,
            view=ManageVouchView(vouches),
            ephemeral=True,
        )

    async def _redeem_callback(
        self,
        interaction: discord.Interaction,
    ):
        await interaction.response.send_modal(RedeemModal())


class SetupView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Redeem Vouch Code",
        style=discord.ButtonStyle.success,
        custom_id="setup_btn_redeem",
        emoji="🎟️",
    )
    async def setup_redeem_callback(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await interaction.response.send_modal(RedeemModal())
