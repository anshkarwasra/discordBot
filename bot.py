token_for_iitr_server = "MTI2NDQ5MzU1OTQ3ODg3ODI1MA.GfbDB1.XHT4-cGqx53gsGUYVt8QJYNsV5UOR-CKtDiaYw"



import discord
import google.generativeai as genai

genai.configure(api_key='AIzaSyD7UtTiGMoQEyWy_-oPDRU1fV5wQhUeFG4')

model = genai.GenerativeModel('gemini-1.5-flash')





class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        channel = message.channel
        if (self.user!=message.author):
            if self.user in message.mentions:
                print(message.content[21:])
                response = model.generate_content(message.content[21:])
                try:
                    await channel.send(f"{message.author.mention}  {response.text}")
                except Exception as e:
                    print(e)
                    await channel.send("opps,something went wrong")

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(token_for_iitr_server)
