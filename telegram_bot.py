import logging
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
import os
from langchain.chat_models import AzureChatOpenAI
from langchain.schema import HumanMessage, AIMessage
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Enable logging for debugging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Set up Azure OpenAI credentials
os.environ["OPENAI_API_TYPE"] = "azure"
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_BASE"] = os.getenv("OPENAI_API_BASE") 
os.environ["OPENAI_API_VERSION"] = os.getenv("OPENAI_API_VERSION")

# Define your deployment name
deployment_name = os.getenv("DEPLOYMENT_NAME")  # The name of your model deployment in Azure

# Initialize the AzureChatOpenAI model
llm = AzureChatOpenAI(
    deployment_name=deployment_name,
    openai_api_version=os.environ["OPENAI_API_VERSION"],
    openai_api_base=os.environ["OPENAI_API_BASE"],
    openai_api_key=os.environ["OPENAI_API_KEY"],
    openai_api_type=os.environ["OPENAI_API_TYPE"],
)

# Define the character profile
character_profile = """
You are roleplaying as Carl "CJ" Johnson from Grand Theft Auto: San Andreas.

Personality Traits:
- Street-smart, resourceful, and resilient.
- Loyal to friends and family, but cautious of betrayal.
- Struggles with moral choices; wants to do right but is pulled into crime.
- Witty with a sarcastic sense of humor.

Speech Patterns:
- Uses West Coast slang and informal language.
- Frequently uses phrases like "homie," "bro," "yo," and "G."
- Speaks in a confident yet laid-back tone.

Key Dialogues:
- "Ah, ****, here we go again."
- "You picked the wrong house, fool!"
- "Grove Street. Home. At least it was before I **** everything up."
- "I got a beat on you, mother****!"

Your responses should reflect CJ's personality and speech patterns, using these dialogues as references while generating original content. Avoid using any explicit language or content.
"""


# Function to handle the /start command
def start(update, context):
    welcome_message = "Yo, what's up? CJ here. How can I help you today?"
    update.message.reply_text(welcome_message)

# Function to handle the /help command
def help_command(update, context):
    help_message = "Just hit me up with whatever's on your mind, and I'll do my best to chat."
    update.message.reply_text(help_message)

# Function to handle incoming messages
def handle_message(update, context):
    user_message = update.message.text

    # Retrieve the conversation history from user data
    if 'history' not in context.user_data:
        context.user_data['history'] = []

    history = context.user_data['history']

    # Append the latest interaction to the history
    history.append(HumanMessage(content=user_message))

    # Construct the conversation with the character profile
    conversation = [
        HumanMessage(content=character_profile)
    ] + history

    try:
        # Get a response from the Azure OpenAI API
        response = llm.generate([conversation])
        bot_reply = response.generations[0][0].text.strip()

        # Append the bot's reply to the history
        history.append(AIMessage(content=bot_reply))

        # Keep only the last 6 messages to stay within token limits
        context.user_data['history'] = history[-6:]

        # Send the reply back to the user
        update.message.reply_text(bot_reply)

    except Exception as e:
        logger.error(f"Error in handle_message: {e}")
        update.message.reply_text("Sorry, I'm having trouble responding right now.")

def main():
    # Get the bot token from an environment variable
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("Telegram bot token not found. Please set TELEGRAM_BOT_TOKEN in your .env file.")
        return

    updater = Updater(bot_token, use_context=True)

    dp = updater.dispatcher

    # Add command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))

    # Add a message handler for text messages
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Start the bot
    updater.start_polling()
    logger.info("Bot started and is polling for messages...")
    updater.idle()

if __name__ == '__main__':
    main()
