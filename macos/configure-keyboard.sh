#!/bin/bash
mkdir -p ~/Library/Scripts

cat <<EOF > ~/Library/Scripts/remap_keys.sh
#!/bin/bash

/usr/bin/hidutil property --set '{
  "UserKeyMapping":[
    {
      "HIDKeyboardModifierMappingSrc": 0x7000000E7,
      "HIDKeyboardModifierMappingDst": 0x7000000E6
    }
  ]
}'
EOF

chmod +x ~/Library/Scripts/remap_keys.sh

cat <<EOF >  ~/Library/LaunchAgents/com.user.remapkeys.plist
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.user.remapkeys</string>
  <key>ProgramArguments</key>
  <array>
    <string>/Users/$USER/Library/Scripts/remap_keys.sh</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
</dict>
</plist>
EOF

cat <<EOF > ~/Library/KeyBindings/DefaultKeyBinding.dict
{
    // Home / End keys
    "\\UF729"     = moveToBeginningOfLine:;                       // Home
    "\\UF72B"     = moveToEndOfLine:;                             // End
    "\\$\\UF729"    = moveToBeginningOfLineAndModifySelection:;     // Shift + Home
    "\\$\\UF72B"    = moveToEndOfLineAndModifySelection:;           // Shift + End

    // Ctrl + Home / End (move to beginning/end of document)
    "^\\UF729"    = moveToBeginningOfDocument:;                   // Control + Home
    "^\\UF72B"    = moveToEndOfDocument:;                         // Control + End
    "^\\$\\UF729"   = moveToBeginningOfDocumentAndModifySelection:; // Control + Shift + Home
    "^\\$\\UF72B"   = moveToEndOfDocumentAndModifySelection:;       // Control + Shift + End

    // Caps Lock (remapped to Control) + Left/Right = Home/End
    "^<Left>"    = moveToBeginningOfLine:;                       // Caps + Left
    "^<Right>"   = moveToEndOfLine:;                             // Caps + Right
    "^$<Left>"   = moveToBeginningOfLineAndModifySelection:;     // Caps + Shift + Left
    "^$<Right>"  = moveToEndOfLineAndModifySelection:;           // Caps + Shift + Right

    // Optional: Control + Return inserts newline ignoring field editor
    "^\\r"        = insertNewlineIgnoringFieldEditor:;            // Control + Return
}
EOF

echo "Done.Run launchctl load ~/Library/LaunchAgents/com.user.remapkeys.plist to activate"