import discord
from discord.ext import commands
from discord import app_commands
from zoneinfo import ZoneInfo
import datetime
import json
import os

from cogs.premium import is_premium, embed_premium_required

COLOR = discord.Color(0x0A3D62)
CONFIG_FILE = "contactar_config.json"


# =========================
# HORA ESPAÑOLA
# =========================

def hora_espanola() -> int:
    return int(datetime.datetime.now(ZoneInfo("Europe/Madrid")).timestamp())


# =========================
# CONFIG CONTACTAR_STAFF
# =========================

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump({}, f)
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


config = load_config()


# =========================
# VIEW: PREGUNTAR DE NUEVO (DM)
# =========================

class PreguntarDeNuevo(discord.ui.View):
    def __init__(self, guild_id: int, staff_message_id: int, motivo_original: str):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        self.staff_message_id = staff_message_id
        self.motivo_original = motivo_original

    @discord.ui.button(label="Preguntar sobre este tema", style=discord.ButtonStyle.blurple, emoji="❓")
    async def preguntar(self, interaction: discord.Interaction, button: discord.ui.Button):

        # El usuario escribe la nueva pregunta respondiendo al DM
        # Usamos el contenido del mensaje al que está respondiendo (si existe)
        nueva_pregunta = "Nueva pregunta relacionada."
        if interaction.message and interaction.message.content:
            nueva_pregunta = interaction.message.content

        bot = interaction.client
        guild = bot.get_guild(self.guild_id)
        if not guild:
            return await interaction.response.send_message(
                "❌ No se ha podido localizar el servidor para reenviar tu pregunta.",
                ephemeral=True
            )

        cfg = config.get(str(self.guild_id))
        if not cfg:
            return await interaction.response.send_message(
                "❌ El sistema de contacto ya no está configurado en este servidor.",
                ephemeral=True
            )

        canal_id = cfg.get("canal")
        roles = cfg.get("roles", [])
        canal = guild.get_channel(canal_id)

        if not canal:
            return await interaction.response.send_message(
                "❌ El canal de staff configurado ya no existe.",
                ephemeral=True
            )

        menciones = " ".join([f"<@&{r}>" for r in roles]) if roles else ""

        embed = discord.Embed(
            title="📨 Nueva pregunta relacionada",
            color=COLOR
        )
        embed.add_field(name="Usuario:", value=f"{interaction.user} (`{interaction.user.id}`)", inline=False)
        embed.add_field(name="Pregunta relacionada con:", value=self.motivo_original, inline=False)
        embed.add_field(name="Nueva pregunta:", value=nueva_pregunta, inline=False)
        embed.add_field(name="Hora:", value=f"<t:{hora_espanola()}:F>", inline=False)

        try:
            mensaje_original = await canal.fetch_message(self.staff_message_id)
        except:
            mensaje_original = None

        view = ResponderButton(interaction.user, nueva_pregunta, hora_espanola(), self.guild_id)

        await canal.send(
            content=menciones,
            embed=embed,
            reference=mensaje_original if mensaje_original else None,
            view=view
        )

        await interaction.response.send_message(
            "✔ Tu nueva pregunta ha sido enviada al staff.",
            ephemeral=True
        )


# =========================
# MODAL: RESPONDER AL USUARIO
# =========================

class ResponderModal(discord.ui.Modal, title="Responder al usuario"):
    def __init__(self, usuario: discord.User, motivo: str, hora_solicitud: int,
                 staff_message: discord.Message, guild_id: int):
        super().__init__()
        self.usuario = usuario
        self.motivo = motivo
        self.hora_solicitud = hora_solicitud
        self.staff_message = staff_message
        self.guild_id = guild_id

        self.respuesta = discord.ui.TextInput(
            label="Respuesta del staff",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )
        self.add_item(self.respuesta)

    async def on_submit(self, interaction: discord.Interaction):

        hora_respuesta = hora_espanola()

        # DM al usuario
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
        embed_user.set_footer(text="Si tienes más dudas, puedes preguntar sobre este tema.")

        try:
            await self.usuario.send(
                embed=embed_user,
                view=PreguntarDeNuevo(self.guild_id, self.staff_message.id, self.motivo)
            )
        except:
            pass

        # Editar embed del mensaje de staff para marcar como respondido
        try:
            if self.staff_message.embeds:
                embed_edit = self.staff_message.embeds[0]
                # Buscamos el campo "Estado:" (posición 5 en nuestro diseño)
                for i, field in enumerate(embed_edit.fields):
                    if field.name.startswith("Estado"):
                        embed_edit.set_field_at(i, name="Estado:", value="🟢 Respondido", inline=False)
                        break
                await self.staff_message.edit(embed=embed_edit)
        except:
            pass

        # Desactivar botón en el mensaje original
        try:
            view = self.staff_message.components[0]
            for child in view.children:
                child.disabled = True
            await self.staff_message.edit(view=view)
        except:
            pass

        await interaction.response.send_message("✔ Respuesta enviada al usuario.", ephemeral=True)


# =========================
# VIEW: BOTÓN RESPONDER (STAFF)
# =========================

class ResponderButton(discord.ui.View):
    def __init__(self, usuario: discord.User, motivo: str, hora_solicitud: int, guild_id: int):
        super().__init__(timeout=None)
        self.usuario = usuario
        self.motivo = motivo
        self.hora_solicitud = hora_solicitud
        self.guild_id = guild_id

    @discord.ui.button(label="Responder", style=discord.ButtonStyle.green, emoji="💬")
    async def responder(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            ResponderModal(
                usuario=self.usuario,
                motivo=self.motivo,
                hora_solicitud=self.hora_solicitud,
                staff_message=interaction.message,
                guild_id=self.guild_id
            )
        )


