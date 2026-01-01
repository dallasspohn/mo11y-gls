# Web Search Site-Specific Syntax

## Problem
When users ask to search a specific website (e.g., "search spohnz.com"), the agent wasn't using the `site:` syntax that DuckDuckGo requires.

## Solution
Updated the agent to automatically detect site-specific search requests and add the `site:` prefix.

## How It Works

### Automatic Detection
The agent now detects when you want to search within a specific site:
- "search spohnz.com" → `site:spohnz.com`
- "search spohnz.com for python" → `site:spohnz.com python`
- "use web_search to search spohnz.com" → `site:spohnz.com`

### Examples

**User**: "search spohnz.com"
**Agent**: Uses `web_search` with query `site:spohnz.com`

**User**: "search spohnz.com for python tutorials"
**Agent**: Uses `web_search` with query `site:spohnz.com python tutorials`

**User**: "use web_search to search the latest world news"
**Agent**: Uses `web_search` with query `latest world news` (no site: prefix for general searches)

## Updated Instructions

The agent now receives explicit instructions:
- For site-specific searches: Use `site:domain.com` syntax
- When user mentions a website domain, use `site:` prefix
- Example: "search spohnz.com" → `site:spohnz.com`

## Testing

Try these commands:
1. "search spohnz.com"
2. "use web_search to search spohnz.com"
3. "search spohnz.com for python"

All should now use `site:spohnz.com` syntax automatically.
