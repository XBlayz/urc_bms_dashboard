---
lang: en
---

# TODO lists
## Fixes
- [?] Plot delta over time
  - _Better explanation needed_
- [?] Cursor should always follow mouse (even when auto-scrolling)
- [?] Max of two fixed time cursors should be possible (with measurements between them)

- [-] Enum plot downsampling
  - _Unable to reproduce_
- [-] Fix SoP unit
  - _In mock is correct_ (Unit are all `Amps`)

- [ ] Fix autoscroll in table view
- [ ] Cursor measurements data view
- [ ] Better aesthetic scrollbar
- [ ] Override procedure help
  - [ ] AIR- blinking brighter when pre-charging is finished
  - [ ] Pre-charge blinking orange when AIR- is closed and pre-charge is still closed
  - [ ] Wait for manual control buttons state update (grayed out)
- [ ] Charging screen target graphs
  - [ ] Change colors to white
  - [ ] Fix continues updating for each telemetry update

## Features
- [ ] "Charging" screen
  - [ ] Pack balancing matrix view
  - [ ] Manual balancing
- [ ] "Logs" screen
  - [ ] Fault widgets
- [ ] "Sidebar"
  - [ ] Fault counter (or code) definition
  - [ ] Serial connection status and stats
- [ ] Try reconnection action for serial interface
- [ ] "Settings" screen
- [ ] App icon and URC logo

## Testing
- [ ] Add testing related to protobuf messages and serial decoding and encoding (virtual COM)

# Questions
- SDC is the circuit state or the signal related to the BMS part?
  - Verify for correct behavior of SDC button in advance mock
- Verify FSM correct behavior in advance mock
