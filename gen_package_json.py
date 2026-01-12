import argparse
import json


def read_file(path):
    with open(path, "r") as f:
        return f.read().strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--extension_entry")

    parser.add_argument("--package_name")
    parser.add_argument("--package_name_file")

    parser.add_argument("--display_name")
    parser.add_argument("--display_name_file")

    parser.add_argument("--version")
    parser.add_argument("--version_file")

    parser.add_argument("--icon")

    parser.add_argument("--allowed_hosts")
    parser.add_argument("--allowed_hosts_file")

    parser.add_argument("--allowed_paths")
    parser.add_argument("--allowed_paths_file")

    args = parser.parse_args()

    data = {"extensionEntry": args.extension_entry, "moosyncExtension": True}

    if args.package_name:
        data["name"] = args.package_name
    elif args.package_name_file:
        data["name"] = read_file(args.package_name_file)

    if args.display_name:
        data["displayName"] = args.display_name
    elif args.display_name_file:
        data["displayName"] = read_file(args.display_name_file)

    if args.version:
        data["version"] = args.version
    elif args.version_file:
        data["version"] = read_file(args.version_file)

    if args.icon:
        data["icon"] = args.icon

    perms = {}
    hosts = []
    if args.allowed_hosts:
        hosts = json.loads(args.allowed_hosts)
    elif args.allowed_hosts_file:
        c = read_file(args.allowed_hosts_file)
        try:
            hosts = json.loads(c)
        except Exception:
            hosts = [line.strip() for line in c.splitlines() if line.strip()]
    if hosts:
        perms["hosts"] = hosts

    paths = {}
    if args.allowed_paths:
        paths = json.loads(args.allowed_paths)
    elif args.allowed_paths_file:
        paths = json.loads(read_file(args.allowed_paths_file))
    if paths:
        perms["paths"] = paths

    if perms:
        data["permissions"] = perms

    with open(args.output, "w") as f:
        json.dump(data, f, indent=4)


if __name__ == "__main__":
    main()
