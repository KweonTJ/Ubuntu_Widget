#!/bin/bash
set -euo pipefail
project_root="$(cd -- "$(dirname -- "$0")/.." && pwd)"
upstream_commit=48f5aa8b379adf29da0b0bb9ca04164f65d8bdaa
source_dir="$project_root/.build/eww-source"
for dependency in git cargo rustup pkg-config cc; do
  command -v "$dependency" >/dev/null || { echo "Missing build tool: $dependency. See README.md." >&2; exit 1; }
done
pkg-config --exists gtk+-3.0 dbusmenu-gtk3-0.4 || { echo 'Install libgtk-3-dev and libdbusmenu-gtk3-dev first.' >&2; exit 1; }
mkdir -p -- "$project_root/.build" "$project_root/build"
if [ ! -d "$source_dir/.git" ]; then
  git init -q "$source_dir"
  git -C "$source_dir" remote add origin https://github.com/elkowar/eww.git
  git -C "$source_dir" fetch --depth=1 origin "$upstream_commit"
  git -C "$source_dir" checkout --detach FETCH_HEAD
fi
[ "$(git -C "$source_dir" rev-parse HEAD)" = "$upstream_commit" ] || { echo 'Unexpected source revision. Move .build/eww-source aside and retry.' >&2; exit 1; }
if git -C "$source_dir" apply --reverse --check "$project_root/patches/eww-native-controls.patch" 2>/dev/null; then
  echo 'Native control patch already applied.'
else
  git -C "$source_dir" apply --check "$project_root/patches/eww-native-controls.patch"
  git -C "$source_dir" apply "$project_root/patches/eww-native-controls.patch"
fi
# Override the old upstream toolchain with the user's installed stable Rust.
# Remap this machine's source directory out of Rust diagnostics in the result.
export CARGO_ENCODED_RUSTFLAGS="${CARGO_ENCODED_RUSTFLAGS:+$CARGO_ENCODED_RUSTFLAGS$'\x1f'}--remap-path-prefix=$source_dir=eww-source"
widget_target_dir="${CARGO_TARGET_DIR:-$source_dir/target}"
mkdir -p -- "$widget_target_dir"
export CARGO_TARGET_DIR="$(cd -- "$widget_target_dir" && pwd)"
(
  cd -- "$source_dir"
  cargo +"${RUST_TOOLCHAIN:-stable}" build --locked --release --no-default-features --features x11
)
cp -- "$CARGO_TARGET_DIR/release/eww" "$project_root/build/eww"
printf '%s\n' "$upstream_commit" > "$project_root/build/upstream-commit.txt"
echo "Built $project_root/build/eww"
