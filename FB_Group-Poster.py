import webbrowser
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import os
import sys
import pyperclip
from PIL import Image, ImageTk

class FacebookPosterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Facebook Auto Poster - Developed by Asad Ijaz")
        self.root.geometry("900x750")
        self.root.resizable(False, False)
        
        # Variables
        self.email_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.anonymous_var = tk.BooleanVar(value=False)
        self.background_var = tk.BooleanVar(value=False)
        self.user_data_dir = tk.StringVar(value=r"C:\selenium_profile")
        self.image_paths = []
        self.groups = []
        self.is_running = False
        
        self.create_widgets()
        
    def create_widgets(self):
        # Header
        header = tk.Frame(self.root, bg="#1877f2", height=60)
        header.pack(fill=tk.X)
        
        title_label = tk.Label(header, text="Facebook Auto Poster", 
                              font=("Arial", 18, "bold"), bg="#1877f2", fg="white")
        title_label.pack(pady=10)
        
        dev_label = tk.Label(header, text="Developed by Asad Ijaz", 
                            font=("Arial", 10), bg="#1877f2", fg="white")
        dev_label.pack()
        
        # Main container
        main_frame = tk.Frame(self.root, bg="#f0f2f5")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Configuration
        left_panel = tk.LabelFrame(main_frame, text="Configuration", 
                                  font=("Arial", 11, "bold"), bg="#ffffff", padx=10, pady=10)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Email
        tk.Label(left_panel, text="Facebook Email:", bg="#ffffff").grid(row=0, column=0, sticky="w", pady=5)
        email_entry = tk.Entry(left_panel, textvariable=self.email_var, width=30)
        email_entry.grid(row=0, column=1, pady=5, padx=5)
        
        # Password
        tk.Label(left_panel, text="Password:", bg="#ffffff").grid(row=1, column=0, sticky="w", pady=5)
        password_entry = tk.Entry(left_panel, textvariable=self.password_var, width=30, show="*")
        password_entry.grid(row=1, column=1, pady=5, padx=5)
        
        # User Data Directory
        tk.Label(left_panel, text="User Data Dir:", bg="#ffffff").grid(row=2, column=0, sticky="w", pady=5)
        dir_frame = tk.Frame(left_panel, bg="#ffffff")
        dir_frame.grid(row=2, column=1, pady=5, padx=5)
        dir_entry = tk.Entry(dir_frame, textvariable=self.user_data_dir, width=22)
        dir_entry.pack(side=tk.LEFT)
        dir_btn = tk.Button(dir_frame, text="...", width=3, command=self.browse_directory)
        dir_btn.pack(side=tk.LEFT, padx=2)
        
        # Options
        options_frame = tk.LabelFrame(left_panel, text="Options", bg="#ffffff")
        options_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)
        
        anon_check = tk.Checkbutton(options_frame, text="Post Anonymously", 
                                   variable=self.anonymous_var, bg="#ffffff")
        anon_check.pack(anchor="w", padx=5, pady=2)
        
        bg_check = tk.Checkbutton(options_frame, text="Use Background Image (Max 125 chars)", 
                                 variable=self.background_var, bg="#ffffff")
        bg_check.pack(anchor="w", padx=5, pady=2)
        
        # Post Text
        tk.Label(left_panel, text="Post Text:", bg="#ffffff", font=("Arial", 10, "bold")).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(10, 5))
        
        self.post_text = scrolledtext.ScrolledText(left_panel, width=40, height=10, wrap=tk.WORD)
        self.post_text.grid(row=5, column=0, columnspan=2, pady=5, padx=5)
        
        # Image Selection
        image_frame = tk.Frame(left_panel, bg="#ffffff")
        image_frame.grid(row=6, column=0, columnspan=2, pady=5)
        
        tk.Button(image_frame, text="Add Images", command=self.add_images, 
                 bg="#1877f2", fg="white", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(image_frame, text="Clear Images", command=self.clear_images, 
                 bg="#e4e6eb", width=15).pack(side=tk.LEFT, padx=5)
        
        self.image_label = tk.Label(left_panel, text="No images selected", 
                                   bg="#ffffff", fg="#666")
        self.image_label.grid(row=7, column=0, columnspan=2, pady=5)
        
        # Right panel - Groups and Log
        right_panel = tk.Frame(main_frame, bg="#f0f2f5")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # Groups
        groups_frame = tk.LabelFrame(right_panel, text="Facebook Groups", 
                                    font=("Arial", 11, "bold"), bg="#ffffff", padx=10, pady=10)
        groups_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.groups_text = scrolledtext.ScrolledText(groups_frame, width=50, height=12, wrap=tk.WORD)
        self.groups_text.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(groups_frame, text="Enter group IDs (one per line)", 
                bg="#ffffff", fg="#666", font=("Arial", 8)).pack(pady=2)
        
        # Log
        log_frame = tk.LabelFrame(right_panel, text="Activity Log", 
                                 font=("Arial", 11, "bold"), bg="#ffffff", padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=50, height=12, 
                                                 wrap=tk.WORD, state=tk.DISABLED, bg="#f9f9f9")
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Control buttons
        button_frame = tk.Frame(self.root, bg="#f0f2f5")
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.start_btn = tk.Button(button_frame, text="Start Posting", 
                                   command=self.start_posting, bg="#42b72a", 
                                   fg="white", font=("Arial", 12, "bold"), 
                                   width=15, height=2)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(button_frame, text="Stop", 
                                 command=self.stop_posting, bg="#e4e6eb", 
                                 font=("Arial", 12, "bold"), width=15, 
                                 height=2, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(self.root, textvariable=self.status_var, 
                            bg="#e4e6eb", anchor="w", relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Configure grid weights
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
                # ====== Bottom-right Social Icons ======
        footer = tk.Frame(self.root, bg="#f0f2f5")
        footer.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-65)

        def open_link(url):
            webbrowser.open(url)

        def resource_path(relative_path):
            """ Get absolute path to resource, works for dev and for PyInstaller """
            try:
                # PyInstaller creates a temp folder and stores path in _MEIPASS
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")
            return os.path.join(base_path, relative_path)
        
        def load_icon(path):
            abs_path = resource_path(path)
            if not os.path.exists(abs_path):
                print(f"Icon not found: {abs_path}")
                # Optional: Return a blank placeholder if icon is missing
                return None
            img = Image.open(abs_path).resize((22, 22))
            return ImageTk.PhotoImage(img)

        # Load icons (keep references!)
        self.icons = {}
        self.icons["linkedin"] = load_icon("icons/linkedin_icon.png")
        self.icons["github"]   = load_icon("icons/github_icon.png")
        self.icons["gmail"]    = load_icon("icons/gmail_icon.png")

        # LinkedIn
        linkedin_lbl = tk.Label(footer, image=self.icons["linkedin"], cursor="hand2", bg="#f0f2f5")
        linkedin_lbl.pack(side="left", padx=6)
        linkedin_lbl.bind("<Button-1>", lambda e: open_link("https://www.linkedin.com/in/asad-ijaz-data-scientist/"))

        # GitHub
        github_lbl = tk.Label(footer, image=self.icons["github"], cursor="hand2", bg="#f0f2f5")
        github_lbl.pack(side="left", padx=6)
        github_lbl.bind("<Button-1>", lambda e: open_link("https://github.com/mirzaasadijaz"))

        # Gmail
        gmail_lbl = tk.Label(footer, image=self.icons["gmail"], cursor="hand2", bg="#f0f2f5")
        gmail_lbl.pack(side="left", padx=6)
        gmail_lbl.bind("<Button-1>", lambda e: open_link("https://mail.google.com/mail/?view=cm&fs=1&to=mirzaasadijaz@gmail.com"))
   
    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.user_data_dir.set(directory)
    
    def add_images(self):
        files = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif")]
        )
        if files:
            self.image_paths.extend(files)
            self.image_label.config(text=f"{len(self.image_paths)} image(s) selected")
    
    def clear_images(self):
        self.image_paths = []
        self.image_label.config(text="No images selected")
    
    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()
    
    def validate_inputs(self):
        if not self.email_var.get():
            messagebox.showerror("Error", "Please enter Facebook email")
            return False
        if not self.password_var.get():
            messagebox.showerror("Error", "Please enter Facebook password")
            return False
        if not self.post_text.get("1.0", tk.END).strip():
            messagebox.showerror("Error", "Please enter post text")
            return False
        if not self.groups_text.get("1.0", tk.END).strip():
            messagebox.showerror("Error", "Please enter at least one group ID")
            return False
        return True
    
    def start_posting(self):
        if not self.validate_inputs():
            return
        
        self.is_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("Running...")
        
        # Clear log
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # Get groups
        groups_text = self.groups_text.get("1.0", tk.END).strip()
        self.groups = [g.strip() for g in groups_text.split("\n") if g.strip()]
        
        # Start in thread
        thread = threading.Thread(target=self.run_posting, daemon=True)
        thread.start()
    
    def stop_posting(self):
        self.is_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("Stopped")
        self.log("🛑 Stopping...")
    
    def run_posting(self):
        FB_EMAIL = self.email_var.get()
        FB_PASSWORD = self.password_var.get()
        POST_ANONYMOUSLY = self.anonymous_var.get()
        USE_BACKGROUND_IMAGE = self.background_var.get()
        POST_TEXT = self.post_text.get("1.0", tk.END).strip()
        IMAGE_PATHS = self.image_paths.copy()
        USER_DATA_DIR = self.user_data_dir.get()
        
        # Validate images
        if USE_BACKGROUND_IMAGE:
            pass
        else:
            for img in IMAGE_PATHS:
                if not os.path.exists(img):
                    self.log(f"⚠️ Warning: Image not found at {img}")
        
        # Chrome Setup
        options = Options()
        options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
        options.add_argument("--disable-notifications")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        self.log("🚀 Launching Chrome...")
        
        try:
            driver = webdriver.Chrome(options=options)
            wait = WebDriverWait(driver, 25)
            actions = ActionChains(driver)
            
            driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"}
            )
            
            # LOGIN
            driver.get("https://www.facebook.com/")
            time.sleep(random.randint(6, 8))
            
            try:
                if len(driver.find_elements(By.ID, "email")) > 0:
                    email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
                    pass_input = driver.find_element(By.ID, "pass")
                    
                    email_input.clear()
                    email_input.send_keys(FB_EMAIL)
                    time.sleep(random.randint(1, 2))
                    
                    pass_input.clear()
                    pass_input.send_keys(FB_PASSWORD)
                    time.sleep(random.randint(1, 2))
                    
                    pass_input.submit()
                    self.log("🔐 Login submitted")
                    time.sleep(random.randint(10, 15))
                else:
                    self.log("ℹ️ Already logged in")
            except Exception as e:
                self.log(f"ℹ️ Login skipped or error: {e}")
            
            # MAIN LOOP
            self.log(f"\n🎭 Anonymous posting: {'ENABLED' if POST_ANONYMOUSLY else 'DISABLED'}")
            self.log(f"🎨 Background mode: {'ENABLED' if USE_BACKGROUND_IMAGE else 'DISABLED'}\n")
            
            for i, group in enumerate(self.groups, start=1):
                if not self.is_running:
                    self.log("🛑 Stopped by user")
                    break
                
                self.log(f"\n[{i}/{len(self.groups)}] Group: {group}")
                self.status_var.set(f"Processing group {i}/{len(self.groups)}")
                
                driver.get(f"https://www.facebook.com/groups/{group}")
                time.sleep(random.randint(6, 10))
                
                try:
                    # Open post box
                    self.log("   🖱️ Clicking 'Write something'...")
                    post_box = wait.until(
                        EC.element_to_be_clickable(
                            (By.XPATH,
                             "//div[@role='button']//span[contains(text(),'Write') or "
                             "contains(text(),'Escribe') or contains(text(),'Crear')]")
                        )
                    )
                    post_box.click()
                    
                    self.log("   ⏳ Waiting for popup...")
                    time.sleep(5)
                    
                    # Anonymous toggle (keeping full implementation from original)
                    if POST_ANONYMOUSLY:
                        try:
                            self.log("   🎭 Attempting to enable anonymous posting...")
                            self.log("   🔍 Scanning dialog for anonymous toggle...")
                            
                            anonymous_toggle = None
                            
                            # Strategy 1
                            try:
                                self.log("   → Strategy 1: Looking for 'Post anonymously' text...")
                                text_elements = driver.find_elements(By.XPATH, 
                                    "//div[@role='dialog']//span[contains(text(), 'Post anonymously') or contains(text(), 'Publicar de forma anónima') or contains(text(), 'anonymously')]")
                                
                                self.log(f"   → Found {len(text_elements)} elements with 'anonymously' text")
                                
                                if text_elements:
                                    for parent_level in range(1, 7):
                                        try:
                                            parent = text_elements[0]
                                            for _ in range(parent_level):
                                                parent = parent.find_element(By.XPATH, "..")
                                            
                                            role = parent.get_attribute("role")
                                            tag = parent.tag_name
                                            aria_checked = parent.get_attribute("aria-checked")
                                            
                                            self.log(f"   → Level {parent_level}: tag={tag}, role={role}, aria-checked={aria_checked}")
                                            
                                            if role in ["switch", "button", "checkbox"]:
                                                anonymous_toggle = parent
                                                self.log(f"   ✓ FOUND toggle at level {parent_level}!")
                                                break
                                        except:
                                            continue
                                    
                                    if not anonymous_toggle:
                                        try:
                                            parent_container = text_elements[0].find_element(By.XPATH, "../..")
                                            toggles = parent_container.find_elements(By.XPATH, 
                                                ".//div[@role='switch'] | .//input[@role='switch'] | .//input[@type='checkbox']")
                                            
                                            self.log(f"   → Found {len(toggles)} switches in container")
                                            
                                            if toggles:
                                                anonymous_toggle = toggles[0]
                                                self.log("   ✓ FOUND toggle via sibling search!")
                                        except Exception as e:
                                            self.log(f"   → Sibling search failed: {e}")
                                            
                            except Exception as e:
                                self.log(f"   → Strategy 1 exception: {e}")
                            
                            # Strategy 2
                            if not anonymous_toggle:
                                try:
                                    self.log("   → Strategy 2: Scanning all switches in dialog...")
                                    all_switches = driver.find_elements(By.XPATH, 
                                        "//div[@role='dialog']//div[@role='switch'] | //div[@role='dialog']//input[@role='switch'] | //div[@role='dialog']//input[@type='checkbox']")
                                    
                                    self.log(f"   → Total switches found: {len(all_switches)}")
                                    
                                    for idx, switch in enumerate(all_switches):
                                        aria_label = switch.get_attribute("aria-label") or ""
                                        aria_checked = switch.get_attribute("aria-checked") or "unknown"
                                        self.log(f"   → Switch {idx}: aria-label='{aria_label}', checked={aria_checked}")
                                        
                                        if "anonym" in aria_label.lower():
                                            anonymous_toggle = switch
                                            self.log(f"   ✓ FOUND toggle (Switch {idx})!")
                                            break
                                            
                                except Exception as e:
                                    self.log(f"   → Strategy 2 exception: {e}")
                            
                            # Strategy 3
                            if not anonymous_toggle:
                                try:
                                    self.log("   → Strategy 3: Looking for clickable row...")
                                    
                                    containers = driver.find_elements(By.XPATH,
                                        "//div[@role='dialog']//div[contains(., 'Post anonymously')]")
                                    
                                    self.log(f"   → Found {len(containers)} containers with text")
                                    
                                    for idx, container in enumerate(containers[:5]):
                                        role = container.get_attribute("role") or "none"
                                        tabindex = container.get_attribute("tabindex") or "none"
                                        self.log(f"   → Container {idx}: role={role}, tabindex={tabindex}")
                                        
                                        if tabindex != "none" or role in ["button", "switch"]:
                                            anonymous_toggle = container
                                            self.log(f"   ✓ FOUND clickable row (Container {idx})!")
                                            break
                                            
                                except Exception as e:
                                    self.log(f"   → Strategy 3 exception: {e}")
                            
                            if not anonymous_toggle:
                                self.log("   ⚠️ DEBUG: Showing first 10 clickable elements in dialog...")
                                try:
                                    clickables = driver.find_elements(By.XPATH, 
                                        "//div[@role='dialog']//*[@role='button' or @role='switch']")[:10]
                                    for idx, el in enumerate(clickables):
                                        text = el.text[:50] if el.text else "(no text)"
                                        aria = el.get_attribute("aria-label") or "(no aria-label)"
                                        self.log(f"   → Element {idx}: text='{text}', aria='{aria}'")
                                except:
                                    pass
                            
                            if anonymous_toggle:
                                self.log("   🎯 Attempting to click toggle...")
                                try:
                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", anonymous_toggle)
                                    time.sleep(1)
                                    
                                    is_on = anonymous_toggle.get_attribute("aria-checked")
                                    self.log(f"   → Current state: aria-checked={is_on}")
                                    
                                    if is_on == "true":
                                        self.log("   ℹ️ Anonymous mode already ON - skipping click")
                                    else:
                                        try:
                                            self.log("   → Trying ActionChains click...")
                                            actions.move_to_element(anonymous_toggle).pause(0.5).click().perform()
                                            self.log("   ✅ Anonymous toggle clicked (ActionChains)")
                                        except:
                                            self.log("   → ActionChains failed, trying JavaScript...")
                                            driver.execute_script("arguments[0].click();", anonymous_toggle)
                                            self.log("   ✅ Anonymous toggle clicked (JavaScript)")
                                        
                                        time.sleep(random.randint(2, 3))
                                        
                                        try:
                                            self.log("   🔍 Looking for 'Got it' confirmation popup...")
                                            
                                            got_it_button = WebDriverWait(driver, 5).until(
                                                EC.element_to_be_clickable(
                                                    (By.XPATH, 
                                                     "//div[@role='button' and (@aria-label='Got it' or @aria-label='Entendido' or contains(text(), 'Got it') or contains(text(), 'Entendido'))]"
                                                     " | //span[text()='Got it' or text()='Entendido']//ancestor::div[@role='button'][1]")
                                                )
                                            )
                                            
                                            self.log("   → Found 'Got it' button, clicking...")
                                            got_it_button.click()
                                            self.log("   ✅ 'Got it' popup dismissed")
                                            time.sleep(random.randint(1, 2))
                                            
                                        except Exception as popup_error:
                                            self.log(f"   ⚠️ No 'Got it' popup found (or already dismissed): {popup_error}")
                                        
                                        new_state = anonymous_toggle.get_attribute("aria-checked")
                                        self.log(f"   → New state: aria-checked={new_state}")
                                        self.log("   ✅ Anonymous posting ENABLED")
                                        
                                except Exception as e:
                                    self.log(f"   ⚠️ Click failed: {e}")
                                    try:
                                        anonymous_toggle.click()
                                        self.log("   ✅ Anonymous toggle clicked (fallback)")
                                        time.sleep(random.randint(2, 3))
                                    except:
                                        self.log(f"   ❌ All click methods failed")
                            else:
                                self.log("   ❌ Anonymous option NOT FOUND (group may not support it)")
                                
                        except Exception as e:
                            self.log(f"   ❌ Fatal error in anonymous toggle: {e}")
                            self.log("   ℹ️ Continuing with regular post...")
                    
                    # Focus textbox
                    self.log("   🔍 Focusing textbox...")
                    textbox = wait.until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//div[@role='dialog']//div[@role='textbox' and @contenteditable='true']")
                        )
                    )
                    
                    actions.move_to_element(textbox).click().perform()
                    time.sleep(random.randint(1, 2))
                    self.log("   ✅ Textbox Focused")
                    
                    # Paste text
                    text_to_paste = POST_TEXT
                    
                    if USE_BACKGROUND_IMAGE:
                        try:
                            text_to_paste = POST_TEXT[:125]
                            self.log(f"   🎨 Background Mode ON: Text truncated to 125 chars")
                            
                            self.log("   🔍 Looking for 'Show Background Options'...")
                            bg_options_btn = wait.until(EC.element_to_be_clickable(
                                (By.XPATH, "//div[@aria-label='Show Background Options']")
                            ))
                            bg_options_btn.click()
                            time.sleep(2)
                            
                            bg_choices = ["purple magenta", "red blue"]
                            selected_bg_name = random.choice(bg_choices)
                            self.log(f"   🎨 Selecting: {selected_bg_name}")
                            
                            bg_btn = wait.until(EC.element_to_be_clickable(
                                (By.XPATH, f"//*[contains(@aria-label, '{selected_bg_name}')]")
                            ))
                            
                            bg_btn.click()
                            time.sleep(2)
                            self.log("   ✅ Background selected")
                            
                        except Exception as e:
                            self.log(f"   ⚠️ Error selecting background: {e}")
                            self.log("   ℹ️ Falling back to normal text paste")
                            text_to_paste = POST_TEXT
                    
                    pyperclip.copy(text_to_paste)
                    time.sleep(0.5)
                    
                    actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
                    
                    self.log("   📝 Text pasted!")
                    time.sleep(random.randint(3, 4))
                    
                    # Upload images
                    if not USE_BACKGROUND_IMAGE and IMAGE_PATHS:
                        try:
                            abs_paths = [os.path.abspath(p) for p in IMAGE_PATHS]
                            files_string = "\n".join(abs_paths)
                            
                            self.log("   🖼️ Uploading images (Background)...")
                            
                            file_input = wait.until(
                                EC.presence_of_element_located(
                                    (By.XPATH, "//div[@role='dialog']//input[@type='file']")
                                )
                            )
                            
                            file_input.send_keys(files_string)
                            
                            self.log("   ✅ Images uploaded successfully")
                            time.sleep(5 + len(IMAGE_PATHS) * 3)
                            
                        except Exception as e:
                            self.log(f"   ⚠️ Image upload skipped/failed: {e}")
                    elif USE_BACKGROUND_IMAGE:
                        self.log("   🚫 Images ignored because Background Mode is active.")
                    
                    # Click Post button
                    time.sleep(random.randint(2, 3))
                    
                    try:
                        if POST_ANONYMOUSLY:
                            self.log("   🔍 Looking for Submit button (anonymous mode)...")
                        else:
                            self.log("   🔍 Looking for Post button...")
                        
                        post_btn = None
                        
                        if POST_ANONYMOUSLY:
                            post_button_xpaths = [
                                "//div[@role='dialog']//div[@aria-label='Submit']",
                                "//div[@role='dialog']//div[@aria-label='Enviar']",
                                "//div[@role='dialog']//span[text()='Submit']//ancestor::div[@role='button'][1]",
                                "//div[@role='dialog']//span[text()='Enviar']//ancestor::div[@role='button'][1]",
                                "//div[@role='dialog']//div[@role='button' and contains(., 'Submit')]",
                                "//div[@role='dialog']//div[@role='button' and contains(., 'Enviar')]",
                            ]
                        else:
                            post_button_xpaths = [
                                "//div[@role='dialog']//div[@aria-label='Post']",
                                "//div[@role='dialog']//div[@aria-label='Publicar']",
                                "//div[@role='dialog']//span[text()='Post']//ancestor::div[@role='button'][1]",
                                "//div[@role='dialog']//span[text()='Publicar']//ancestor::div[@role='button'][1]",
                                "//div[@role='dialog']//div[@role='button' and contains(., 'Post')]",
                                "//div[@role='dialog']//div[@role='button' and contains(., 'Publicar')]",
                            ]
                        
                        for xpath in post_button_xpaths:
                            try:
                                post_btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                                if post_btn:
                                    btn_text = post_btn.text or post_btn.get_attribute('aria-label') or 'button'
                                    self.log(f"   ✓ Found button: '{btn_text}'")
                                    break
                            except:
                                continue
                        
                        if not post_btn:
                            self.log("   ⚠️ Button not found with standard methods, trying broader search...")
                            all_buttons = driver.find_elements(By.XPATH, "//div[@role='dialog']//div[@role='button']")
                            
                            search_terms = ['submit', 'enviar'] if POST_ANONYMOUSLY else ['post', 'publicar', 'publish']
                            
                            for btn in all_buttons:
                                btn_text = btn.text.strip().lower()
                                btn_aria = (btn.get_attribute('aria-label') or '').lower()
                                
                                if any(term in btn_text or term in btn_aria for term in search_terms):
                                    post_btn = btn
                                    self.log(f"   ✓ Found button via text search: '{btn.text or btn_aria}'")
                                    break
                        
                        if post_btn:
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", post_btn)
                            time.sleep(random.randint(1, 2))
                            
                            try:
                                self.log("   → Clicking with ActionChains...")
                                actions.move_to_element(post_btn).click().perform()
                                self.log("   ✅ Button clicked (ActionChains)")
                            except:
                                try:
                                    self.log("   → ActionChains failed, trying JavaScript...")
                                    driver.execute_script("arguments[0].click();", post_btn)
                                    self.log("   ✅ Button clicked (JavaScript)")
                                except:
                                    self.log("   → JavaScript failed, trying direct click...")
                                    post_btn.click()
                                    self.log("   ✅ Button clicked (Direct)")
                            
                            if POST_ANONYMOUSLY:
                                self.log("   ✅ POSTED ANONYMOUSLY")
                            else:
                                self.log("   ✅ POSTED SUCCESSFULLY")
                                
                        else:
                            self.log("   ❌ Could not find Post/Submit button!")
                            raise Exception("Post/Submit button not found")
                            
                    except Exception as post_error:
                        self.log(f"   ❌ Error clicking Post/Submit button: {post_error}")
                        raise
                    
                    # Cool down
                    cooldown = random.randint(45, 70)
                    self.log(f"   ⏳ Cooling down {cooldown}s...")
                    time.sleep(cooldown)
                    
                except Exception as e:
                    self.log(f"❌ Failed in group {group}. ERROR: {e}")
                    continue
            
            self.log("\n🔥 All groups processed.")
            driver.quit()
            
        except Exception as e:
            self.log(f"❌ Fatal error: {e}")
            import traceback
            self.log(traceback.format_exc())
        
        finally:
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.status_var.set("Completed")




if __name__ == "__main__":
    root = tk.Tk()
    app = FacebookPosterGUI(root)
    root.mainloop()