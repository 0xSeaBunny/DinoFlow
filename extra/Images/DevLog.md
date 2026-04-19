# v1.0.2:

**- Chat History:** Some models were having issues understanding that the chat history is just context, and not 
the actual prompt at hand. My main idea to fix this is to make the raw chat history something the model can pull 
when needed through a tool, meanwhile only the last 3 messages will be sent every message.

**- Sprites For The Model's State:** I thought adding a little character to show when your model is thinking, just responded, you are AFK, and so on would be a nice way to liven up the program. Might turn this into a tamagotchi esc thing where it gets feed off of prompts, becomes happy from using tools, etc 