# =========================
# COG: COMANDOS PREMIUM
# =========================

class PremiumCmds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =====================
    # /contactar_staff
    # =====================
    @app_commands.command(
        name="contactar_staff",
        description="Enviar una consulta directamente al staff (Premium)."
    )
    async def contactar_staff(self, interaction: discord.Interaction, motivo: str):

        # PREMIUM
        if not is_premium(interaction.user.id):
            return await interaction.response.send_message(
                embed=embed_premium_required(),
                ephemeral=True
            )

        guild_id_str = str(interaction.guild.id)

        if guild_id_str not in config:
            return await interaction.response.send_message(
                "❌ El sistema no está configurado. Usa /contactar_config",
                ephemeral=True
            )

        canal_id = config[guild_id_str]["canal"]
        roles = config[guild_id_str]["roles"]

        canal = interaction.guild.get_channel(canal_id)
        if not canal:
            return await interaction.response.send_message("❌ El canal configurado no existe.", ephemeral=True)

        hora_solicitud = hora_espanola()

        embed = discord.Embed(
            title="📨 Nueva solicitud de usuario premium",
            color=COLOR
        )
        embed.add_field(name="Usuario:", value=f"{interaction.user} (`{interaction.user.id}`)", inline=False)
        embed.add_field(name="Servidor:", value=interaction.guild.name, inline=False)
        embed.add_field(name="Canal:", value=interaction.channel.mention, inline=False)
        embed.add_field(name="Hora:", value=f"<t:{hora_solicitud}:F>", inline=False)
        embed.add_field(name="Motivo:", value=motivo, inline=False)
        embed.add_field(name="Estado:", value="🟡 Pendiente", inline=False)

        menciones = " ".join([f"<@&{r}>" for r in roles]) if roles else ""

        view = ResponderButton(interaction.user, motivo, hora_solicitud, interaction.guild.id)

        staff_message = await canal.send(
            content=menciones,
            embed=embed,
            view=view
        )

        await interaction.response.send_message(
            "✔ Tu solicitud ha sido enviada al staff. Te responderán por DM.",
            ephemeral=True
        )

    # =====================
    # /filtrar_purge
    # =====================
    @app_commands.command(
        name="filtrar_purge",
        description="Borra mensajes aplicando filtros avanzados (Premium)."
    )
    @app_commands.describe(
        palabra="Borra mensajes que contengan esta palabra.",
        usuario="Borra mensajes enviados por este usuario.",
        imagenes="Cantidad de mensajes con imágenes a borrar.",
        links="Cantidad de mensajes con enlaces a borrar.",
        bots="Cantidad de mensajes enviados por bots a borrar.",
        horas="Borra mensajes enviados en las últimas X horas.",
        cantidad="Cantidad máxima de mensajes a analizar (por defecto 100)."
    )
    async def filtrar_purge(
        self,
        interaction: discord.Interaction,
        palabra: str = None,
        usuario: discord.User = None,
        imagenes: int = None,
        links: int = None,
        bots: int = None,
        horas: int = None,
        cantidad: int = 100
    ):

        # PREMIUM
        if not is_premium(interaction.user.id):
            return await interaction.response.send_message(
                embed=embed_premium_required(),
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        canal = interaction.channel
        mensajes_a_borrar = []

        ahora = datetime.datetime.now(ZoneInfo("Europe/Madrid"))
        limite_tiempo = None
        if horas:
            limite_tiempo = ahora - datetime.timedelta(hours=horas)

        cont_imagenes = 0
        cont_links = 0
        cont_bots = 0

        async for msg in canal.history(limit=cantidad):
            # Filtro por horas
            if limite_tiempo:
                creado = msg.created_at
                if creado.tzinfo is None:
                    creado = creado.replace(tzinfo=ZoneInfo("UTC"))
                if creado < limite_tiempo:
                    continue

            # Filtro por palabra
            if palabra and palabra.lower() in msg.content.lower():
                mensajes_a_borrar.append(msg)
                continue

            # Filtro por usuario
            if usuario and msg.author.id == usuario.id:
                mensajes_a_borrar.append(msg)
                continue

            # Filtro por imágenes
            if imagenes and cont_imagenes < imagenes and msg.attachments:
                mensajes_a_borrar.append(msg)
                cont_imagenes += 1
                continue

            # Filtro por links
            if links and cont_links < links and ("http://" in msg.content or "https://" in msg.content):
                mensajes_a_borrar.append(msg)
                cont_links += 1
                continue

            # Filtro por bots
            if bots and cont_bots < bots and msg.author.bot:
                mensajes_a_borrar.append(msg)
                cont_bots += 1
                continue

        # Borrar mensajes
        borrados = 0
        for m in mensajes_a_borrar:
            try:
                await m.delete()
                borrados += 1
            except:
                pass

        embed = discord.Embed(
            title="🧹 Purge avanzado completado",
            description=f"Se han borrado **{borrados}** mensajes usando filtros avanzados.",
            color=COLOR
        )
        embed.add_field(name="Canal:", value=canal.mention, inline=False)
        embed.add_field(name="Hora:", value=f"<t:{hora_espanola()}:F>", inline=False)

        await interaction.followup.send(embed=embed, ephemeral=True)


# =========================
# SETUP
# =========================

async def setup(bot):
    await bot.add_cog(PremiumCmds(bot))
