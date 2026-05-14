# How to use Platformio Core on this project

Here is a practical guide to set up your dev environment with `clangd` able to
correctly match the Platformio deps in your favorite editor.

No VSCode, Platformio CLI only.

> Inspired by [this template](https://github.com/ironlungx/nvim-pio/tree/main)

## Prerequisities

- `clangd` ready to be run in your IDE.
- `python` (with no required extra package)

## Instructions

1. At the root of this repository, setup the PlatformIO project for an external
   IDE:

   ```sh
   # Even if you are not in vim, this will work
   pio init --ide vim
   ```

2. Generate the `clangd` helper files:

   ```sh
   python3 conv.py
   ```

3. Be sure your IDE's LSP client run `clangd` in background with the
   `--background-index` option
