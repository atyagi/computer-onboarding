"""CLI entry point for macsetup."""

import argparse
import os
import sys
from pathlib import Path

from macsetup import __version__

# Default config directory
DEFAULT_CONFIG_DIR = Path.home() / ".config" / "macsetup"


def get_config_dir() -> Path:
    """Get the configuration directory, respecting environment variable override."""
    env_dir = os.environ.get("MACSETUP_CONFIG_DIR")
    if env_dir:
        return Path(env_dir)
    return DEFAULT_CONFIG_DIR


def add_global_options(parser: argparse.ArgumentParser) -> None:
    """Add global options that apply to all commands."""
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=None,
        metavar="PATH",
        help=f"Override config directory (default: {DEFAULT_CONFIG_DIR})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format (for scripting)",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress non-essential output",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug output",
    )


def cmd_capture(args: argparse.Namespace) -> int:
    """Handle the capture command."""
    import json

    from macsetup.models.config import save_config
    from macsetup.services.capture import CaptureService

    config_dir = args.resolved_config_dir

    # Parse dotfiles list
    dotfiles = []
    if args.dotfiles:
        dotfiles = [d.strip() for d in args.dotfiles.split(",") if d.strip()]

    # Parse preference domains
    preference_domains = []
    if args.preferences:
        preference_domains = [p.strip() for p in args.preferences.split(",") if p.strip()]

    # Progress callback
    def progress(message: str, current: int, total: int):
        if not args.quiet and not args.json:
            print(f"  [{current}/{total}] {message}")

    service = CaptureService(
        config_dir=config_dir,
        profile=args.profile,
        dotfiles=dotfiles,
        preference_domains=preference_domains,
        skip_apps=args.skip_apps,
        skip_dotfiles=args.skip_dotfiles,
        skip_preferences=args.skip_preferences,
        progress_callback=progress,
    )

    if not args.quiet and not args.json:
        print(f"Capturing configuration to {config_dir} (profile: {args.profile})")
        print()

    config = service.capture()

    # Save configuration
    config_path = config_dir / "config.yaml"
    save_config(config, config_path)

    if args.json:
        from macsetup.models.config import config_to_dict

        output = {
            "success": True,
            "config_path": str(config_path),
            "profile": args.profile,
            "config": config_to_dict(config),
        }
        print(json.dumps(output, indent=2))
    elif not args.quiet:
        profile = config.profiles[args.profile]
        print()
        print(f"Configuration saved to {config_path}")
        apps = profile.applications
        if apps and apps.homebrew:
            brew = apps.homebrew
            print(
                f"  Homebrew: {len(brew.taps)} taps, "
                f"{len(brew.formulas)} formulas, {len(brew.casks)} casks"
            )
        if apps and apps.mas:
            print(f"  Mac App Store: {len(apps.mas)} apps")
        if profile.dotfiles:
            print(f"  Dotfiles: {len(profile.dotfiles)} files")
        if profile.preferences:
            print(f"  Preferences: {len(profile.preferences)} domains")

    return 0


