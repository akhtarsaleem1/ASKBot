# ASKBot Daily Play Store Promotion Bot

ASKBot is a local Windows bot that promotes your Google Play developer portfolio apps automatically. It refreshes Play Store metadata, picks an app in rotation, generates professional AI marketing copy, creates promo graphics using Gemini or Flux, and queues posts to social media via Buffer.

## Core Features

- **Automated Rotation**: Promotes one enabled app per day using round-robin rotation.
- **AI Content Generation**: Generates platform-specific social copy (X, Instagram, LinkedIn, etc.) using Groq (Llama 3/Mistral).
- **AI Image Generation**: Creates high-end promo graphics using **Gemini 2.0 Flash** or **Hugging Face (Flux)**.
- **Dynamic Dashboard**: Full control over settings, apps, and channels through a beautiful web interface.
- **Silent Background Operation**: Runs completely invisibly on your laptop with no annoying windows.
- **Preview & Manual Approval**: Generate content for any app on-demand and publish it with one click.
- **Auto-Startup**: Automatically resumes its work every time you turn on your laptop.

## First-Time Setup

1. **Install Dependencies**:
   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
   ```

2. **Configure API Keys**:
   Create a `.env` file in the root directory and add your keys:
   ```env
   GROQ_API_KEY=your_key
   BUFFER_API_KEY=your_key
   CLOUDINARY_CLOUD_NAME=your_name
   CLOUDINARY_API_KEY=your_key
   CLOUDINARY_API_SECRET=your_secret
   GEMINI_API_KEY=your_gemini_key
   HUGGINGFACE_API_KEY=your_hf_key
   ```

3. **Enable Silent Auto-Startup**:
   Run this to ensure the bot starts automatically every time you log in:
   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\enable_autostart.ps1
   ```

## Managing the Bot

### Control Commands
- **Start Silently**: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\start_background.ps1`
- **Stop Bot**: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\stop.ps1`
- **Restart**: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\restart.ps1`
- **Check Status**: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\status.ps1`

### Using the Dashboard
Open [http://127.0.0.1:8788](http://127.0.0.1:8788) to:
- **Apps**: Refresh your app catalog from Google Play or add apps manually.
- **Settings**: Change the **Daily Post Time**, update your **Timezone**, or switch your **AI Image Provider** (Gemini vs. Hugging Face).
- **Preview**: Select an app, generate a draft preview, and click **Approve & Publish** to post it immediately.
- **Run Now**: Trigger the daily automated run manually (useful for testing timing changes).

## Operation Modes

### 1. Fully Automated (Set and Forget)
The bot runs silently in the background. It will wake up at your configured **Daily Post Time**, pick an app, and post to your social media. No windows will appear; it just works.

### 2. Manual Curation (Preview Mode)
If you want to review the content before it goes live:
1. Go to the **Preview** page in the dashboard.
2. Select an app and generate a preview.
3. If you like the result, click **Approve & Publish**.

## Troubleshooting
If you experience any issues:
- Check the **Logs** tab in the dashboard for detailed error messages.
- View the raw background logs in `data\background.out.log` and `data\background.err.log`.
- Run `.\status.ps1` to verify all API keys are correctly loaded.

---
*Keep your `.env` file private. It contains your API secrets.*
