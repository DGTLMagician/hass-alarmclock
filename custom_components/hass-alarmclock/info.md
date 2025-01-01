# Alarm Clock Integration

A fully customizable alarm clock integration for Home Assistant that supports multiple alarm clocks, snooze functionality, and easy integration with media players and browser notifications.

## Features

- ✨ Create multiple alarm clocks
- 🔄 Configurable snooze duration
- ⏰ Flexible time format input
- 🌐 Multi-language support
- 🔊 Media player integration
- 🌐 Browser notification support

## Configuration

1. Go to Settings > Devices & Services
2. Click "+ Add Integration"
3. Search for "Alarm Clock"
4. Configure:
   - Name (e.g., "Bedroom Alarm")
   - Default alarm time
   - Snooze duration

## Example Usage

```yaml
automation:
  - alias: "Bedroom Alarm - Play Music"
    trigger:
      platform: event
      event_type: alarm_clock_triggered
      event_data:
        alarm_id: alarm_clock_bedroom
    action:
      - service: media_player.play_media
        target:
          entity_id: media_player.bedroom_speaker
        data:
          media_content_id: your_playlist_url
          media_content_type: music
```

[Full Documentation](https://github.com/DGTLMagician/hass-alarmclock)