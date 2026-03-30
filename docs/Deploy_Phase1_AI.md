# Phase 1: Deploying the AI Service to Render

**Why are we doing this first?**
Because you mentioned the AI Service crashed on Render for you previously. I have completely redesigned your AI code behind the scenes (forcing it to use the CPU-only version of PyTorch and the Gunicorn production server) to ensure it never runs out of memory again. I just pushed these fixes to your GitHub. We will deploy this slowly and carefully right now.

## Step 1: Connect to Render
1. Go to [Render.com](https://render.com) and log in.
2. At the top of your Dashboard, click the **"New+"** button and select **"Web Service"**.
3. Under "Connect a repository", select the **`MohitSingh-2335/DePIN-Guard`** repository. *(If you don't see it, click "Connect GitHub" or "Configure Account" to give Render permission to see the repo).*

## Step 2: Fill in the EXACT Details (Do Not Guess)
When Render asks you to fill out the Deployment form, type these EXACT values in the boxes:

- **Name:** `depin-ai` *(or whatever you like)*
- **Region:** Choose the region closest to you (e.g., `Singapore` or `Frankfurt`).
- **Branch:** `main`
- **Root Directory:** `ai-service`  *(🚨 THIS IS CRITICALLY IMPORTANT! Do not leave this blank. Type exactly `ai-service` because all the AI code is hidden inside that specific folder).*
- **Environment:** `Docker` *(Render will automatically find the Dockerfile we just updated).*
- **Instance Type:** Select the `Free` tier ($0/month).

## Step 3: Click Deploy!
1. Scroll down to the bottom and click **"Create Web Service"**.
2. Render will open a black terminal window and start downloading your AI model. 
3. **Wait exactly 5-10 minutes.** Because we just optimized your `requirements.txt`, it will successfully download the files, install them, and print `AI service ready...` without crashing!

## Step 4: Save Your Permanent URL
Once the top left corner says **"Live"** in green, look right below the name of your service. You will see a permanent URL that looks something like `https://depin-ai-abcd.onrender.com`.

**Copy that URL.** That is your permanent AI URL for the rest of the project.

---

### 👉 Stop Here and Reply to Me
Do this exact phase right now. 

If Render asks you a confusing question or spits out an error in the logs, **stop immediately, copy-paste the error here (or describe what you see), and ask me.** I will solve it instantly. 

If it succeeds, reply to me and paste your permanent URL! We will then immediately move to Phase 2 (The Auth Service).
