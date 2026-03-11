# PS_Calc — Compact Modes Implementation Guide

_How to implement `slim_content` and `header_summary` for any Section subclass._

---

## Architecture Overview

`Section` supports two independent compact-mode flags, set via `compact_modes: list[str]` in `layout_config.json`:

| Flag | Effect |
|---|---|
| `"slim_content"` | Show a compact widget when the panel is slim; toggle between collapsed and compact (full content never shown in slim mode) |
| `"header_summary"` | Always-visible summary label in the header; section auto-collapses when slim (no separate compact widget) |
| `"hidden"` | Section hidden entirely when slim |
| `[]` | No change when slim |

Any combination is valid. `["slim_content", "header_summary"]` gives both: compact widget in slim mode + always-visible header text.

The **base class** (`Section`) owns all frame visibility, `_is_collapsed`, and arrow state.
Subclass hooks **only** build/update/show-hide their own widget.

---

## State Machine

### slim_content

```
Panel NOT slim:                    Panel slim:
  collapsed ←→ full content shown    collapsed ←→ slim widget shown
  (header click toggles)             (header click toggles)

Transitions (set_slim_mode):
  not_slim → slim, was_expanded  : hide full content, call _enter_slim()
  slim → not_slim, was_expanded  : call _exit_slim(), show full content
  slim ↔ not_slim, was_collapsed : no content change (only content shown on expand)
```

### header_summary

```
Summary label is ALWAYS visible in the header, regardless of slim state or collapsed state.

Panel NOT slim: toggle between collapsed / full content normally.
Panel → slim:   if was expanded, auto-collapse to header only (summary text still visible).
Panel → not slim: restore pre-slim collapse state.
```

---

## Implementing `slim_content`

### 1. Set the flag in `layout_config.json`

```json
{
  "key": "my_section",
  "compact_modes": ["slim_content"]
}
```

### 2. Add compact widget storage in `__init__`

```python
self._compact_widget: QWidget | None = None
```

### 3. Add a lazy builder

```python
def _build_compact_widget(self) -> None:
    w = QWidget()
    # ... build your compact layout inside w ...
    w.setVisible(False)           # must start hidden
    self._compact_widget = w
    self.layout().addWidget(w)    # add to section root layout (outside _content_frame)
```

### 4. Override `_enter_slim` and `_exit_slim`

```python
def _enter_slim(self) -> None:
    if self._compact_widget is None:
        self._build_compact_widget()
    # update compact widget with current values
    self._compact_widget.setVisible(True)

def _exit_slim(self) -> None:
    if self._compact_widget is not None:
        self._compact_widget.setVisible(False)
```

**Do NOT** touch `_content_frame`, `_is_collapsed`, or `_arrow` inside these hooks —
the base class owns those.

### 5. Keep compact widget in sync when data changes

When the section's data is updated (e.g. in `refresh()` or `load_build()`), also update the
compact widget if it exists:

```python
def refresh(self, data) -> None:
    # update full content labels ...
    if self._compact_widget is not None:
        self._compact_lbl.setText(self._build_compact_text())
```

---

## Implementing `header_summary`

### 1. Set the flag in `layout_config.json`

```json
{
  "key": "my_section",
  "compact_modes": ["header_summary"]
}
```

This causes `Section.__init__` to add a `_header_summary_lbl: QLabel` to the header row.

### 2. Call `set_header_summary` whenever data changes

```python
# In __init__, after setting up initial values:
self.set_header_summary(self._build_summary())

# In any change handler:
def _on_changed(self) -> None:
    self.some_signal.emit()
    self.set_header_summary(self._build_summary())

# In load_build:
def load_build(self, build) -> None:
    # ... restore values ...
    self.set_header_summary(self._build_summary())
```

### 3. Write `_build_summary() -> str`

Return a short one-line string describing the current section state.
This appears in the header at all times.

```python
def _build_summary(self) -> str:
    active = [name for name, val in self._things.items() if val]
    return "  ·  ".join(active) if active else "None active"
```

**No** `_enter_slim` / `_exit_slim` needed — the base class handles auto-collapse.

---

## Combining Both Flags

```json
{ "compact_modes": ["slim_content", "header_summary"] }
```

- Header summary label is always present.
- In slim mode: toggle between collapsed and slim widget (header text always readable).
- Implement both the `_enter_slim`/`_exit_slim` hooks and `set_header_summary` calls.

---

## Styling

Header summary label object name: `"section_header_summary"`.
Add a rule in `dark.qss` to style it:

```css
QLabel#section_header_summary {
    color: #888;
    font-size: 10px;
    padding-left: 8px;
}
```

---

## Existing Implementations (reference)

| Section | compact_modes | Slim widget | Notes |
|---|---|---|---|
| `stats_section` | `["slim_content"]` | 2×3 grid of stat totals | `_compact_labels` dict synced in `update_from_bonuses` |
| `derived_section` | `["slim_content"]` | 5-row BATK/DEF/FLEE/HIT/CRI grid | synced in `refresh()` |
| `equipment_section` | `["slim_content"]` | Weapon name + "N/11 slots" | `_update_compact_labels()` called from multiple sites |
| `passive_section` | `["header_summary"]` | — | `_build_summary()` → mastery levels + flags |
| `buffs_section` | `["header_summary"]` | — | `_build_summary()` → active self-buff names |
| `player_debuffs_section` | `["slim_content"]` | Stub text label | Pending Session R |
| `target_section` | `["slim_content"]` | One-line mob summary | `_update_compact_label()` |

---

## Base Class Fallback

If a section has `"slim_content"` in its modes but does NOT override `_enter_slim`,
the base class fallback shows the full content frame — graceful degradation for stubs.
The section works normally in slim mode (just not compacted).

Override `_enter_slim` only when you have a real compact widget to show.
