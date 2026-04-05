# Flask Settings
SECRET_KEY = "dev_secret_key_change_me_in_production"

# --- Email Configuration (SMTP) ---
# Replace these with your actual SMTP credentials
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USE_SSL = False
MAIL_USERNAME = 'example@gmail.com'
MAIL_PASSWORD = 'your-app-specific-password'
MAIL_DEFAULT_SENDER = ('Smart Study Assistant', 'example@gmail.com')

# --- AI Configuration ---
# Options: "openai", "gemini", "deepseek"
AI_PROVIDER = "gemini"

# OpenAI Settings (Also used by DeepSeek if using OpenAI-compatible mode)
OPENAI_API_KEY = "[your_openai_api_key_here]"
OPENAI_MODEL = "gpt-4o-mini"

# Gemini Settings
GEMINI_API_KEY = "[your_gemini_api_key_here]"
GEMINI_MODEL = "gemini-2.5-flash"

# DeepSeek Settings
DEEPSEEK_API_KEY = "[your_deepseek_api_key_here]"
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
