



import discord
import google.generativeai as genai
import json
from datetime import datetime,timezone
from discord.ext import commands, tasks
import httpx,base64
import io





genai.configure(api_key='<your api key>')

model = genai.GenerativeModel('gemini-1.5-flash')


class InactivityManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_activity = {}  # To store the last activity timestamps
        self.inactivity_threshold = 172800 # Inactivity threshold in seconds (1 hour)
        self.cleanup_task.start()  # Start the background task
        self.botChannel = 1320000561474703420

    def cog_unload(self):
        self.cleanup_task.cancel()  # Stop the task when the cog is unloaded

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return  # Ignore bots

        # Update last activity time for the user
        self.last_activity[message.author.id] = datetime.now(timezone.utc)

    @tasks.loop(minutes=1)  # Run every minute
    async def cleanup_task(self):
        current_time = datetime.now(timezone.utc)
        to_remove = []

        for user_id, last_time in self.last_activity.items():
            # Calculate inactivity duration
            inactivity_duration = (current_time - last_time).total_seconds()
            if inactivity_duration > self.inactivity_threshold:
                to_remove.append(user_id)

        # Remove inactive users' instances
        for user_id in to_remove:
            del self.last_activity[user_id]
            print(f"Deleted instance for user {user_id} due to inactivity.")
            warnEmbd = discord.Embed(
                title="Inactivity for long time",
                description=f"dear {user_id} due to your inactiviy for a long time your chat instance has been removed because we dont a NASA's pc",
                color=discord.Color.red()

            )
            await self.bot.get_channel(self.botChannel).send(embed=warnEmbd)
            # Add custom cleanup logic here if needed

    @cleanup_task.before_loop
    async def before_cleanup_task(self):
        await self.bot.wait_until_ready()  # Wait until the bot is ready




