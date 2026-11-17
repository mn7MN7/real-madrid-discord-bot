import discord
from discord.ext import commands, tasks
import requests
from datetime import datetime, timedelta

# 1. إعداد الصلاحيات الأساسية
intents = discord.Intents.default()
intents.message_content = True  
bot = commands.Bot(command_prefix="!", intents=intents)

# 🛑 ضع الرموز الخاصة بك هنا (أو استخدم متغيرات البيئة) 🛑
DISCORD_TOKEN = "YOUR_DISCORD_TOKEN_HERE"
FOOTBALL_API_KEY = "YOUR_FOOTBALL_API_KEY_HERE"

REAL_MADRID_ID = 86 

# قاموس الترجمة العربية
TRANSLATIONS = {
    "Primera Division": "الدوري الإسباني 🏆",
    "UEFA Champions League": "دوري أبطال أوروبا 🇪🇺",
    "Copa del Rey": "كأس ملك إسبانيا 👑",
    "Real Madrid CF": "ريال مدريد",
    "Real Oviedo": "ريال أوفييدو",
    "Sevilla FC": "إشبيلية",
    "Athletic Club": "أتلتيك بيلباو",
    "FC Barcelona": "برشلونة",
    "Atlético Madrid": "أتلتيكو مدريد",
    "Girona FC": "جيرونا",
    "Valencia CF": "فالنسيا",
    "Real Sociedad de Fútbol": "ريال سوسيداد",
    "Real Betis Balompié": "ريال بيتيس",
    "Villarreal CF": "فياريال"
}

def translate(text):
    return TRANSLATIONS.get(text, text)

# 2. التأكد من بدء تشغيل البوت
@bot.event
async def on_ready():
    print("==========================================")
    print(f"✅ البوت اشتغل بنجاح باسم: {bot.user.name}")
    print("==========================================")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Real Madrid ⚪"))
    
    # تشغيل التذكير التلقائي فوراً عند جاهزية البوت
    if not check_upcoming_matches.is_running():
        check_upcoming_matches.start()

# 3. أمر عرض المباريات يدويًا
@bot.command(name="مباريات")
async def get_matches(ctx):
    url = f"https://api.football-data.org/v4/teams/{REAL_MADRID_ID}/matches?status=SCHEDULED"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        matches = data.get("matches", [])
        
        if not matches:
            await ctx.send("لا توجد مباريات قادمة مجدولة حالياً.")
            return

        embed = discord.Embed(title="📅 مباريات ريال مدريد القادمة", color=0xF1C40F)
        for match in matches[:3]:
            home_team = translate(match["homeTeam"]["name"])
            away_team = translate(match["awayTeam"]["name"])
            competition = translate(match["competition"]["name"])
            
            utc_datetime = datetime.strptime(match["utcDate"], "%Y-%m-%dT%H:%M:%SZ")
            local_datetime = utc_datetime + timedelta(hours=3)
            time_am_pm = "مساءً" if local_datetime.strftime("%p") == "PM" else "صباحاً"
            formatted_time = local_datetime.strftime(f"%Y-%m-%d | %I:%M {time_am_pm}")

            embed.add_field(
                name=f"⚽ {home_team} ضد {away_team}",
                value=f"🏆 **البطولة:** {competition}\n⏰ **التوقيت:** {formatted_time}",
                inline=False
            )
        await ctx.send(embed=embed)
    except Exception as e:
        print(f"❌ خطأ في أمر مباريات: {e}")
        await ctx.send("حدث خطأ أثناء جلب البيانات.")

# 4. مهمة التذكير التلقائي (تعمل كل ساعة خلف الكواليس)
@tasks.loop(hours=1)
async def check_upcoming_matches():
    url = f"https://api.football-data.org/v4/teams/{REAL_MADRID_ID}/matches?status=SCHEDULED"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        matches = data.get("matches", [])
        
        if matches:
            next_match = matches[0]
            utc_datetime = datetime.strptime(next_match["utcDate"], "%Y-%m-%dT%H:%M:%SZ")
            local_datetime = utc_datetime + timedelta(hours=3)
            now = datetime.now()
            
            time_difference = local_datetime - now
            
            # إذا كانت المباراة اليوم (متبقي أقل من 12 ساعة)
            if timedelta(hours=0) < time_difference <= timedelta(hours=12):
                home_team = translate(next_match["homeTeam"]["name"])
                away_team = translate(next_match["awayTeam"]["name"])
                competition = translate(next_match["competition"]["name"])
                
                for guild in bot.guilds:
                    for channel in guild.text_channels:
                        if channel.permissions_for(guild.me).send_messages:
                            embed = discord.Embed(
                                title="🔔 تذكير تلقائي: يوم المباراة! ⚽",
                                description=f"اليوم سيلعب نادي **ريال مدريد** مباراة قادمة!\n\n"
                                            f"⚔️ **المواجهة:** {home_team} ضد {away_team}\n"
                                            f"🏆 **البطولة:** {competition}\n"
                                            f"⏰ **التوقيت:** {local_datetime.strftime('%I:%M %p')}\n\n"
                                            f"كونوا في الموعد لمؤازرة الملكي! ⚪🔥",
                                color=0xE74C3C
                            )
                            await channel.send(embed=embed)
                            print(f"📢 تم إرسال تذكير تلقائي في سيرفر: {guild.name}")
                            break
                    break
    except Exception as e:
        print(f"❌ خطأ في مهمة التذكير التلقائي: {e}")

# تشغيل البوت
bot.run(DISCORD_TOKEN)