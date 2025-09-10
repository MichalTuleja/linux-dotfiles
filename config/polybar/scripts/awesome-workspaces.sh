#!/bin/bash

awesome-client <<'EOF' 2>/dev/null | sed -n 's/^.*return //p'
return (function()
  local awful = require("awful")
  local s = mouse.screen or awful.screen.focused()
  local tags = {}

  for _, t in ipairs(s.tags) do
    if t.selected then
      table.insert(tags, "[" .. t.name .. "]")
    else
      table.insert(tags, t.name)
    end
  end

  return table.concat(tags, " ")
end)()
EOF
