# Migrate Windows App Connections from Old Profile

## Method 1: Export/Import via Windows App Settings

### Step 1: Export from Old Profile
1. Open **Windows App** (formerly Remote Desktop)
2. Click the **Settings** gear icon (⚙️) in the top-right
3. Go to **Account** tab
4. Click **Export connections**
5. Save the `.rdp` or connection file to a shared location (Desktop, Documents, or USB drive)

### Step 2: Import to New Profile
1. Open **Windows App** in your new profile
2. Click **Settings** gear icon (⚙️)
3. Go to **Account** tab
4. Click **Import connections**
5. Select the exported file from Step 1
6. All connections should appear in your new profile

## Method 2: Manual File Copy (Alternative)

### Windows App Connection Files Location
```
Old Profile: /Users/jocousen-old/Library/Containers/com.microsoft.rdc.macos/Data/Library/Application Support/com.microsoft.rdc.macos/
New Profile: /Users/[current-username]/Library/Containers/com.microsoft.rdc.macos/Data/Library/Application Support/com.microsoft.rdc.macos/
```

### Copy Commands (run in Terminal)
```bash
# Navigate to old profile app data
cd "/Users/jocousen-old/Library/Containers/com.microsoft.rdc.macos/Data/Library/Application Support/com.microsoft.rdc.macos/"

# Copy connection files to current profile
cp -r * "/Users/$(whoami)/Library/Containers/com.microsoft.rdc.macos/Data/Library/Application Support/com.microsoft.rdc.macos/"
```

## Method 3: Using Finder (GUI Method)

### Step 1: Access Old Profile Files
1. Open **Finder**
2. Press `Cmd + Shift + G` (Go to Folder)
3. Enter: `/Users/jocousen-old/Library/Containers/com.microsoft.rdc.macos/Data/Library/Application Support/com.microsoft.rdc.macos/`
4. Copy all files in this folder

### Step 2: Paste to New Profile
1. Press `Cmd + Shift + G` again
2. Enter: `/Users/[your-current-username]/Library/Containers/com.microsoft.rdc.macos/Data/Library/Application Support/com.microsoft.rdc.macos/`
3. Paste the copied files
4. Restart Windows App

## Troubleshooting

### If Library Folder is Hidden
```bash
# Show hidden files in Finder
defaults write com.apple.finder AppleShowAllFiles YES
killall Finder

# Hide them again after migration
defaults write com.apple.finder AppleShowAllFiles NO
killall Finder
```

### If Windows App Doesn't Start
1. Quit Windows App completely
2. Clear app cache:
   ```bash
   rm -rf "/Users/$(whoami)/Library/Containers/com.microsoft.rdc.macos/Data/Library/Caches/"
   ```
3. Restart Windows App

### Verify Migration Success
1. Open Windows App
2. Check that all your connections appear
3. Test connecting to one of your servers
4. Verify saved credentials work

## Alternative: Fresh Setup (If Migration Fails)

If the above methods don't work, you can manually recreate connections:

1. Open Windows App
2. Click **+ Add** button
3. Select **PC** or **Remote Resource**
4. Enter connection details:
   - **PC name**: Server IP or hostname
   - **User account**: Your credentials
   - **Display name**: Friendly name for connection
5. Repeat for each connection

## Security Note

After successful migration, consider:
- Updating any saved passwords
- Verifying connection security settings
- Removing old profile data if no longer needed