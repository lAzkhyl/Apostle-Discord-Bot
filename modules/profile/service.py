import discord
from config import config
from modules.vouch.db import vouch_db

ROLE_HIERARCHY = [
    ("OWNER_ROLES",    "Owner"),
    ("MOD_ROLES",      "Mod"),
    ("ALLSTARS_ROLES", "All Stars"),
    ("KAISER_ROLES",   "Kaiser"),
    ("WARLORD_ROLES",  "Warlord"),
    ("MEMBER_ROLES",   "Member"),
    ("FRIENDS_ROLES",  "Friends"),
    ("VISITORS_ROLES", "Visitors"),
]

TIER_COLORS = {
    "Owner":     0xFFFFFF,
    "Mod":       0x00FFFF,
    "All Stars": 0x800000,
    "Kaiser":    0x3498DB,
    "Warlord":   0xE67E22,
    "Member":    0x2ECC71,
    "Friends":   0x9B59B6,
    "Visitors":  0x95A5A6,
}

TIER_VOUCH_CONFIG = {
    "Owner":     {"cooldown": 0,   "rep": 50},
    "Mod":       {"cooldown": 0,   "rep": 20},
    "All Stars": {"cooldown": 10,  "rep": 10},
    "Kaiser":    {"cooldown": 60,  "rep": 5},
    "Warlord":   {"cooldown": 60,  "rep": 5},
}


class ProfileService:

    @staticmethod
    def get_main_role(member: discord.Member) -> str:
        user_role_ids = {role.id for role in member.roles}

        for config_attr, tier_name in ROLE_HIERARCHY:
            role_id_list = getattr(config, config_attr, [])
            if any(role_id in user_role_ids for role_id in role_id_list):
                return tier_name

        return "Visitors"

    @staticmethod
    def get_vouch_tier(member: discord.Member) -> dict | None:
        user_role_ids = {role.id for role in member.roles}

        for config_attr, tier_name in ROLE_HIERARCHY:
            if tier_name not in TIER_VOUCH_CONFIG:
                continue
            role_id_list = getattr(config, config_attr, [])
            if any(role_id in user_role_ids for role_id in role_id_list):
                return {
                    "tier_name": tier_name,
                    **TIER_VOUCH_CONFIG[tier_name],
                    "color": TIER_COLORS.get(tier_name, 0x95A5A6),
                }

        return None

    @staticmethod
    async def build_embed(
        target: discord.Member,
        guild: discord.Guild,
    ) -> discord.Embed:
        profile_row = await vouch_db.get_user_profile(target.id)
        reputation = profile_row[0] if profile_row else 0
        voucher_id = profile_row[1] if profile_row else None

        main_role = ProfileService.get_main_role(target)
        embed_color = TIER_COLORS.get(main_role, 0x95A5A6)

        embed = discord.Embed(color=embed_color)

        embed.set_author(
            name=target.display_name,
            icon_url=target.display_avatar.url if target.display_avatar else None,
        )

        if target.display_avatar:
            embed.set_thumbnail(url=target.display_avatar.url)

        embed.add_field(
            name="⭐  Reputation",
            value=f"**{reputation}** Points",
            inline=False,
        )

        vouched_by_text = "_Original / No Record_"
        if voucher_id:
            voucher_member = guild.get_member(voucher_id)
            if voucher_member:
                voucher_main_role = ProfileService.get_main_role(voucher_member)
                vouched_by_text = (
                    f"**{voucher_member.display_name}** "
                    f"(@{voucher_main_role})"
                )
            else:
                vouched_by_text = f"<@{voucher_id}> *(Left Server)*"

        embed.add_field(
            name="🔖  Vouched By",
            value=vouched_by_text,
            inline=False,
        )

        embed.add_field(
            name="👑  Main Role",
            value=f"**{main_role}**",
            inline=True,
        )

        join_date_text = (
            target.joined_at.strftime("%Y-%m-%d")
            if target.joined_at
            else "_Unknown_"
        )
        embed.add_field(
            name="📅  Join Date",
            value=join_date_text,
            inline=True,
        )

        embed.set_footer(text="Click 'Extended Info' to reveal more details.")

        return embed

    @staticmethod
    def build_extended_embed(target: discord.Member) -> discord.Embed:
        embed = discord.Embed(
            title="🔐  Extended Profile — Private View",
            description=(
                "This information is only visible to you.\n"
                "The public profile message has not been changed."
            ),
            color=0x2C2F33,
        )
        embed.set_thumbnail(
            url=target.display_avatar.url if target.display_avatar else None
        )

        embed.add_field(
            name="Display Name",
            value=target.display_name,
            inline=True,
        )
        embed.add_field(
            name="Username",
            value=f"@{target.name}",
            inline=True,
        )
        embed.add_field(
            name="User ID",
            value=f"`{target.id}`",
            inline=False,
        )

        full_join_date = (
            target.joined_at.strftime("%A, %d %B %Y — %H:%M:%S UTC")
            if target.joined_at
            else "Unknown"
        )
        account_created = target.created_at.strftime(
            "%A, %d %B %Y — %H:%M:%S UTC"
        )

        embed.add_field(
            name="📅  Server Join Date",
            value=full_join_date,
            inline=False,
        )
        embed.add_field(
            name="🗓️  Account Created",
            value=account_created,
            inline=False,
        )

        roles_to_hide = set(
            config.MEMBER_ROLES
            + config.FRIENDS_ROLES
            + config.VISITORS_ROLES
            + config.IGNORED_ROLES
        )

        display_roles = [
            role.mention
            for role in reversed(target.roles)
            if role.name != "@everyone" and role.id not in roles_to_hide
        ]

        roles_display = " ".join(display_roles) if display_roles else "_No notable roles_"
        embed.add_field(
            name="🏷️  Roles",
            value=roles_display,
            inline=False,
        )

        return embed
