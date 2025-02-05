Sure thing! Here is the full README content for you to copy:

```markdown
# Animix Game Bot

This is the Animix Game Bot with auto PVP arena functionality and other features. It's built using Node.js and supports both noproxy and proxy configurations.

## Features

- Auto PVP arena
- Existing functions remain unchanged
- Auto upgrade pet and clone DNA (upcoming feature)

## Installation

### Prerequisites

- Node.js installed on your system.

### Steps

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/animix-game-bot.git
   cd animix-game-bot
   ```

2. Install the necessary modules:

   ```bash
   npm install
   ```

3. Configure the `.env` file according to your needs.

4. If you already have `data.txt` for query ID and `proxy.txt` for proxy, you don't need to create them again. Otherwise, create new ones with the following formats:

   - `data.txt`: `query_id: user=...` or `query_id=xxx`
   - `proxy.txt`: `http://user:pass@ip:port`

5. Run the bot:

   - Without proxy:

     ```bash
     node animix
     ```

   - With proxy:

     ```bash
     node animix-proxy
     ```

## Notes

- Some missions might fail due to pet being busy; you can ignore these errors.
- If you encounter 401, 403, or 503 errors, try changing the query ID.

## Community
