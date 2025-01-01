# Home Assistant Alarm Clock Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release][releases-shield]][releases]
![Project Maintenance][maintenance-shield]
[![License][license-shield]](LICENSE)

A fully customizable alarm clock integration for Home Assistant that supports multiple alarm clocks, snooze functionality, and easy integration with media players and browser notifications.

## Features

- ✨ Create multiple alarm clocks (e.g., bedroom, kids room)
- 🔄 Configurable snooze duration
- ⏰ Flexible time format input (HH:MM:SS, HH:MM, HHMM)
- 🌐 Multi-language support (English, German, Dutch)
- 🔊 Easy integration with media players
- 🌐 Browser notification support via Browsermod
- 🏠 Full Home Assistant service integration

## Installation

### HACS (Recommended)

1. Open HACS
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add `https://github.com/DGTLMagician/hass-alarmclock` as a custom repository
   - Category: Integration
6. Click "Install"
7. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/alarm_clock` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

### Adding an Alarm Clock

1. Go to Settings > Devices & Services
2. Click "+ Add Integration"
3. Search for "Alarm Clock"
4. Configure your alarm clock:
   - Name (e.g., "Bedroom Alarm")
   - Default alarm time
   - Snooze duration (in minutes)

### Service Calls

The integration provides several services:

```yaml
# Set alarm time
service: alarm_clock.set_alarm
target:
  entity_id: switch.bedroom_alarm_clock
data:
  time: "07:00"  # Accepts HH:MM:SS, HH:MM, or HHMM

# Snooze alarm
service: alarm_clock.snooze
target:
  entity_id: switch.bedroom_alarm_clock

# Stop alarm
service: alarm_clock.stop
target:
  entity_id: switch.bedroom_alarm_clock
```

## Example Automations

### Media Player Integration

```yaml
automation:
  - alias: "Bedroom Alarm - Play Wake Up Music"
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
          media_content_id: !secret morning_playlist_url
          media_content_type: music
```

### Browser Notification

```yaml
automation:
  - alias: "Bedroom Alarm - Browser Notification"
    trigger:
      platform: event
      event_type: alarm_clock_triggered
      event_data:
        alarm_id: alarm_clock_bedroom
    action:
      - service: browsermod.notification
        data:
          message: "Wake up! It's time to start your day!"
          title: "Bedroom Alarm"
          duration: 0
```

### Smart Light Integration

```yaml
automation:
  - alias: "Bedroom Alarm - Gradual Wake Up Light"
    trigger:
      platform: event
      event_type: alarm_clock_triggered
      event_data:
        alarm_id: alarm_clock_bedroom
    action:
      - service: light.turn_on
        target:
          entity_id: light.bedroom
        data:
          brightness_pct: 1
          transition: 900  # 15 minutes
      - delay: 900
      - service: light.turn_on
        target:
          entity_id: light.bedroom
        data:
          brightness_pct: 100
```

## State Attributes

Each alarm clock entity has the following attributes:

| Attribute | Description |
|-----------|-------------|
| alarm_time | The time the alarm is set for |
| snooze_time | The configured snooze duration |

## Event Data

When an alarm is triggered, it fires an event `alarm_clock_triggered` with the following data:

```yaml
event_type: alarm_clock_triggered
event_data:
  alarm_id: alarm_clock_bedroom  # Based on the configured name
```

## Troubleshooting

### Time Format Issues

The integration accepts various time formats:
- HH:MM:SS (e.g., "07:00:00")
- HH:MM (e.g., "07:00")
- H:MM (e.g., "7:00")
- HHMM (e.g., "0700")

If you're having issues with time formats, ensure you're using one of these formats.

### Common Issues

1. **Alarm not triggering:** Ensure the alarm switch is turned on
2. **Snooze not working:** Verify the alarm is in an active state
3. **Multiple alarms conflicting:** Each alarm should have a unique name

## Contributing

Feel free to contribute to the project on [GitHub](https://github.com/DGTLMagician/hass-alarmclock).

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Open a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to the Home Assistant community
- Icons made by [Freepik](https://www.freepik.com) from [www.flaticon.com](https://www.flaticon.com)

---

[releases-shield]: https://img.shields.io/github/release/DGTLMagician/hass-alarmclock.svg
[releases]: https://github.com/DGTLMagician/hass-alarmclock/releases
[maintenance-shield]: https://img.shields.io/maintenance/yes/2025.svg
[license-shield]: https://img.shields.io/github/license/DGTLMagician/hass-alarmclock.svg