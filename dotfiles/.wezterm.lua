local wezterm = require 'wezterm'
local mux = wezterm.mux
local act = wezterm.action
local config = {}
local keys = {}
local mouse_bindings = {}
local launch_menu = {}
local haswork,work = pcall(require,"work")

--- Disable defaul keys and set some minimum ones for now.
--- This helps with conflicting keys in pwsh
keys = {
  { key = 'Tab', mods = 'CTRL', action = act.ActivateTabRelative(1) },
  { key = 'Tab', mods = 'SHIFT|CTRL', action = act.ActivateTabRelative(-1) },
  { key = 'RightArrow', mods = 'SHIFT|CTRL', action = act.ActivateTabRelative(1) },
  { key = 'LeftArrow', mods = 'SHIFT|CTRL', action = act.ActivateTabRelative(-1) },
  -- { key = 'Enter', mods = 'ALT', action = act.ToggleFullScreen },
  -- { key = '\"', mods = 'ALT|CTRL', action = act.SplitVertical{ domain =  'CurrentPaneDomain' } },
  -- { key = '\"', mods = 'SHIFT|ALT|CTRL', action = act.SplitVertical{ domain =  'CurrentPaneDomain' } },
  { key = '%', mods = 'ALT|CTRL', action = act.SplitHorizontal{ domain =  'CurrentPaneDomain' } },
  { key = '%', mods = 'SHIFT|ALT|CTRL', action = act.SplitHorizontal{ domain =  'CurrentPaneDomain' } },
  { key = '\'', mods = 'SHIFT|ALT|CTRL', action = act.SplitVertical{ domain =  'CurrentPaneDomain' } },
  { key = ')', mods = 'CTRL', action = act.ResetFontSize },
  { key = ')', mods = 'SHIFT|CTRL', action = act.ResetFontSize },
  { key = '+', mods = 'CTRL', action = act.IncreaseFontSize },
  { key = '+', mods = 'SHIFT|CTRL', action = act.IncreaseFontSize },
  { key = '-', mods = 'CTRL', action = act.DecreaseFontSize },
  { key = '-', mods = 'SHIFT|CTRL', action = act.DecreaseFontSize },
  { key = '-', mods = 'SUPER', action = act.DecreaseFontSize },
  { key = '0', mods = 'CTRL', action = act.ResetFontSize },
  { key = '0', mods = 'SHIFT|CTRL', action = act.ResetFontSize },
  { key = '0', mods = 'SUPER', action = act.ResetFontSize },
  { key = '=', mods = 'CTRL', action = act.IncreaseFontSize },
  { key = '=', mods = 'SHIFT|CTRL', action = act.IncreaseFontSize },
  { key = '=', mods = 'SUPER', action = act.IncreaseFontSize },
  { key = 'C', mods = 'SHIFT|CTRL', action = act.CopyTo 'Clipboard' },
  { key = 'F', mods = 'SHIFT|CTRL', action = act.Search 'CurrentSelectionOrEmptyString' },
  { key = 'K', mods = 'SHIFT|CTRL', action = act.ClearScrollback 'ScrollbackOnly' },
  { key = 'L', mods = 'SHIFT|CTRL', action = act.ShowDebugOverlay },
  { key = 'N', mods = 'CTRL', action = act.SpawnWindow },
  { key = 'P', mods = 'CTRL', action = act.ActivateCommandPalette },
  { key = 'R', mods = 'SHIFT|CTRL', action = act.ReloadConfiguration },
  -- { key = 'T', mods = 'SHIFT|CTRL', action = act.ShowLauncher },
  { key = 'T', mods = 'SHIFT|CTRL', action = act.SpawnTab 'DefaultDomain' },
  { key = 'V', mods = 'CTRL', action = act.PasteFrom 'Clipboard' },
  { key = 'W', mods = 'CTRL', action = act.CloseCurrentTab{ confirm = true } },
  { key = 'W', mods = 'SHIFT|CTRL', action = act.CloseCurrentTab{ confirm = true } },
  { key = 'X', mods = 'SHIFT|CTRL', action = act.ActivateCopyMode },
  { key = 'Z', mods = 'SHIFT|CTRL', action = act.TogglePaneZoomState },
  { key = '[', mods = 'SHIFT|SUPER', action = act.ActivateTabRelative(-1) },
  { key = ']', mods = 'SHIFT|SUPER', action = act.ActivateTabRelative(1) },
  { key = '_', mods = 'CTRL', action = act.DecreaseFontSize },
  { key = '_', mods = 'SHIFT|CTRL', action = act.DecreaseFontSize },
  { key = 'c', mods = 'SHIFT|CTRL', action = act.CopyTo 'Clipboard' },
  { key = 'c', mods = 'SUPER', action = act.CopyTo 'Clipboard' },
  { key = 'f', mods = 'SHIFT|CTRL', action = act.Search 'CurrentSelectionOrEmptyString' },
  { key = 'k', mods = 'SHIFT|CTRL', action = act.ClearScrollback 'ScrollbackOnly' },
  { key = 'k', mods = 'SUPER', action = act.ClearScrollback 'ScrollbackOnly' },
  { key = 'l', mods = 'SHIFT|CTRL', action = act.ShowDebugOverlay },
  { key = 'm', mods = 'SHIFT|CTRL', action = act.Hide },
  { key = 'n', mods = 'SUPER', action = act.SpawnWindow },
  { key = 'r', mods = 'SHIFT|CTRL', action = act.ReloadConfiguration },
  { key = 'r', mods = 'SUPER', action = act.ReloadConfiguration },
  -- { key = 't', mods = 'SHIFT|CTRL', action = act.ShowLauncher },
  -- { key = 't', mods = 'SUPER', action = act.ShowLauncher },
  { key = 't', mods = 'SHIFT|CTRL', action = act.SpawnTab 'DefaultDomain' },
  { key = 't', mods = 'SUPER', action = act.SpawnTab 'DefaultDomain' },
  { key = 'u', mods = 'SHIFT|CTRL', action = act.CharSelect{ copy_on_select = true, copy_to =  'ClipboardAndPrimarySelection' } },
  { key = 'v', mods = 'SUPER', action = act.PasteFrom 'Clipboard' },
  { key = 'w', mods = 'SHIFT|CTRL', action = act.CloseCurrentTab{ confirm = true } },
  { key = 'w', mods = 'SUPER', action = act.CloseCurrentTab{ confirm = true } },
  { key = 'x', mods = 'SHIFT|CTRL', action = act.ActivateCopyMode },
  { key = 'z', mods = 'SHIFT|CTRL', action = act.TogglePaneZoomState },
  { key = '{', mods = 'SUPER', action = act.ActivateTabRelative(-1) },
  { key = '{', mods = 'SHIFT|SUPER', action = act.ActivateTabRelative(-1) },
  { key = '}', mods = 'SUPER', action = act.ActivateTabRelative(1) },
  { key = '}', mods = 'SHIFT|SUPER', action = act.ActivateTabRelative(1) },
  { key = 'phys:Space', mods = 'SHIFT|CTRL', action = act.QuickSelect },
  { key = 'PageUp', mods = 'SHIFT', action = act.ScrollByPage(-1) },
  { key = 'PageUp', mods = 'CTRL', action = act.ActivateTabRelative(-1) },
  { key = 'PageUp', mods = 'SHIFT|CTRL', action = act.MoveTabRelative(-1) },
  { key = 'PageDown', mods = 'SHIFT', action = act.ScrollByPage(1) },
  { key = 'PageDown', mods = 'CTRL', action = act.ActivateTabRelative(1) },
  { key = 'PageDown', mods = 'SHIFT|CTRL', action = act.MoveTabRelative(1) },
  { key = 'LeftArrow', mods = 'SHIFT|ALT|CTRL', action = act.AdjustPaneSize{ 'Left', 1 } },
  -- Turning these off so I can use pwsh keys
  -- { key = 'LeftArrow', mods = 'SHIFT|CTRL', action = act.ActivatePaneDirection 'Left' },
  -- { key = 'RightArrow', mods = 'SHIFT|CTRL', action = act.ActivatePaneDirection 'Right' },
  -- Add these to allow quick moving between prompts
  { key = 'UpArrow', mods = 'SHIFT', action = act.ScrollToPrompt(-1) },
  { key = 'DownArrow', mods = 'SHIFT', action = act.ScrollToPrompt(1) },
  --
  { key = 'RightArrow', mods = 'SHIFT|ALT|CTRL', action = act.AdjustPaneSize{ 'Right', 1 } },
  { key = 'UpArrow', mods = 'SHIFT|CTRL', action = act.ActivatePaneDirection 'Up' },
  { key = 'UpArrow', mods = 'SHIFT|ALT|CTRL', action = act.AdjustPaneSize{ 'Up', 1 } },
  { key = 'DownArrow', mods = 'SHIFT|CTRL', action = act.ActivatePaneDirection 'Down' },
  { key = 'DownArrow', mods = 'SHIFT|ALT|CTRL', action = act.AdjustPaneSize{ 'Down', 1 } },
  { key = 'Insert', mods = 'SHIFT', action = act.PasteFrom 'PrimarySelection' },
  { key = 'Insert', mods = 'CTRL', action = act.CopyTo 'PrimarySelection' },
  { key = 'F11', mods = 'NONE', action = act.ToggleFullScreen },
  { key = 'Copy', mods = 'NONE', action = act.CopyTo 'Clipboard' },
  { key = 'Paste', mods = 'NONE', action = act.PasteFrom 'Clipboard' },
}