class MyClient(commands.Bot):   
    def __init__(self, command_prefix, intents):
        super().__init__(command_prefix=command_prefix, intents=intents)
        self.usersInChat = {}

    def getFileExtension(self,filename):
        extension = filename.split('.')[-1]
        if extension in ['jpg', 'jpeg', 'png', 'gif','webp']:
            return f'image/{extension}'
        elif extension in ['mp4', 'avi', 'mov', 'mkv']:
            return f'video/{extension}'
        elif extension in ['mp3', 'wav', 'ogg']:
            return f'audio/{extension}'
        elif extension in ['pdf', 'doc', 'docx']:
            return f'application/{extension}'
        elif extension in ['txt', 'csv', 'json', 'xml']:
            return 'text/plain'
        else:
            return 'application/binary-stream'

    async def reset_chat(self, user_id):
        """Reset chat history for a user"""
        if user_id in self.user_chats:
            del self.user_chats[user_id]
        return self.get_or_create_chat(user_id)

    async def setup_hook(self):
        # Add the cog during bot startup
        await self.add_cog(InactivityManager(self))

    async def attachFileWithMessage(self,message,channel,user_message,fileExtension):
        async with channel.typing():
            messageEmbed = discord.Embed(
                title="File Attached",
                description=user_message,
                color=discord.Color.green()
            )
            messageEmbed.set_footer(text=f"Requested by {message.author.name}")
            await channel.send(
                f"{message.author.mention}",
                embed=messageEmbed,
                file='your file here'
            )


    async def handleAttachment(self,message,channel,user_message):
        print("process started")
        for attachment in message.attachments:
            print("im here")
            fileType = self.getFileExtension(attachment.filename)
            if fileType in ['application/pdf', 'application/doc', 'application/docx']:
                async with channel.typing():
                    doc_data = base64.standard_b64encode(httpx.get(attachment.url).content).decode("utf-8")
                    
                    response = model.generate_content([{'mime_type':fileType, 'data': doc_data},user_message])
                    response_embed = discord.Embed(
                        description=response.text,
                        color=discord.Color.green()
                    )
                    response_embed.set_footer(text=f"Requested by {message.author.name}")
                    
                    await channel.send(
                        f"{message.author.mention}",
                        embed=response_embed
                    )
                    return
            elif fileType in ['image/jpg', 'image/jpeg', 'image/png', 'image/gif','image/webp']:
                async with channel.typing():
                    image = httpx.get(attachment.url)
                    response = model.generate_content([{'mime_type':fileType, 'data': base64.b64encode(image.content).decode('utf-8')}, user_message])
                    response_embed = discord.Embed(
                        description=response.text,
                        color=discord.Color.green()
                    )
                    response_embed.set_footer(text=f"Requested by {message.author.name}")
                    await channel.send(
                        f"{message.author.mention}",
                        embed=response_embed
                    )
                    return


        

    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        # Set a custom status
        await self.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching, 
            name="for @mentions | Type @bot help"
        ))
    def creteOrStartChat(self,user_id):
        if user_id not in self.usersInChat:
            self.usersInChat[user_id] = model.start_chat()
            self.usersInChat[user_id].send_message('''whenever user demands to attach a file please respond with a custom response contatinng a json object as follows:- {
                fileName: generated,
                fileExtension: <extension-that-user-demands>,
                fileData: <content-that-user-gave-you>
            }
            NOTE:- do not anticipate the user that embed a file if he says "attach ... content in a file" then only return this json otherwise continue your behavoir as a chat bot
            ''')
        return self.usersInChat[user_id]

    def is_file_response(self, text):
        """Check if the response contains a valid file JSON structure"""
        try:
            if '{' not in text or '}' not in text:
                return False
                
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            json_str = text[start_idx:end_idx]
            
            file_data = json.loads(json_str)
            required_fields = ['fileName', 'fileExtension', 'fileData']
            
            return all(field in file_data for field in required_fields)
        except:
            return False

    async def send_file_response(self, message, channel, response_text):
        """Handle file-type responses"""
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            json_str = response_text[start_idx:end_idx]
            file_data = json.loads(json_str)
            
            # Get message text before JSON
            user_message = response_text[:start_idx].strip()
            
            # Handle file data
            if isinstance(file_data['fileData'], str):
                try:
                    file_bytes = base64.b64decode(file_data['fileData'])
                except:
                    file_bytes = file_data['fileData'].encode('utf-8')
            else:
                file_bytes = str(file_data['fileData']).encode('utf-8')

            file = discord.File(
                io.BytesIO(file_bytes),
                filename=f"{file_data['fileName']}.{file_data['fileExtension']}"
            )

            embed = discord.Embed(
                title="File Generated",
                description=user_message,
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Requested by {message.author.name}")

            await channel.send(
                f"{message.author.mention}",
                embed=embed,
                file=file
            )
            
        except Exception as e:
            print(f"Error in send_file_response: {e}")
            return False

    async def send_regular_response(self, message, channel, response_text):
        """Handle regular text responses"""
        response_embed = discord.Embed(
            description=response_text,
            color=discord.Color.green()
        )
        response_embed.set_footer(text=f"Requested by {message.author.name}")
        await channel.send(
            f"{message.author.mention}",
            embed=response_embed
        )

    async def on_message(self, message):
        if self.user == message.author:  # Ignore self messages
            return

        channel = message.channel
        error_log_channel = self.get_channel(1261997710265946182)
        
        if self.user in message.mentions:
            user_message = message.content[21:]
            
            # Handle attachments
            if message.attachments:
                await self.handleAttachment(message, channel, user_message)
                return

            # Handle help command
            tempMessage = user_message.strip()
            if tempMessage.lower()[3:] == "help":
                help_embed = discord.Embed(
                    title="Bot Help",
                    description="Here's how to use me:",
                    color=discord.Color.blue()
                )
                help_embed.add_field(
                    name="Basic Usage", 
                    value="Just mention me (@bot) followed by your question/prompt",
                    inline=False
                )
                help_embed.add_field(
                    name="Examples",
                    value="• @bot What is quantum computing?\n• @bot Write a poem about space",
                    inline=False
                )
                await channel.send(embed=help_embed)
                return

            # Handle reset command
            if tempMessage.lower()[3:] == "reset":
                await self.reset_chat(message.author.id)
                await channel.send(f"{message.author.mention} Your chat history has been reset!")
                return

            # Show typing indicator while processing
            async with channel.typing():
                try:
                    # Handle empty messages
                    if not user_message:
                        await channel.send(f"{message.author.mention} Please provide a message along with the mention!")
                        return

                    print(f"Processing request from {message.author}: {user_message}")
                    userChat = self.creteOrStartChat(message.author.id)
                    response = userChat.send_message(user_message)

                    # Check response type and handle accordingly
                    if self.is_file_response(response.text):
                        await self.send_file_response(message, channel, response.text)
                    else:
                        await self.send_regular_response(message, channel, response.text)

                except Exception as e:
                    error_data = {
                        "status": "error",
                        "message": str(e),
                        "text": "an error occurred in your genAI's backend please resolve it asap",
                        "user": str(message.author),
                        "channel": str(channel),
                        "prompt": user_message,
                        "timestamp": str(message.created_at)
                    }
                    
                    await error_log_channel.send(json.dumps(error_data, indent=2))
                    await channel.send(
                        f"{message.author.mention} Sorry, I encountered an error. Please try again later."
                    )
    
    

   



intents = discord.Intents.default()
intents.messages = True

bot = MyClient(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run('<your bot token>')