# DC Scorecard website: setup guide

You already own **dcscorecard.org** (registered at Porkbun). The plan:
- **Now:** put the scorecard site live on GitHub Pages as a test (Part 1), then on your own address, `scorecard.dcscorecard.org` (Part 2).
- **Later:** the Substack newsletter takes the main address, `dcscorecard.org` (Part 3).

The subdomain doesn't have to be `scorecard`. `map` or `data` work just as well; use the same word everywhere it appears below.

---

## Part 1. Put the site live on GitHub (free, about 20 minutes)

### 1a. Create your GitHub account
1. Go to github.com and click **Sign up**.
2. Choose your username. It appears in the test address (`username.github.io`). A project-style name like `dcscorecard` works well.
3. Verify your email.
4. Turn on two-factor authentication: click your profile picture (top right), then **Settings > Password and authentication**. It protects the site from being defaced.

### 1b. Create the repository (the folder that holds the site)
1. Click the **+** in the top right, then **New repository**.
2. **Repository name:** `dc-scorecard`
3. **Description (optional):** "A report card for DC, block by block"
4. Choose **Public**. Free GitHub Pages requires it.
5. Leave "Add a README file" **unchecked** (the zip already has one). Leave .gitignore and license as **None**.
6. Click **Create repository**.

### 1c. Upload the site files
1. Unzip `DC-Scorecard-website.zip` on your computer. You'll get files and folders like `index.html`, `404.html`, `README.md`, `assets`, `data`, `traffic-safety`, `about` and `pipeline`.
2. On the new, empty repository page, click the link **uploading an existing file** in the "Quick setup" box.
3. Open the unzipped folder, select **everything inside it** (Ctrl+A on Windows, Cmd+A on Mac) and drag it onto the GitHub page. Drag the contents, not the folder itself.
   - Use Chrome, Edge or Firefox; they keep the subfolders when you drag. If a folder doesn't upload, drag it in on its own.
4. Wait until every file appears in the list (about 26).
5. Under **Commit changes**, type "First version of the site". Keep **Commit directly to the main branch** selected and click **Commit changes**.
6. Check the repository's main page: `index.html`, `404.html`, `README.md` and the folders should be listed at the top level.
   - If they ended up inside another folder (for example `DC-Scorecard-website/`), delete the repository (**Settings**, scroll to **Danger Zone**, **Delete this repository**) and redo 1b and 1c.

### 1d. Turn on GitHub Pages
1. In the repository, click the **Settings** tab (gear icon), then **Pages** in the left sidebar.
2. Under **Build and deployment**:
   - **Source:** Deploy from a branch
   - **Branch:** `main`, folder `/ (root)`
   - Click **Save**.
3. Wait one to two minutes and refresh. A banner appears: "Your site is live at `https://username.github.io/dc-scorecard/`".
   - If nothing shows yet, open the **Actions** tab. Yellow means building, green means done, red means it failed (send Claude a screenshot).
4. Open the address and test the site: search for 4D02, switch between City, Wards, ANCs and districts, and open it on your phone.

**Your test site is live.** Share the address with a few people for feedback. Parts 2 and 3 can wait as long as you like.

---

## Part 2. Move it to scorecard.dcscorecard.org (free, about 15 minutes plus waiting)

### 2a. Verify your domain with GitHub (recommended)
This stops anyone else from claiming dcscorecard.org on GitHub.
1. On GitHub, click your profile picture, then **Settings**, then **Pages** in the left sidebar (under "Code, planning, and automation"). This is your account settings, not the repository's.
2. Click **Add a domain**, enter `dcscorecard.org` and click **Add domain**.
3. GitHub shows a **TXT** record with a host name (something like `_github-pages-challenge-username`) and a value (a long code). Leave this page open.
4. In another tab, log in to Porkbun, go to **Domain Management**, find dcscorecard.org and click **DNS**.
5. Click **+ Add record** and fill in:
   - **Type:** TXT
   - **Host:** the host name GitHub showed, without the `.dcscorecard.org` part (Porkbun adds that automatically)
   - **Answer / Value:** the code GitHub showed
   - **TTL:** leave the default
6. Save the record, go back to GitHub and click **Verify**. If it fails, wait 10 to 30 minutes and try again.