-- Mousing bindings
mouse_bindings = {
  -- Change the default click behavior so that it only selects
  -- text and doesn't open hyperlinks
  {
    event = { Up = { streak = 1, button = 'Left' } },
    mods = 'NONE',
    action = act.CompleteSelection 'ClipboardAndPrimarySelection',
  },

  -- and make CTRL-Click open hyperlinks
  {
    event = { Up = { streak = 1, button = 'Left' } },
    mods = 'CTRL',
    action = act.OpenLinkAtMouseCursor,
  },
  {
    event = { Down = { streak = 3, button = 'Left' } },
    action = wezterm.action.SelectTextAtMouseCursor 'SemanticZone',
    mods = 'NONE',
  },
}

--- Default config settings
config.scrollback_lines = 10000
config.hyperlink_rules = wezterm.default_hyperlink_rules()
config.hide_tab_bar_if_only_one_tab = false


-- Top5:
config.color_scheme = 'Paul Millr (Gogh)' -- top10, very balanced, best contrast
-- config.color_scheme = 'Builtin Tango Dark' -- GNOME Tango equivalent, with better white
-- config.color_scheme = 'Muse (terminal.sexy)' -- top10, good white, clear mc
-- config.color_scheme = 'Fahrenheit' -- really cool, yellowish/red, bit retro
-- config.color_scheme = 'Pro' -- similar to Tango and Paul Millr, but std iTerm colors