def cmd_setup(args: argparse.Namespace) -> int:
    """Handle the setup command."""
    import json

    from macsetup.models.config import load_config
    from macsetup.services.setup import SetupService

    config_path = args.resolved_config_dir / "config.yaml"

    # Check if config exists
    if not config_path.exists():
        if args.json:
            print(json.dumps({"success": False, "error": "Configuration file not found"}))
        else:
            print(f"Error: Configuration file not found: {config_path}")
            print("Run 'macsetup capture' first to create a configuration.")
        return 2

    # Load configuration
    try:
        config = load_config(config_path)
    except Exception as e:
        if args.json:
            print(json.dumps({"success": False, "error": f"Invalid configuration: {e}"}))
        else:
            print(f"Error: Invalid configuration file: {e}")
        return 2

    # Check if profile exists
    if args.profile not in config.profiles:
        if args.json:
            print(json.dumps({"success": False, "error": f"Profile not found: {args.profile}"}))
        else:
            print(f"Error: Profile '{args.profile}' not found")
            print(f"Available profiles: {', '.join(config.profiles.keys())}")
        return 2

    # Dry-run mode
    if args.dry_run:
        if not args.quiet:
            print(f"Dry-run: would apply profile '{args.profile}'")
        # TODO: implement preview output
        return 0

    # Progress callback
    def progress(message: str, current: int, total: int):
        if not args.quiet and not args.json:
            print(f"  [{current}/{total}] {message}")

    # Create and run setup service
    service = SetupService(
        config=config,
        config_dir=args.resolved_config_dir,
        profile=args.profile,
        force=args.force,
        skip_dotfiles=args.no_dotfiles,
        skip_preferences=args.no_preferences,
        progress_callback=progress,
    )

    if not args.quiet and not args.json:
        print(f"Applying configuration from {config_path} (profile: {args.profile})")
        print()

    result = service.run(resume=args.resume)

    # Output results
    if args.json:
        output = {
            "success": result.success and result.failed_count == 0,
            "completed": result.completed_count,
            "failed": result.failed_count,
            "failures": [
                {"type": f.type, "identifier": f.identifier, "error": f.error}
                for f in result.failed_items
            ],
            "manual_required": [{"name": m.name, "url": m.url} for m in result.manual_apps],
        }
        print(json.dumps(output, indent=2))
    else:
        if not args.quiet:
            print()
            if result.failed_count > 0:
                print(f"Setup complete with {result.failed_count} failure(s):")
                for f in result.failed_items:
                    print(f"  - {f.type}:{f.identifier}: {f.error}")
            else:
                print("Setup complete!")

            if result.manual_apps:
                print()
                print("Manual steps required:")
                for m in result.manual_apps:
                    if m.url:
                        print(f"  - {m.name}: {m.url}")
                    else:
                        print(f"  - {m.name}")

    # Return appropriate exit code
    if result.interrupted:
        return 130
    if result.failed_count > 0:
        return 3
    return 0


