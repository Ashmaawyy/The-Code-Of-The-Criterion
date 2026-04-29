"""CLI tool for managing Al-Furqan API keys.

Usage:
    python -m al_furqan.auth.cli create-key --name "Muhammad" --role evaluator
    python -m al_furqan.auth.cli list-keys
    python -m al_furqan.auth.cli revoke-key afk_live_xxx
    python -m al_furqan.auth.cli rotate-key afk_live_xxx
"""

import argparse
import sys
from datetime import datetime

from al_furqan.auth.key_manager import KeyManager
from al_furqan.auth.models import APIKey


def _format_time(ts: float) -> str:
    """Format a Unix timestamp for display."""
    if ts == 0:
        return "Never"
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def cmd_create_key(args, km: KeyManager):
    """Create a new API key."""
    raw_key, api_key = km.create_key(
        name=args.name,
        role=args.role,
        rate_limit=args.rate_limit,
    )
    print("\n✅ API Key Created")
    print(f"   Name:      {api_key.name}")
    print(f"   Role:      {api_key.role}")
    print(f"   Key ID:    {api_key.key_id}")
    print(f"   API Key:   {raw_key}")
    print("\n⚠️  Save this key now — it will NOT be shown again!\n")


def cmd_list_keys(_args, km: KeyManager):
    """List all API keys."""
    keys = km.list_keys()
    if not keys:
        print("No API keys found.")
        return

    print(
        f"\n{'Key ID':<25} {'Name':<20} {'Role':<12} {'Active':<8} {'Created':<20} {'Last Used':<20}"
    )  # pylint: disable=line-too-long
    print("─" * 105)
    for k in keys:
        print(
            f"{k.key_id:<25} {k.name:<20} {k.role:<12} "
            f"{'✓' if k.is_active else '✗':<8} "
            f"{_format_time(k.created_at):<20} {_format_time(k.last_used):<20}"
        )
    print()


def cmd_revoke_key(args, km: KeyManager):
    """Revoke an API key."""
    success = km.revoke_key(args.key_id)
    if success:
        print(f"✅ Key {args.key_id} revoked.")
    else:
        print(f"❌ Key {args.key_id} not found.")
        sys.exit(1)


def cmd_rotate_key(args, km: KeyManager):
    """Rotate an API key."""
    result = km.rotate_key(args.key_id)
    if result:
        raw_key, new_key = result
        print("\n✅ Key Rotated")
        print(f"   Old Key ID: {args.key_id} (revoked)")
        print(f"   New Key ID: {new_key.key_id}")
        print(f"   New API Key: {raw_key}")
        print("\n⚠️  Save this key now — it will NOT be shown again!\n")
    else:
        print(f"❌ Key {args.key_id} not found.")
        sys.exit(1)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="al-furqan-keys",
        description="Al-Furqan API Key Management",
    )
    parser.add_argument(
        "--storage",
        default=None,
        help="Path to API keys JSON file (default: ~/.al-furqan/api_keys.json)",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # create-key
    create_parser = subparsers.add_parser("create-key", help="Create a new API key")
    create_parser.add_argument("--name", required=True, help="Human-readable name")
    create_parser.add_argument(
        "--role", default="reader", choices=APIKey.ROLES, help="Key role"
    )
    create_parser.add_argument(
        "--rate-limit", type=int, default=0, help="Requests per minute (0=default)"
    )  # pylint: disable=line-too-long

    # list-keys
    subparsers.add_parser("list-keys", help="List all API keys")

    # revoke-key
    revoke_parser = subparsers.add_parser("revoke-key", help="Revoke an API key")
    revoke_parser.add_argument("key_id", help="Key ID to revoke")

    # rotate-key
    rotate_parser = subparsers.add_parser("rotate-key", help="Rotate an API key")
    rotate_parser.add_argument("key_id", help="Key ID to rotate")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    km = KeyManager(storage_path=args.storage)

    commands = {
        "create-key": cmd_create_key,
        "list-keys": cmd_list_keys,
        "revoke-key": cmd_revoke_key,
        "rotate-key": cmd_rotate_key,
    }

    commands[args.command](args, km)


if __name__ == "__main__":
    main()