-- Best of
-- config.color_scheme = 'Google Dark (Gogh)' -- well composed, quite standard, balanced blue, lighter background
-- config.color_scheme = 'Unsifted Wheat (terminal.sexy)'
-- config.color_scheme = 'Ubuntu' -- just Ubuntu
-- config.color_scheme = 'Tango (terminal.sexy)'
-- config.color_scheme = 'synthwave' -- light blueish with pink
-- config.color_scheme = 'Symfonic' -- lila/violet dominance
-- config.color_scheme = 'Srcery (Gogh)' -- better brownish white, mc looks okayish
-- config.color_scheme = 'Spacedust (Gogh)' -- interesting brownish, good blue, bad frames
-- config.color_scheme = 'Sex Colors (terminal.sexy)' -- good white contrast, good mc, blueish tinted labels in ls
-- config.color_scheme = 'Pro' -- similar to Tango and Paul Millr, but std iTerm colors
-- config.color_scheme = 'Paul Millr (Gogh)' -- top10, very balanced, good contrast
-- config.color_scheme = 'Panels (terminal.sexy)' -- autumn, dark orange, good main white
-- config.color_scheme = 'Muse (terminal.sexy)' -- top10, good white, clear mc
-- config.color_scheme = 'midnight-in-mojave' -- well balances, bit light blue in mc
-- config.color_scheme = 'Matrix (terminal.sexy)' -- good contrast, 50 shades of green
-- config.color_scheme = 'Konsolas' -- very good contrast, darker white than Tango
-- config.color_scheme = 'Kasugano (terminal.sexy)' -- violet dominance, good white
-- config.color_scheme = 'iTerm2 Tango Light' -- coming later
-- config.color_scheme = 'iTerm2 Dark Background' -- coming later
-- config.color_scheme = 'Isotope (base16)' - juicy, some pink accents
-- config.color_scheme = 'IC_Orange_PPL' -- cool retro amber
-- config.color_scheme = 'Hurtado' -- well balanced, bit mono
-- config.color_scheme = 'Homebrew' -- xterm with green base font
-- config.color_scheme = 'Hipster Green' -- martix base, standard mc and others, mtrx for normal ppl
-- config.color_scheme = 'Harper' -- green mc, dark white
-- config.color_scheme = 'Green Screen (base16)' -- matrix, very retro-looking
-- config.color_scheme = 'Gotham (Gogh)' -- green/bluish dark, bit mono
-- config.color_scheme = 'Gnometerm (terminal.sexy)' -- Similar to Tango, bit more xterm
-- config.color_scheme = 'Fahrenheit' -- really cool, yellowish/red, bit retro
-- config.color_scheme = 'Dissonance (Gogh)' -- another high-contrast
-- config.color_scheme = 'deep' -- juicy colours, good contrast, weaker white than Tango
-- config.color_scheme = 'darkmoss (base16)' -- well balanced bleached Tango
-- config.color_scheme = 'Colors (base16)' -- quite balanced, juicy colors, grey white
-- config.color_scheme = 'Cobalt 2 (Gogh)' -- good contrast, dark blue/teal bg
-- config.color_scheme = 'Clone Of Ubuntu (Gogh)' -- Classic Ubuntu
-- config.color_scheme = 'City Streets (terminal.sexy)' -- b/w look, weak white
-- config.color_scheme = 'CGA' -- bit dark white, std mc look
-- config.color_scheme = 'Builtin Tango Dark' -- GNOME Tango equivalent
-- config.color_scheme = 'Brogrammer' -- Good contrasts, blueish
-- config.color_scheme = 'Adventure' -- pretty cool, bit too bueish in mc
-- config.color_scheme = 'Abernathy' -- Good white, awful blue
-- config.color_scheme = 'Tangoesque (terminal.sexy)' -- Too dark
-- config.color_scheme = 'AdventureTime'

config.font = wezterm.font_with_fallback {
  {
    family = 'Menlo'
  },
  {
    family = 'Liberation Mono'
  },
  {
    family = 'Menlo'
  },
  {
    family = 'Liberation Mono'
  },
  {
    family = 'Fira Code'
  },
  {
    family = 'Source Code Pro'
  },
  {
    family = 'Terminus',
  }
}
config.font_size = 14
config.launch_menu = launch_menu
config.default_cursor_style = 'SteadyBlock'
config.cursor_blink_rate = 0
config.animation_fps = 30
config.disable_default_key_bindings = true
config.keys = keys
config.mouse_bindings = mouse_bindings
config.window_close_confirmation = "NeverPrompt"
config.window_decorations = "RESIZE"

-- Allow overwriting for work stuff
if haswork then
  work.apply_to_config(config)
end

return config