def cmd_preview(args: argparse.Namespace) -> int:
    """Handle the preview command."""
    import json

    from macsetup.models.config import load_config
    from macsetup.services.preview import PreviewService

    config_path = args.resolved_config_dir / "config.yaml"

    if not config_path.exists():
        if args.json:
            print(json.dumps({"success": False, "error": "Configuration file not found"}))
        else:
            print(f"Error: Configuration file not found: {config_path}")
            print("Run 'macsetup capture' first to create a configuration.")
        return 2

    try:
        config = load_config(config_path)
    except Exception as e:
        if args.json:
            print(json.dumps({"success": False, "error": f"Invalid configuration: {e}"}))
        else:
            print(f"Error: Invalid configuration file: {e}")
        return 2

    if args.profile not in config.profiles:
        if args.json:
            print(json.dumps({"success": False, "error": f"Profile not found: {args.profile}"}))
        else:
            print(f"Error: Profile '{args.profile}' not found")
            print(f"Available profiles: {', '.join(config.profiles.keys())}")
        return 2

    service = PreviewService(config=config, profile=args.profile)

    if args.diff:
        diff = service.diff()
        if args.json:
            # Serialize MacApp objects in diff
            serializable_diff = {}
            for key, value in diff.items():
                if value and hasattr(value[0], "id") if value else False:
                    serializable_diff[key] = [{"id": a.id, "name": a.name} for a in value]
                else:
                    serializable_diff[key] = value
            print(json.dumps({"success": True, "diff": serializable_diff}, indent=2))
        else:
            if not args.quiet:
                print(f"Diff for profile '{args.profile}':")
                print()
                for key in ["taps", "formulas", "casks", "mas"]:
                    to_install = diff.get(f"{key}_to_install", [])
                    installed = diff.get(f"{key}_installed", [])
                    if to_install or installed:
                        print(f"  {key.capitalize()}:")
                        for item in to_install:
                            name = f"{item.id} ({item.name})" if hasattr(item, "id") else item
                            print(f"    + {name}")
                        for item in installed:
                            name = f"{item.id} ({item.name})" if hasattr(item, "id") else item
                            print(f"    = {name} (installed)")
    else:
        items = service.preview()
        if args.json:
            print(json.dumps({"success": True, "preview": items}, indent=2))
        elif not args.quiet:
            print(f"Preview for profile '{args.profile}':")
            print()
            if items["taps"]:
                print(f"  Taps ({len(items['taps'])}):")
                for t in items["taps"]:
                    print(f"    - {t}")
            if items["formulas"]:
                print(f"  Formulas ({len(items['formulas'])}):")
                for f in items["formulas"]:
                    print(f"    - {f}")
            if items["casks"]:
                print(f"  Casks ({len(items['casks'])}):")
                for c in items["casks"]:
                    print(f"    - {c}")
            if items["mas"]:
                print(f"  Mac App Store ({len(items['mas'])}):")
                for a in items["mas"]:
                    print(f"    - {a['name']} ({a['id']})")
            if items["dotfiles"]:
                print(f"  Dotfiles ({len(items['dotfiles'])}):")
                for d in items["dotfiles"]:
                    print(f"    - {d['path']} ({d['mode']})")
            if items["preferences"]:
                print(f"  Preferences ({len(items['preferences'])}):")
                for p in items["preferences"]:
                    print(f"    - {p['domain']} {p.get('key', '')}")

    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    """Handle the sync command."""
    import json

    from macsetup.services.sync import SyncService

    config_dir = args.resolved_config_dir
    sync_cmd = getattr(args, "sync_command", None)

    if sync_cmd is None:
        print("Usage: macsetup sync {start|stop|status|now}")
        return 0

    service = SyncService(
        config_dir=config_dir,
        interval_minutes=getattr(args, "interval", 60),
        watch=getattr(args, "watch", True),
    )

    if sync_cmd == "now":
        if not args.quiet and not args.json:
            print("Running sync...")
        success = service.sync_now()
        if args.json:
            print(json.dumps({"success": success}))
        elif not args.quiet:
            if success:
                print("Sync complete.")
            else:
                print("Error: Sync failed.")
        return 0 if success else 1

    elif sync_cmd == "status":
        status = service.status()
        if args.json:
            print(json.dumps(status))
        elif not args.quiet:
            if status["running"]:
                print("Sync daemon is running.")
            else:
                print("Sync daemon is not running.")
            print(f"  Interval: {status['interval_minutes']} minutes")
            print(f"  Config: {status['config_dir']}")
        return 0

    elif sync_cmd == "stop":
        stopped = service.stop()
        if args.json:
            print(json.dumps({"stopped": stopped}))
        elif not args.quiet:
            if stopped:
                print("Sync daemon stopped.")
            else:
                print("Sync daemon is not running.")
        return 0

    elif sync_cmd == "start":
        if service.is_running():
            if args.json:
                print(json.dumps({"success": False, "error": "Already running"}))
            elif not args.quiet:
                print("Sync daemon is already running.")
            return 1
        # For foreground "start", just run once and inform about daemon mode
        if not args.quiet and not args.json:
            print(f"Sync started (interval: {service.interval_minutes} minutes)")
            print("Running initial sync...")
        success = service.sync_now()
        if args.json:
            print(json.dumps({"success": success}))
        elif not args.quiet:
            if success:
                print("Initial sync complete.")
            else:
                print("Error: Initial sync failed.")
        return 0 if success else 1

    return 0


