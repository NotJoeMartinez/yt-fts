# Troubleshooting 403 Errors

## What are 403 Errors?

403 Forbidden errors occur when YouTube blocks requests from your application. This typically happens due to:

- **Rate limiting**: Too many requests in a short time period
- **Missing authentication**: No cookies or session data
- **Bot detection**: YouTube identifying automated requests
- **IP blocking**: Your IP address has been temporarily blocked
- **Geographic restrictions**: Content not available in your region

## Quick Diagnosis

Run the built-in diagnosis tool to identify the issue:

```bash
# Basic diagnosis
yt-fts diagnose

# Diagnosis with browser cookies
yt-fts diagnose --cookies-from-browser chrome

# Diagnosis with specific job count
yt-fts diagnose -j 4
```

## Common Solutions

### 1. Use Browser Cookies

The most effective solution is to use cookies from your browser:

```bash
# Use Chrome cookies
yt-fts download --cookies-from-browser chrome <channel_url>

# Use Firefox cookies
yt-fts download --cookies-from-browser firefox <channel_url>
```

**How to set up cookies:**
1. Log into YouTube in your browser (Chrome or Firefox)
2. Make sure you're logged in and can access the channel
3. Run the download command with `--cookies-from-browser`

### 2. Reduce Parallel Jobs

High parallel job counts can trigger rate limiting:

```bash
# Use fewer parallel jobs
yt-fts download -j 2 <channel_url>
yt-fts download -j 4 <channel_url>

# For very problematic channels, use just 1 job
yt-fts download -j 1 <channel_url>
```

### 3. Wait Between Attempts

If you're getting rate limited, wait a few minutes before trying again:

```bash
# Wait 5-10 minutes between attempts
# Then try again with reduced jobs
yt-fts download -j 2 --cookies-from-browser chrome <channel_url>
```

### 4. Check Channel Accessibility

Some channels may be:
- **Private**: Only accessible to subscribers
- **Age-restricted**: Requires login and age verification
- **Region-blocked**: Not available in your country

Try accessing the channel in your browser first to verify it's publicly accessible.

## Advanced Troubleshooting

### Test Network Connectivity

```bash
# Test basic connectivity
curl -I https://www.youtube.com

# Test with custom user agent
curl -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" https://www.youtube.com
```

### Update yt-dlp

Ensure you have the latest version of yt-dlp:

```bash
pip install --upgrade yt-dlp
```

### Check for VPN/Proxy Issues

If you're using a VPN or proxy:
1. Try disabling it temporarily
2. Switch to a different server/location
3. Use a residential IP if possible

### Monitor Rate Limits

Watch for these error patterns:
- **429 Too Many Requests**: Immediate rate limit
- **403 Forbidden**: General blocking
- **503 Service Unavailable**: Temporary server issues

## Error Message Reference

| Error | Cause | Solution |
|-------|-------|----------|
| `403 Forbidden` | General blocking | Use cookies, reduce jobs |
| `429 Too Many Requests` | Rate limiting | Wait, reduce jobs |
| `Video unavailable` | Private/restricted | Check channel access |
| `Sign in to confirm your age` | Age restriction | Use logged-in cookies |

## Prevention Tips

1. **Always use browser cookies** for consistent access
2. **Start with low job counts** (2-4) and increase gradually
3. **Monitor for errors** and adjust accordingly
4. **Don't run multiple instances** simultaneously
5. **Respect rate limits** - wait between large downloads

## Getting Help

If you're still experiencing issues:

1. Run the diagnosis tool: `yt-fts diagnose`
2. Check the error messages for specific details
3. Try the test script: `python test_403_diagnosis.py`
4. Report issues with:
   - Error messages
   - Channel URL (if public)
   - Your configuration (jobs, cookies, etc.)
   - Diagnosis output

## Example Workflow

```bash
# 1. Diagnose the issue
yt-fts diagnose --cookies-from-browser chrome

# 2. Try with cookies and low job count
yt-fts download --cookies-from-browser chrome -j 2 <channel_url>

# 3. If successful, gradually increase jobs
yt-fts download --cookies-from-browser chrome -j 4 <channel_url>

# 4. For large channels, consider breaking into smaller batches
# Download in chunks with breaks between them
``` 