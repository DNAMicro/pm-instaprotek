# Bazaarvoice Review Bot - Setup Instructions

## Folder Structure

Create this structure in your `pm-instaprotek` folder:

```
pm-instaprotek/
├── bazaarvoice-bot/
│   ├── package.json
│   ├── bazaarvoice-bot.js
│   ├── config.json
│   ├── credentials.json.example
│   ├── credentials.json (create from example - never commit)
│   ├── .gitignore
│   └── SKILL.md (the automation skill)
```

## Quick Setup

### 1. Create the folder
```bash
cd ~/Documents/pm-instaprotek
mkdir bazaarvoice-bot
cd bazaarvoice-bot
```

### 2. Copy all files
Copy these files into the `bazaarvoice-bot` folder:
- `package.json`
- `bazaarvoice-bot.js`
- `config.json`
- `credentials.json.example`
- `.gitignore`
- `bazaarvoice-automation-SKILL.md` (rename to `SKILL.md`)

### 3. Create credentials file
```bash
cp credentials.json.example credentials.json
```

Edit `credentials.json` and add your actual Bazaarvoice email and password:
```json
{
  "bazaarvoice": {
    "username": "your_actual_email@example.com",
    "password": "your_actual_password",
    "url": "https://response.bazaarvoice.com/#/respond"
  }
}
```

### 4. Install dependencies
```bash
npm install
```

### 5. Test locally
```bash
npm start
```

The browser will open and show the bot logging in and filtering reviews.

## For GitHub

### Commit these files:
- `package.json`
- `bazaarvoice-bot.js`
- `config.json`
- `credentials.json.example`
- `.gitignore`
- `SKILL.md`

### NEVER commit:
- `credentials.json` (it's in .gitignore)
- `node_modules/`

### Push to GitHub:
```bash
git add .
git commit -m "Add Bazaarvoice review automation bot"
git push
```

## For Cloud Server

1. Clone the repo:
```bash
git clone https://github.com/your-username/your-repo.git
cd bazaarvoice-bot
npm install
```

2. Create credentials.json on the server:
```bash
cat > credentials.json << 'EOF'
{
  "bazaarvoice": {
    "username": "your_email@example.com",
    "password": "your_password",
    "url": "https://response.bazaarvoice.com/#/respond"
  }
}
EOF
```

3. Run the bot:
```bash
npm start
```

4. Schedule with cron (Linux/Mac):
```bash
crontab -e
# Add: 0 17 * * * cd /path/to/bazaarvoice-bot && npm start
```

## Troubleshooting

**Bot won't login:**
- Check credentials.json has correct email/password
- Verify Bazaarvoice account works in browser

**Can't find reviews:**
- Make sure filters are applied correctly
- Check if reviews are actually unread

**Script errors:**
- Run `npm install` again
- Check Node.js version (needs v12+)
- Look at console output for specific errors

## Security Reminders

✅ credentials.json is in .gitignore - never committed
✅ .gitignore prevents accidental password leaks
✅ credentials.json.example is your template
✅ Cloud server has its own credentials.json

## Next Steps

1. Copy all files to your `bazaarvoice-bot` folder
2. Create credentials.json with your Bazaarvoice login
3. Run `npm install`
4. Test with `npm start`
5. Push to GitHub
6. Deploy to cloud server when ready
