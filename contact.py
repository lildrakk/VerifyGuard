import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import datetime
import pytz

from cogs.premium import is_premium, embed_premium_required

CONFIG_FILE = "contactar_config.json"
COLOR = discord.Color(0x0A3D62)

# ============================================================
# HORA ESPAÑOLA
# ============================================================

def hora_espanola():
    tz = pytz.timezone("Europe/Madrid")
    return int(datetime.datetime.now(tz).timestamp())

# ============================================================
# JSON CONFIG
# ============================================================

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump({}, f)
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

config = load_config()

# ============================================================
# CONFIGURACIÓN DEL SISTEMA
# ============================================================

class ContactarConfig(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="contactar_config",
        description="Configurar el canal y hasta 4 roles de staff para el sistema de contacto premium."
    )
    @commands.has_permissions(administrator=True)
    async def contactar_config(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel,
        rol1: discord.Role,
        rol2: discord.Role = None,
        rol3: discord.Role = None,
        rol4: discord.Role = None
    ):

        roles = [r.id for r in [rol1, rol2, rol3, rol4] if r is not None]

        if len(roles) == 0:
            return await interaction.response.send_message(
                "❌ Debes configurar al menos **1 rol de staff**.",
                ephemeral=True
            )

        config[str(interaction.guild.id)] = {
            "canal": canal.id,
            "roles": roles
        }

        save_config(config)

        roles_txt = " ".join([f"<@&{r}>" for r in roles])

        await interaction.response.send_message(
            f"✔ Configuración guardada.\nCanal: {canal.mention}\nRoles: {roles_txt}",
            ephemeral=True
        )

# ============================================================
# MODAL DE RESPUESTA
# ============================================================

class ResponderModal(discord.ui.Modal, title="Responder al usuario"):
    def __init__(self, usuario, motivo, hora_solicitud):
        super().__init__()
        self.usuario = usuario
        self.motivo = motivo
        self.hora_solicitud = hora_solicitud

        self.respuesta = discord.ui.TextInput(
            label="Respuesta del staff",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )
        self.add_item(self.respuesta)

    async def on_submit(self, interaction: discord.Interaction):

        hora_respuesta = hora_espanola()

        embed_user = discord.Embed(
            title="📩 El staff te respondió",
            color=COLOR
        )
        embed_user.add_field(name="Usuario:", value=f"{self.usuario} (`{self.usuario.id}`)", inline=False)
        embed_user.add_field(name="Staff que respondió:", value=f"{interaction.user} (`{interaction.user.id}`)", inline=False)
        embed_user.add_field(name="Motivo:", value=self.motivo, inline=False)
        embed_user.add_field(name="Respuesta:", value=self.respuesta.value, inline=False)
        embed_user.add_field(name="Hora de solicitud:", value=f"<t:{self.hora_solicitud}:F>", inline=False)
        embed_user.add_field(name="Hora de respuesta:", value=f"<t:{hora_respuesta}:F>", inline=False)
        embed_user.set_footer(text="Si tienes más dudas, usa /contactar_staff")

        try:
            await self.usuario.send(embed=embed_user)
        except:
            pass

        await interaction.response.send_message("✔ Respuesta enviada al usuario.", ephemeral=True)

# ============================================================
# BOTÓN DE RESPUESTA
# ============================================================

class ResponderButton(discord.ui.View):
    def __init__(self, usuario, motivo, hora_solicitud):
        super().__init__(timeout=None)
        self.usuario = usuario
        self.motivo = motivo
        self.hora_solicitud = hora_solicitud

    @discord.ui.button(label="Responder", style=discord.ButtonStyle.green, emoji="💬")
    async def responder(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            ResponderModal(self.usuario, self.motivo, self.hora_solicitud)
        )

# ============================================================
# COMANDO PREMIUM /contactar_staff
# ============================================================

class ContactarStaff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="contactar_staff",
        description="Enviar una consulta directamente al staff (Premium)."
    )
    async def contactar_staff(self, interaction: discord.Interaction, motivo: str):

        if not is_premium(interaction.user.id):
            return await interaction.response.send_message(
                embed=embed_premium_required(),
                ephemeral=True
            )

        guild_id = str(interaction.guild.id)

        if guild_id not in config:
            return await interaction.response.send_message(
                "❌ El sistema no está configurado. Usa /contactar_config",
                ephemeral=True
            )

        canal_id = config[guild_id]["canal"]
        roles = config[guild_id]["roles"]

        canal = interaction.guild.get_channel(canal_id)
        if not canal:
            return await interaction.response.send_message("❌ El canal configurado no existe.", ephemeral=True)

        hora_solicitud = hora_espanola()

        embed = discord.Embed(
            title="📨 Nueva solicitud de usuario premium",
            color=COLOR
        )
        embed.add_field(name="Usuario:", value=f"{interaction.user} (`{interaction.user.id}`)", inline=False)
        embed.add_field(name="Hora:", value=f"<t:{hora_solicitud}:F>", inline=False)
        embed.add_field(name="Motivo:", value=motivo, inline=False)

        menciones = " ".join([f"<@&{r}>" for r in roles])

        await canal.send(
            content=menciones,
            embed=embed,
            view=ResponderButton(interaction.user, motivo, hora_solicitud)
        )

        await interaction.response.send_message(
            "✔ Tu solicitud ha sido enviada al staff. Te responderán por DM.",
            ephemeral=True
        )

# ============================================================
# SETUP
# ============================================================

async def setup(bot):
    await bot.add_cog(ContactarConfig(bot))
    await bot.add_cog(ContactarStaff(bot))
