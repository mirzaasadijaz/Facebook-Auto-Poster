# Facebook Auto Poster

A desktop automation tool for posting content to multiple Facebook groups automatically, built with Python, Tkinter, and Selenium.

> **Developed by [Asad Ijaz](https://www.linkedin.com/in/asad-ijaz-data-scientist/)**

---

## Features

### Login
- **Auto Login** — enter your email and password; the tool fills and submits the form automatically, types each character with a human-like random delay to reduce bot detection
- **Manual Login** — Chrome opens the Facebook login page; you log in yourself; the tool waits and detects when the home page is reached (handles 2FA and human verification automatically)
- **Saved Sessions** — if a Chrome profile is reused, an already-logged-in session is detected and the login step is skipped entirely

### Posting
- Posts to any number of Facebook groups sequentially from a list of group IDs
- **Anonymous Posting** — toggles the "Post anonymously" switch inside the group post dialog using three fallback detection strategies
- **Background Image Mode** — selects a random Facebook background colour for text-only posts (text capped at 125 characters)
- **Image Upload** — attach one or more images (PNG, JPG, JPEG, GIF) to the post
- **Configurable Cooldown** — random delay between posts (min/max in seconds) to reduce rate-limit risk
- Post button detection uses three-pass strategy (instant scan → broad scan → short wait) to find the Post/Submit button as fast as possible

### Error Handling
- **Pattern-based error detection** after each post (rate-limit messages, server errors, "Give feedback" dialog)
- **Same-type consecutive error tracking** — only terminates if the same error type occurs 5 times in a row; different error types reset the counter
- **Group unavailable detection** — if a group page cannot be loaded (deleted, banned, restricted), the group is skipped and logged; it never counts toward the termination counter
- **Pause / Resume** — pause the run at any point between posts without losing progress; resume when ready
- **Stop** — cleanly halts the run after the current group finishes

### Logging and Results
- **Live activity log** — timestamped entries in a dark terminal-style panel, scrollable
- **Timestamped CSV file** — created at the start of every session, e.g. `fb_poster_results_20250501_143012.csv`
  - Columns: `Datetime`, `Group ID`, `Status`, `Note`
  - Status values: `Success`, `Failed`, `Skipped`
  - Note column contains the exact Facebook error text or the specific exception message
- **Export Log** — save the full activity log to a `.txt` file at any time
- **Legacy `failed_groups.txt`** — also maintained for backward compatibility

### Configuration
- **Save / Load Config** — credentials, group list, login mode, options, and cooldown settings are saved to `fb_poster_config.json` and reloaded automatically on next launch
- **Import Groups from File** — load a `.txt` file of group IDs (one per line) directly into the groups panel
- **Live counters** — success and fail chips in the header update in real time
- **Progress bar** — shows current group number and percentage

---

## Requirements

```
Python 3.10+
selenium
pyperclip
Pillow
```

Install dependencies:

```bash
pip install selenium pyperclip Pillow
```

You also need **Google Chrome** and a matching **ChromeDriver** on your system PATH.  
Download ChromeDriver: https://chromedriver.chromium.org/downloads

---

## Usage

```bash
python facebook_auto_poster.py
```

1. Select **Auto Login** or **Manual Login**
2. Enter your post text
3. Paste your group IDs (one per line) or import from a `.txt` file
4. Optionally add images or enable background / anonymous mode
5. Adjust cooldown in the **Settings** tab
6. Click **Start Posting**

Results are saved automatically to a CSV file in the same folder as the script.

---

## Project Structure

```
facebook_auto_poster.py   Main application (GUI + automation)
fb_poster_config.json     Auto-saved configuration (created on first save)
fb_poster_results_*.csv   Per-session results (created on each run)
failed_groups.txt         Legacy error log (appended on each run)
icons/
  linkedin_icon.png
  github_icon.png
  gmail_icon.png
```

---

## Version History

### v3.0 — Current
- Same-type consecutive error tracking (terminate only after 5 of the same error in a row)
- Group page unavailable check before posting (deleted/banned groups skipped, never terminate)
- "This content isn't available" removed from rate-limit patterns — handled separately
- Full error reason written to CSV Note column for every failure type
- All log messages and code comments in English

### v2.0
- Complete login rewrite: always opens `/login` first, waits for `facebook.com/` or `facebook.com/home.php`
- Handles 2FA and human verification natively in both login modes
- Pause / Resume button with interruptible cooldown
- Timestamped CSV results file per session
- Manual login mode: Chrome opens for user, tool polls until home page detected
- Group import from `.txt` file
- Export log to `.txt` file
- Save / Load configuration (JSON)

### v1.0
- Initial release with Tkinter GUI
- Selenium-based auto login and group posting
- Anonymous posting toggle with three-strategy detection
- Background image mode
- Image upload support
- Live activity log, progress bar, success/fail counters
- Configurable cooldown, scrollable left panel
- Social icon links (LinkedIn, GitHub, Gmail)

---

## Notes

- This tool automates browser actions using Selenium and a real Chrome window. It does not use any unofficial APIs.
- Facebook actively detects automation. Using realistic cooldowns (45–70 seconds minimum) and a saved Chrome profile significantly reduces the chance of being flagged.
- The tool stores your Chrome session in the User Data Dir (default: `C:\selenium_profile`). This allows the saved login to persist across runs.

---

## Author

**Asad Ijaz** — Data Scientist  
[LinkedIn](https://www.linkedin.com/in/asad-ijaz-data-scientist/) · [GitHub](https://github.com/mirzaasadijaz) · [Email](mailto:mirzaasadijaz@gmail.com)
