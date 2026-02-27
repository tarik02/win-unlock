# win-unlock

A tool to unlock Windows lockscreen without user interaction.

## How it works

When Windows locks the session, `LogonUI.exe` is running on the console. The tool connects via RDP (using credentials you provide), waits for an active RDP session to appear, then uses `tscon` to move that session back to the console — dismissing the lock screen without any user interaction.

## Requirements

- Windows (must be run on the machine you want to unlock)
- RDP must be enabled on the machine
- The account credentials in the RDP URL must have permission to log in via RDP
- Must be run with sufficient privileges to call `tscon`

## Usage

```powershell
win-unlock [--rdp-url URL | --rdp-url-file FILE] [--width W --height H] [--force]
```

The RDP URL can be supplied in three ways (mutually exclusive):

| Method                       | Example                                                    |
| ---------------------------- | ---------------------------------------------------------- |
| `--rdp-url URL`              | `--rdp-url "rdp+ntlm-password://user:pass@127.0.0.1:3389"` |
| `--rdp-url-file FILE`        | `--rdp-url-file /path/to/url.txt`                          |
| `WIN_UNLOCK_RDP_URL` env var | `WIN_UNLOCK_RDP_URL=rdp+ntlm-password://...`               |

### Options

| Flag                   | Description                                                                                                  |
| ---------------------- | ------------------------------------------------------------------------------------------------------------ |
| `--width W --height H` | RDP session resolution in pixels. Both must be supplied together. Defaults to the current screen resolution. |
| `--force`              | Run even if the session does not appear to be locked                                                         |

### URL format

```plain
rdp+ntlm-password://username:password@host:port
```

## Development

```powershell
mise install
```
