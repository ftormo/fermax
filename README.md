# Fermax for Home Assistant

Custom Home Assistant integration for Fermax DUOX / Blue door entry systems.

This integration focuses on one job only: exposing visible Fermax doors as Home Assistant button entities so you can trigger door opening from the UI, dashboards, or automations.

## Features

- Config flow with Fermax Blue username and password
- Stores both access token and refresh token in the config entry
- Automatically requests a new token if an API call returns unauthorized
- Discovers doors from the pairing data returned by `GET /me`
- Creates one Home Assistant button entity for each visible door in `accessDoorMap`
- Includes local brand assets for the integration UI

## Supported API flow

The integration uses these Fermax endpoints:

1. `POST /oauth/token`
2. `GET /pairing/api/v4/pairings/me`
3. `POST /deviceaction/api/v1/device/{device_id}/directed-opendoor`

Authentication is based on the Fermax Blue mobile app client credentials and the user's account credentials.

## Installation

### Manual installation

1. Copy `custom_components/fermax` into your Home Assistant `config/custom_components` directory.
2. Restart Home Assistant.
3. Go to `Settings -> Devices & Services`.
4. Click `Add Integration`.
5. Search for `Fermax DuoxMe`.
6. Enter your Fermax Blue email and password.

Expected final path:

```text
config/
└── custom_components/
	└── fermax/
```

## Configuration

This integration is configured from the UI only.

During setup, the integration asks for:

- Username / email
- Password

On successful login, it stores:

- `access_token`
- `refresh_token`

The refresh token is persisted for future use, although the current implementation renews authentication by requesting a new token with username/password when needed.

## How it works

1. The integration authenticates against Fermax.
2. It requests the list of pairings from the account.
3. It reads `accessDoorMap` for each pairing.
4. Every door with `visible: true` becomes a Home Assistant button entity.
5. Pressing the button sends the `directed-opendoor` request for that specific door.

If any authenticated API call returns `401 Unauthorized`, the integration automatically performs a new login, updates the stored tokens, and retries the original request.

## Entities

The integration creates `button` entities.

Examples:

- `button.portal`
- `button.calle`

Entity names come from the Fermax door title. If the title is empty, the integration falls back to the door key from `accessDoorMap`.

All doors from the same pairing are grouped under one Home Assistant device.

## Notes and limitations

- The integration is cloud-based and requires internet access.
- Only door opening is supported.
- It does not expose call events, sensors, cameras, audio, or video.
- Door data is refreshed periodically through the coordinator, while the open-door action is executed on demand.
- The current implementation depends on the Fermax mobile app API behavior and headers.

## Project structure

```text
custom_components/fermax/
├── __init__.py
├── api.py
├── button.py
├── config_flow.py
├── const.py
├── coordinator.py
├── manifest.json
├── strings.json
├── brand/
│   ├── icon.png
│   └── logo.png
└── translations/
	├── en.json
	└── es.json
```

## Development notes

- `api.py` handles authentication, token persistence callbacks, retries, and API requests.
- `coordinator.py` loads pairing data from Fermax.
- `button.py` builds Home Assistant button entities for visible doors.
- `config_flow.py` validates credentials before creating the config entry.

## Disclaimer

This project is an unofficial integration and is not affiliated with or endorsed by Fermax.