# Vimma theme for Omarchy

An [Omarchy](https://omarchy.org) theme in the colours of [Vimma](https://vimma.dev), the
keyboard-first browser: a deep teal-black background, aqua accent and a magenta neon. With it,
the terminal, editor, bar and lock screen match Vimma's own default theme.

## Install

```sh
omarchy theme install https://github.com/vimma-browser/omarchy-vimma-theme.git
```

Omarchy builds each app's colours (terminals, Neovim, btop, Hyprland and the rest) from
`colors.toml`, so the theme carries only the palette, the wallpapers and an icon set.

## Using it with Vimma

Vimma follows the current Omarchy theme when `vimma.theme.source` is `omarchy`. With this theme
the browser's colours match its built-in default, except the link hints: Vimma draws an Omarchy
theme's hints in its yellow, and its own built-in theme's in magenta.

## Licence

Mozilla Public License 2.0, as Vimma. The wallpapers use the Vimma logo.
