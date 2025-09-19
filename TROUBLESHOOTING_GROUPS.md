# Troubleshooting Group Registration

## Issue: Groups not showing up in broadcasts

If you don't see groups registered even after users have joined and authenticated, follow these steps:

### Step 1: Check if the bot is properly added to the group
1. Make sure the bot is added to the group as an administrator (or at least with permission to send messages)
2. The bot should send a welcome message when added to the group

### Step 2: Register users in the group
1. In the group, have users type: `/register` to register themselves
2. Then have them type: `/join general welcome123` (or whatever the channel name and secret are)
3. The bot should respond with a success message
4. Check if the user is authenticated by having them type: `/status`

### Step 3: Use the debug command
1. As an admin, send `/debug_groups` to the bot in a private chat
2. This will show you:
   - All registered groups
   - All group members and their authentication status
   - All authenticated users

### Step 4: Check the database directly
If you have access to the database file (`data/bot_database.db`), you can run these SQL queries:

```sql
-- Check all groups
SELECT * FROM groups;

-- Check all group members
SELECT gm.group_id, g.group_title, gm.user_id, u.username, u.first_name, u.is_authenticated
FROM group_members gm
JOIN groups g ON gm.group_id = g.group_id
JOIN users u ON gm.user_id = u.user_id;

-- Check authenticated users
SELECT user_id, username, first_name, is_authenticated, channel_id
FROM users 
WHERE is_authenticated = TRUE;
```

### Step 5: Test the API
Run the test script to see what the API returns:

```bash
python test_group_broadcast.py
```

### Common Issues and Solutions

#### Issue: Bot crashes when users send regular messages
**Cause**: Bot was trying to reply to every message
**Solution**: 
1. The bot now ignores regular messages and only responds to commands
2. Users can send any message without causing crashes
3. Only `/start`, `/join`, `/status`, etc. commands will get responses

#### Issue: Group not registered
**Cause**: The bot wasn't properly added to the group
**Solution**: 
1. Remove the bot from the group
2. Add the bot back to the group
3. Make sure the bot sends a welcome message

#### Issue: User not tracked in group
**Cause**: User didn't send any messages in the group after joining
**Solution**:
1. Have the user send any message in the group (this triggers group tracking)
2. Or have them use `/join` command in the group

#### Issue: User authenticated but not in group_members table
**Cause**: User authenticated in private chat, not in the group
**Solution**:
1. Have the user use `/join` command in the group (not in private chat)
2. Or have them send a message in the group after authenticating

#### Issue: Broadcast not reaching groups
**Cause**: No authenticated users in groups
**Solution**:
1. Make sure at least one user in the group is authenticated
2. Check the debug output to verify group membership

### Expected Flow

1. **Bot added to group** → Group registered in `groups` table
2. **User joins group** → User added to `group_members` table
3. **User authenticates in group** → User marked as authenticated in `users` table
4. **Broadcast sent** → Message sent to all groups with authenticated users

### Testing Commands

- `/debug_groups` - Show all groups, members, and authentication status (admin only)
- `/stats` - Show basic statistics (admin only)
- `/status` - Check your own authentication status
- `/register` - Register yourself in the current group
- `/join <channel_name> <channel_secret>` - Authenticate in a channel
- `/leave` - Leave current channel
- `/stop` - Remove yourself from group and deauthenticate

### API Testing

Use the test script or curl commands:

```bash
# Test broadcast
curl -X POST http://localhost:5000/api/broadcast \
  -H "X-API-Key: change-me" \
  -H "Content-Type: application/json" \
  -d '{"message": "Test message"}'

# Check stats
curl -X GET http://localhost:5000/api/stats \
  -H "X-API-Key: change-me"
```

If you're still having issues, check the bot logs for any error messages.