### 2b. Point the subdomain at GitHub
1. On Porkbun's DNS page for dcscorecard.org, find the record **CNAME `*.dcscorecard.org` → `pixie.porkbun.com`** and delete it with the red trash icon. This is Porkbun's placeholder for subdomains.
2. **Leave the ALIAS record for `dcscorecard.org` alone.** That's the main address, which Substack takes later. Until then it shows Porkbun's placeholder page.
3. Click **+ Add record** and fill in:
   - **Type:** CNAME
   - **Host:** `scorecard`
   - **Answer / Value:** `username.github.io` (your GitHub username, with no `https://` and no `/dc-scorecard`)
   - **TTL:** leave the default
4. Save the record.

### 2c. Tell GitHub about the address
1. Go back to your `dc-scorecard` repository, then **Settings > Pages**.
2. Under **Custom domain**, enter `scorecard.dcscorecard.org` and click **Save**.
3. GitHub runs a DNS check. Within a few minutes to an hour it shows "DNS check successful."
4. Wait until the **Enforce HTTPS** box becomes clickable (up to an hour while GitHub gets the security certificate), then tick it.
5. Visit `https://scorecard.dcscorecard.org`. The old `username.github.io/dc-scorecard` address now forwards there automatically.

GitHub adds a file named `CNAME` to the repository when you save the custom domain. Leave it there.

---

## Part 3. Add the Substack newsletter (later)

### 3a. Start the Substack (free)
1. Go to substack.com and click **Start writing**. Sign up with the email you want readers to see replies from.
2. Try `dcscorecard` as the Substack address (`dcscorecard.substack.com`) so it matches.
3. Set the publication name, a one-line description and a logo. Claude can export the flag mark from the site so they match.

### 3b. Point dcscorecard.org at Substack ($50 one-time fee)
1. In Substack, open your **Dashboard**, then **Settings > Domain** (in some versions, **Settings > Publication details > Custom domain**).
2. Click **Add custom domain** and pay the $50 one-time fee.
3. Enter `www.dcscorecard.org`. Substack recommends the www version and redirects plain `dcscorecard.org` to it.
4. Substack shows the DNS records to add. On Porkbun's DNS page:
   - Delete Porkbun's placeholder **ALIAS `dcscorecard.org` → `pixie.porkbun.com`** if Substack's instructions include a record for the bare domain.
   - Add each record exactly as Substack shows it: same type, same host, same value. Leave your `scorecard` CNAME and the GitHub TXT record alone.
5. Back in Substack, click **Check status**. It often works within an hour but can take up to 36 hours.

### 3c. Connect the two
1. **In Substack:** go to **Settings > Website** (or **Settings > Navigation**) and add a navigation link named "Scorecard" pointing to `https://scorecard.dcscorecard.org`.
2. **On the site:** send Claude the newsletter address. Claude adds a "Newsletter" link to the site menu and gives you updated files to upload (see "Updating the site").

### 3d. Interactive charts in posts (optional, free)
1. Create a free account at datawrapper.de.
2. Ask Claude for the ready-made files (boundaries plus grades). In Datawrapper, choose **Create new > Map > Choropleth map**, then **Upload your own map** and paste in the grades.
3. Click **Publish**, copy the "Visualization only" link and paste it into a Substack post. It stays interactive on the web and shows as an image in email.

---

## Updating the site
1. In the repository, open the folder holding the file (for example `data/traffic-safety`).
2. Click **Add file > Upload files**, drag in the new version with the same name, and click **Commit changes**. GitHub replaces the old file.
3. The live site updates within a minute or two. Every past version is kept in the repository's history, so any change can be undone.

## Refreshing the data
1. Download fresh copies from DC Open Data: Crashes in DC, Single Member District 2023, Traffic Volume, Ward 2022 and Roadway Functional Classification.
2. Send them to Claude to rebuild, or run the scripts in `pipeline/` in this order: `process.py`, `build.py`, `trend.py`, `grade.py`, `build_site.py`.
3. Upload the changed files as above.

## Costs
- Domain: $7.98 the first year, then $11.84 a year (Porkbun)
- GitHub Pages: free
- Substack: free, plus $50 one time for the custom domain