def cmd_profile(args: argparse.Namespace) -> int:
    """Handle the profile command."""
    import json

    from macsetup.models.config import load_config
    from macsetup.services.preview import PreviewService

    config_path = args.resolved_config_dir / "config.yaml"
    profile_cmd = getattr(args, "profile_command", None)

    if profile_cmd is None:
        print("Usage: macsetup profile {list|show|create|delete|diff}")
        return 0

    if not config_path.exists():
        if args.json:
            print(json.dumps({"success": False, "error": "Configuration file not found"}))
        else:
            print(f"Error: Configuration file not found: {config_path}")
        return 2

    try:
        config = load_config(config_path)
    except Exception as e:
        if args.json:
            print(json.dumps({"success": False, "error": str(e)}))
        else:
            print(f"Error: {e}")
        return 2

    if profile_cmd == "list":
        profiles = list(config.profiles.keys())
        if args.json:
            print(json.dumps({"profiles": profiles}))
        elif not args.quiet:
            print("Profiles:")
            for name in profiles:
                p = config.profiles[name]
                desc = f" - {p.description}" if p.description else ""
                extends = f" (extends: {p.extends})" if p.extends else ""
                print(f"  {name}{extends}{desc}")
        return 0

    elif profile_cmd == "show":
        name = args.name
        if name not in config.profiles:
            if args.json:
                print(json.dumps({"success": False, "error": f"Profile not found: {name}"}))
            else:
                print(f"Error: Profile '{name}' not found")
            return 2
        service = PreviewService(config=config, profile=name)
        items = service.preview()
        if args.json:
            print(json.dumps({"profile": name, "items": items}, indent=2))
        elif not args.quiet:
            print(f"Profile: {name}")
            p = config.profiles[name]
            if p.description:
                print(f"  Description: {p.description}")
            if p.extends:
                print(f"  Extends: {p.extends}")
            print(f"  Formulas: {len(items['formulas'])}")
            print(f"  Casks: {len(items['casks'])}")
            print(f"  MAS apps: {len(items['mas'])}")
            print(f"  Dotfiles: {len(items['dotfiles'])}")
            print(f"  Preferences: {len(items['preferences'])}")
        return 0

    elif profile_cmd == "diff":
        name1 = args.name1
        name2 = args.name2
        for name in [name1, name2]:
            if name not in config.profiles:
                if args.json:
                    print(json.dumps({"success": False, "error": f"Profile not found: {name}"}))
                else:
                    print(f"Error: Profile '{name}' not found")
                return 2

        svc1 = PreviewService(config=config, profile=name1)
        svc2 = PreviewService(config=config, profile=name2)
        items1 = svc1.preview()
        items2 = svc2.preview()

        if args.json:
            print(json.dumps({name1: items1, name2: items2}, indent=2))
        elif not args.quiet:
            print(f"Comparing {name1} vs {name2}:")
            for key in ["formulas", "casks", "taps"]:
                set1 = set(items1[key])
                set2 = set(items2[key])
                only1 = set1 - set2
                only2 = set2 - set1
                if only1 or only2:
                    print(f"  {key.capitalize()}:")
                    for item in sorted(only1):
                        print(f"    - {item} (only in {name1})")
                    for item in sorted(only2):
                        print(f"    + {item} (only in {name2})")
        return 0

    elif profile_cmd in ("create", "delete"):
        if not args.quiet and not args.json:
            print(f"Profile {profile_cmd} requires manual editing of config.yaml")
        return 0

    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Handle the validate command."""
    import json

    import yaml

    from macsetup.models.schema import validate_config

    config_path = args.resolved_config_dir / "config.yaml"

    if not config_path.exists():
        if args.json:
            print(json.dumps({"valid": False, "error": "Configuration file not found"}))
        else:
            print(f"Error: Configuration file not found: {config_path}")
        return 2

    # Try loading as YAML
    try:
        with open(config_path) as f:
            config_data = yaml.safe_load(f)
    except Exception as e:
        if args.json:
            print(json.dumps({"valid": False, "error": f"Invalid YAML: {e}"}))
        else:
            print(f"Error: Invalid configuration: {e}")
        return 1

    # Validate against schema
    errors = validate_config(config_data)

    if errors:
        if args.json:
            print(json.dumps({"valid": False, "errors": errors}))
        else:
            print(f"Validation failed with {len(errors)} error(s):")
            for err in errors:
                print(f"  - {err}")
        return 1

    if args.json:
        print(json.dumps({"valid": True}))
    elif not args.quiet:
        print(f"Configuration is valid: {config_path}")

    return 0


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="macsetup",
        description="macOS Configuration Sync CLI - Capture, store, and restore macOS machine configurations",
    )
    add_global_options(parser)

    subparsers = parser.add_subparsers(dest="command", title="commands")

    # capture command
    capture_parser = subparsers.add_parser(
        "capture",
        help="Capture current machine configuration",
        description="Capture current machine configuration to a YAML file.",
    )
    capture_parser.add_argument(
        "--profile",
        default="default",
        metavar="NAME",
        help="Profile to capture to (default: default)",
    )
    capture_parser.add_argument(
        "--dotfiles",
        metavar="PATHS",
        help="Additional dotfiles to capture (comma-separated)",
    )
    capture_parser.add_argument(
        "--preferences",
        metavar="DOMAINS",
        help="Additional preference domains (comma-separated)",
    )
    capture_parser.add_argument(
        "--skip-apps",
        action="store_true",
        help="Skip application capture",
    )
    capture_parser.add_argument(
        "--skip-dotfiles",
        action="store_true",
        help="Skip dotfile capture",
    )
    capture_parser.add_argument(
        "--skip-preferences",
        action="store_true",
        help="Skip preference capture",
    )
    capture_parser.set_defaults(func=cmd_capture)

    # setup command
    setup_parser = subparsers.add_parser(
        "setup",
        help="Apply configuration to current machine",
        description="Apply configuration from YAML file to current machine.",
    )
    setup_parser.add_argument(
        "--profile",
        default="default",
        metavar="NAME",
        help="Profile to apply (default: default)",
    )
    setup_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    setup_parser.add_argument(
        "--include",
        metavar="ITEMS",
        help="Only install these items (comma-separated)",
    )
    setup_parser.add_argument(
        "--exclude",
        metavar="ITEMS",
        help="Skip these items (comma-separated)",
    )
    setup_parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume interrupted setup",
    )
    setup_parser.add_argument(
        "--force",
        action="store_true",
        help="Reinstall already-installed items",
    )
    setup_parser.add_argument(
        "--no-dotfiles",
        action="store_true",
        help="Skip dotfile setup",
    )
    setup_parser.add_argument(
        "--no-preferences",
        action="store_true",
        help="Skip preference setup",
    )
    setup_parser.set_defaults(func=cmd_setup)

    # preview command
    preview_parser = subparsers.add_parser(
        "preview",
        help="Show what setup would do",
        description="Preview what setup would do without making changes.",
    )
    preview_parser.add_argument(
        "--profile",
        default="default",
        metavar="NAME",
        help="Profile to preview (default: default)",
    )
    preview_parser.add_argument(
        "--diff",
        action="store_true",
        help="Show what's different from current state",
    )
    preview_parser.set_defaults(func=cmd_preview)

    # sync command
    sync_parser = subparsers.add_parser(
        "sync",
        help="Manage background sync daemon",
        description="Manage background sync daemon.",
    )
    sync_subparsers = sync_parser.add_subparsers(dest="sync_command", title="subcommands")

    sync_start = sync_subparsers.add_parser("start", help="Start background sync")
    sync_start.add_argument(
        "--interval",
        type=int,
        default=60,
        metavar="MINUTES",
        help="Sync interval in minutes (default: 60)",
    )
    sync_start.add_argument(
        "--watch",
        action="store_true",
        default=True,
        help="Watch dotfiles for changes (default: true)",
    )

    sync_subparsers.add_parser("stop", help="Stop background sync")
    sync_subparsers.add_parser("status", help="Show sync status")
    sync_subparsers.add_parser("now", help="Run sync immediately")
    sync_parser.set_defaults(func=cmd_sync)

    # profile command
    profile_parser = subparsers.add_parser(
        "profile",
        help="Manage configuration profiles",
        description="Manage configuration profiles.",
    )
    profile_subparsers = profile_parser.add_subparsers(dest="profile_command", title="subcommands")

    profile_subparsers.add_parser("list", help="List all profiles")

    profile_show = profile_subparsers.add_parser("show", help="Show profile details")
    profile_show.add_argument("name", help="Profile name")

    profile_create = profile_subparsers.add_parser("create", help="Create new profile")
    profile_create.add_argument("name", help="Profile name")

    profile_delete = profile_subparsers.add_parser("delete", help="Delete profile")
    profile_delete.add_argument("name", help="Profile name")

    profile_diff = profile_subparsers.add_parser("diff", help="Compare two profiles")
    profile_diff.add_argument("name1", help="First profile name")
    profile_diff.add_argument("name2", help="Second profile name")

    profile_parser.set_defaults(func=cmd_profile)

    # validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate configuration file",
        description="Validate configuration file against schema.",
    )
    validate_parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on warnings",
    )
    validate_parser.set_defaults(func=cmd_validate)

    return parser


def main(args: list[str] | None = None) -> int:
    """Main entry point for macsetup CLI."""
    parser = create_parser()
    parsed = parser.parse_args(args)

    # If no command specified, show help
    if parsed.command is None:
        parser.print_help()
        return 0

    # Resolve config directory
    config_dir = parsed.config_dir or get_config_dir()

    # Store resolved config dir in namespace for commands to use
    parsed.resolved_config_dir = config_dir

    # macOS version compatibility check
    if parsed.command in ("setup", "capture") and not getattr(parsed, "quiet", False):
        from macsetup.services.setup import SetupService

        warning = SetupService.check_macos_version()
        if warning and not getattr(parsed, "json", False):
            print(warning)
            print()

    # Call the command handler
    return parsed.func(parsed)


if __name__ == "__main__":
    sys.exit(main())
