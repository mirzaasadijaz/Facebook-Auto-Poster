# Facebook-Auto-Poster
This repository features a powerful, automated Facebook Group Auto-Poster with a built-in Graphical User Interface (GUI). Developed in Python using Selenium, this tool is designed to streamline social media marketing by allowing users to post text and images to multiple Facebook groups automatically.

# 🚀 Project Overview
The Facebook Auto Poster automates the tedious task of manual posting. It handles the login process, navigates to specified group URLs, handles "Anonymous" posting toggles, and manages media uploads, all while incorporating human-like delays to ensure account safety.

# 📊 Key Features
User-Friendly GUI: Built with Tkinter, providing an intuitive dashboard to manage credentials, post content, and group lists.

Automated Login & Profile Management: Supports Selenium user data directories to maintain login sessions and bypass repeated multi-factor authentication.

Multi-Media Support: Ability to upload and post multiple images alongside text descriptions.

Anonymous Posting: Includes a dedicated toggle to post anonymously in groups that support the feature.

Smart Throttling: Implements random cooldown timers (45–70 seconds) between posts to mimic human behavior and avoid spam flags.

Live Logging: A real-time terminal window within the GUI that tracks the status of every post and provides instant error feedback.

Headless Mode: Option to run the browser in the background for a non-intrusive experience.

# 🛠️ Tools & Libraries
Python 3

Selenium: For browser automation and web interaction.

Tkinter: For the desktop application interface.

Pillow (PIL): For handling image processing for the GUI.

Pyperclip: For clipboard management during the posting process.
