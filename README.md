# DinoFlow 

**DinoFlow** is an open source python based program that is meant to allow anyone to easily turn local Ollama models into autonomous agents complete with memory and great tools. The goal is to take away the price point and confusing nature of OpenClaw / HermesAgent while still providing a useful agent for your computer. 

# -> How To Install/Use :
<details>
  <summary><b>How To Install DinoFlow📥</b></summary>
  
  - 1: Install Python: https://www.python.org/
  - 2: Install Ollama: https://ollama.com/download
  - 3: Download **DinoFlow.zip** from the releases tab in this repo
  - 4: Run **Setup.py** once to install any missing Python Libs
  - 5: Launch **DinoFlow.py**, and you are ready to start using it!
</details>

<details>
  <summary><b>Required Python Libs🐍</b></summary>

  Use the *setup.py* file in the root of *DinoFlow.py* to quickly see what you already have out of the following, and install the missing ones.
  
  - Python
  - selenium
  - webdriver-manager
  - pyautogui
  - discord.py
  - python-telegram-bot
  - requests
</details>

<details>
  <summary><b>How To Setup Agent🤖</b></summary>

  ## Installing An Ollama Model
  - 1: Head over to the **Manage Models** tab
  - 2: Go into the *Download Model* sub tab
  - 3: Paste the name of whatever Ollama model you want to download in the input box
  - 4: Press the *install* button, and wait for it to finish installing.
  
  ## Setting Up A DinoFlow Agent:
  - 5: Head over to the **Agents** tab.
  - 6: Name your agent what ever you want.
  - 7: Select what ollama model of yours, you want to run as this agent.
  - 8: Give it a system prompt based on what it will be doing for you.
  - 9: Select what tools it will have access to
  - 10: Hit the save button in the top right corner, and now your agent will be ready to use!
  ----------------------------------
  
   - You can start usng your agent by select it in the *Agent:* drop down box in the Chat tab
   - You can edit your already made agents at any time in the **Agents** tab
</details>

# -> Features 📰:

<details>
  <summary><b>Main Features 🦎</b></summary>
  
  - **🤖Agents:**Agents act as profiles, where you can save an agent name, the model it uses, and a custom system prompt as an "agent", It's "Minions", it's "Databases", and the tools it has access to. This system allows you to create agents for specific situations, while also allowing you to easily swap between them.

  - **:clock130:Tasks:** Tasks are prompts that will be automatically sent to your agent. You can set them to be sent one or repeat, alongside picking if you want the timer on it to go off at a specific time, or just wait in minutes 
  
  - **:school:Learns over time:** DinoFlow allows your models to learn from their actions so they can handle tasks they have seen before better. The most commonly used things in memory will never get phased out, while memories that don't get used as often slowly fade out over time. 

  - **:file_folder: Databases:** Give your agents direct file paths to specific folders/files so they can easily call upon them without you giving the path each time/the agent saving having to figure it out. 

  - **🧰Pre built tools for your models to use:** Various pre built tools that allow your model to do what ever you wish on your computer.

  - **:motorway: Browser Sandbox:** Models running in DinoFlow will only have access to open browsers up through selenium / selenium's chromium browser, keeping them in a sand box of sorts when exploring the web, while also allowing them to clearly figure out whats on a website at the same time.

  - **↕️Save/Load Conversations:** You can save conversations with any model, and then be able to load that back up at anytime. The saved conversations will only update when you hit the save button, allowing you easily walk back mistakes.

  - **🖥️Remote Chats:** Alongside letting you talk to your agent/model directly in DinoFlow, you can also talk to your agent with full features through the following remote options: Telegram, Discord

  - **:inbox_tray:Download / Manage models directly in the main program:** The main program for DinoFlow has a built in option that allows you to delete models, and download new models *only* using their model names. This includes a button to open ollama's model library, so you can quickly and safely find new models

  - **:1234:Context Calculator:** See how much context you are taking up, and exactly what is taking up that context, allowing you ensure your prompts hit the mark.
</details>

<details>
  <summary><b>Remote Chat Options🖥️</b></summary>
  
  - 1: Telegram Bot
  - 2: Discord Bot
</details>

<details>
  <summary><b>Pre Built Model Tools🧰</b></summary>
  
   > - **System Tools:**
   > 
   > - 1: Get system info
   > - 2: Get Current Time
   > - 3: List Processes
   > - 4: Start Process
   > - 5: Run Shell Command
   > - 6: Run Python Code
  ----------------------------------
   > - **General Tools:**
   > 
   > - 1: Take Screenshot
   > - 2: Save To Memory
   > - 3: Toggle Task
   > - 4: Create Task
  ----------------------------------
   > - **Browser Tools(selenium):**
   > 
   > - 1: Launch Browser
   > - 2: Navigate To
   > - 3: Get Page Text
   > - 4: Click Element
   > - 5: Find Element
   > - 6: Scroll Page
   > - 7: Close Browser
  ----------------------------------
   > - **File/Folder Tools:**
   > 
   > - 1: Read File
   > - 2: Write File
   > - 3: Delete File
   > - 4: List Directory
   > - 5: Search Files
   > - 6: Create Folders
   > - 7: Move File
   > - 8: Copy File
  ----------------------------------
   > - **Input Tools:**
   > 
   > - 1: Type Text
   > - 2: Press Key
   > - 3: Get Mouse Position
   > - 4: Move Mouse
   > - 5: Click Mouse
</details>

# FAQ ❓:

> **- Q: Why is DinoFlow built in python?**
> 
> - A: To ensure it can automatically work on multiple OSs, while also keeping it in a state that allows anyone to easily tweak it on their own. 

> **- Q: Why no support for claude/other cloud model?**
> 
> - A: DinoFlow is only meant to work with 100% local models, with it's main goal being to provide the openclaw/hermes agent experience to the best degree for free. If you want use a Cloud/API/Key based model, there are other options outside of DinoFlow that are better suited for those types of models. 

> **- Q: Why can it only access a browser through selenium by default?**
> 
> - A: This is to ensure that the model you are running, can't have access to important information, logins, etc from the get go as local models are bound to make mistakes. If you want to use your default browser, ask your model to make a tool to do just that, ensure it saves that to memory, and you will be good to go.
