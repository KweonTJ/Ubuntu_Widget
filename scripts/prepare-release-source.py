#!/usr/bin/python3
"""Prepare matching engine/dependency source and redistribution license notices."""
import argparse
import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parent.parent


def tracked_files(root):
    names = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=root).decode().split('\0')
    return [root / name for name in sorted(set(filter(None, names)))]


def prepare(output):
    upstream = ROOT / '.build/eww-source'
    if not (upstream / 'Cargo.lock').is_file():
        raise ValueError('Build the pinned Eww engine first.')
    toolchain = os.environ.get('RUST_TOOLCHAIN', 'stable')
    metadata = json.loads(subprocess.check_output(['cargo', '+' + toolchain, 'metadata', '--locked', '--filter-platform', 'x86_64-unknown-linux-gnu', '--no-default-features', '--features', 'x11', '--format-version', '1'], cwd=upstream))
    version = (ROOT / 'VERSION').read_text().strip()
    stage = ROOT / 'build/release-source' / ('ubuntu-widget-' + version)
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    vendor_config = subprocess.check_output(['cargo', '+' + toolchain, 'vendor', '--locked', '--versioned-dirs', str(stage / 'vendor')], cwd=upstream, text=True)
    # Archive-relative paths allow rebuilding after extraction on another PC.
    vendor_config = vendor_config.replace(str(stage / 'vendor'), '../vendor')
    cargo_dir = stage / 'eww-source/.cargo'
    cargo_dir.mkdir(parents=True)
    (cargo_dir / 'config.toml').write_text(vendor_config)
    for source_root, destination in [(ROOT, stage / 'ubuntu-widget'), (upstream, stage / 'eww-source')]:
        for source in tracked_files(source_root):
            if not source.is_file() or source.is_symlink():
                raise ValueError('Unexpected source entry: ' + str(source))
            target = destination / source.relative_to(source_root)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            target.chmod(0o755 if os.access(source, os.X_OK) else 0o644)
    notices = ROOT / 'build/rust-licenses'
    if notices.exists():
        shutil.rmtree(notices)
    notices.mkdir(parents=True)
    index = []
    fetched = {}
    for package in sorted(metadata['packages'], key=lambda p: (p['name'], p['version'])):
        directory = Path(package['manifest_path']).parent
        destination = notices / (package['name'] + '-' + package['version'])
        destination.mkdir()
        candidates = [p for p in directory.iterdir() if p.is_file() and p.name.lower().startswith(('license', 'licence', 'copying', 'notice', 'copyright'))]
        if package.get('license_file'):
            candidates.append(directory / package['license_file'])
        if package['source'] is None:
            candidates.append(upstream / 'LICENSE')
        for source in set(candidates):
            shutil.copyfile(source, destination / source.name)
        if not candidates:
            # A few published crates omit their repository's root license.
            if package['license'] == 'LGPL-3.0-only':
                for name in ('LGPL-3', 'GPL-3'):
                    shutil.copyfile(Path('/usr/share/common-licenses') / name, destination / name)
            else:
                repository = (package.get('repository') or '').removesuffix('.git')
                vcs_file = directory / '.cargo_vcs_info.json'
                revision = json.loads(vcs_file.read_text()).get('git', {}).get('sha1', 'HEAD') if vcs_file.exists() else 'HEAD'
                key = (repository, revision)
                if key not in fetched:
                    found = {}
                    if repository.startswith('https://github.com/'):
                        for name in ('LICENSE', 'LICENSE-MIT', 'LICENSE-APACHE', 'COPYING'):
                            endpoint = 'repos/' + repository.removeprefix('https://github.com/') + '/contents/' + name + '?ref=' + revision
                            response = subprocess.run(['gh', 'api', endpoint], capture_output=True, text=True)
                            if response.returncode:
                                if '404' not in response.stderr:
                                    raise ValueError(response.stderr.strip())
                                continue
                            found[name] = base64.b64decode(json.loads(response.stdout)['content'])
                            break
                    fetched[key] = found
                for name, contents in fetched[key].items():
                    (destination / name).write_bytes(contents)
        if not any(destination.iterdir()):
            if package['license'] == 'MIT' and package.get('authors'):
                # Some crates declare MIT in Cargo.toml but publish no license
                # file, including at their pinned upstream revision. Retain
                # that declaration and author attribution with the MIT text;
                # do not pretend this is a file supplied by the upstream.
                permission = (ROOT / 'LICENSE').read_text().split('Permission is hereby granted', 1)[1]
                declaration = ('Upstream Cargo.toml declares license = "MIT".\n'
                               'Authors listed by upstream: ' + ', '.join(package['authors']) + '\n'
                               'Repository: ' + str(package.get('repository')) + '\n\n'
                               'Standard MIT permission text (no standalone license file was published):\n\n'
                               'Permission is hereby granted' + permission)
                (destination / 'MANIFEST-LICENSE.txt').write_text(declaration)
            else:
                raise ValueError('Missing redistribution license for ' + package['name'])
        index.append({k: package.get(k) for k in ('name', 'version', 'license', 'repository', 'source', 'authors')})
    (notices / 'INDEX.json').write_text(json.dumps(index, indent=2, ensure_ascii=False) + '\n')
    sysroot = Path(subprocess.check_output(['rustc', '+' + toolchain, '--print', 'sysroot'], text=True).strip())
    rust_notices = sysroot / 'share/doc/rust'
    for name in ('COPYRIGHT', 'COPYRIGHT.html', 'COPYRIGHT-library.html', 'LICENSE-MIT', 'LICENSE-APACHE'):
        if (rust_notices / name).is_file():
            shutil.copyfile(rust_notices / name, notices / ('Rust-' + name))
    if (rust_notices / 'licenses').is_dir():
        shutil.copytree(rust_notices / 'licenses', notices / 'Rust-licenses')
    shutil.copytree(notices, stage / 'rust-licenses')
    (stage / 'BUILD.md').write_text('''# Rebuild or relink the release engine

This archive includes the application source, the patched Eww source and the
Cargo.lock-pinned dependency source (including the LGPL-3.0 dbusmenu Rust bindings).
The corresponding notices are in rust-licenses/ and in the Debian package under
/usr/share/doc/ubuntu-widget/rust-licenses/. System GTK, GLib, X11 and related
libraries are dynamically linked and supplied by Ubuntu.

Install the Ubuntu build dependencies from ubuntu-widget/README.md and a current
stable Rust toolchain. The original release used Rust 1.99.0 on Ubuntu 22.04 amd64.
Then, from this extracted directory:

```bash
cd eww-source
cargo +stable build --offline --locked --release --no-default-features --features x11
cd ../ubuntu-widget
./install.sh --eww ../eww-source/target/release/eww
```

You may modify the application or LGPL library source and rebuild/relink it using
these steps. No signing key or device authorization is required. The project does
not restrict reverse engineering for debugging modifications to the LGPL libraries.
To substitute the engine in an existing Debian installation, run as your user:

```bash
EWW_WIDGET_BINARY=/path/to/modified/eww /usr/bin/ubuntu-widget restart
```

Upstream licenses apply to their respective files; the project's MIT license does
not replace them. The regular GitHub source archive alone does not contain the
vendored engine/dependency source; use this accompanying release source archive.
''')
    epoch = int(os.environ.get('SOURCE_DATE_EPOCH') or subprocess.check_output(['git', 'log', '-1', '--format=%ct'], cwd=ROOT, text=True))
    output.mkdir(parents=True, exist_ok=True)
    artifact = output / ('ubuntu-widget-' + version + '-source.tar.xz')
    with tarfile.open(artifact, 'w:xz', preset=3) as archive:
        def normalize(info):
            info.uid = info.gid = 0
            info.uname = info.gname = 'root'
            info.mtime = epoch
            return info
        archive.add(stage, arcname=stage.name, filter=normalize)
    print(artifact)
    print(f'Collected notices for {len(index)} Cargo packages plus the Rust toolchain.')
    return artifact


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist')
    args = parser.parse_args()
    try:
        prepare(args.output.resolve())
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, str(exc) + '\n')
