# Homebrew Tap for Address Cleanser

This directory contains the Homebrew formula for Address Cleanser, allowing users to install it easily via Homebrew.

## Installation

Users can install Address Cleanser using:

```bash
brew tap joshuboi77/homebrew-address-cleanser
brew install address-cleanser
```

## Formula

The formula automatically:
- Downloads the latest release from GitHub
- Verifies the SHA256 checksum
- Installs the binary to `/opt/homebrew/bin/` (Apple Silicon) or `/usr/local/bin/` (Intel)
- Renames the binary from `address-cleanser-darwin-universal` to `address-cleanser`
- Provides a test to verify installation

## Updating

To update the formula for a new release:

1. Update the `url` field with the new release URL
2. Update the `sha256` field with the new checksum
3. Update the `version` field
4. Commit and push the changes

## Testing

Test the formula locally:

```bash
brew install --build-from-source ./Formula/address-cleanser.rb
brew test address-cleanser
```
