# Where Ravens Wait: Eternal Reckoning — Game Identity Lock

## Canonical Identity

```text
Title: Where Ravens Wait: Eternal Reckoning
Abbreviation: WRW:ER
Genre: single-player RPG
Engine: Yggdrasil World Engine
Initial downstream product target: native macOS
Repository role: agnostic engine blueprint and game-system design repository
```

## Architecture Position

```text
ASH Model of the Universe
  -> Yggdrasil World Engine
    -> Where Ravens Wait: Eternal Reckoning
      -> Native macOS Runtime Implementation
```

## Boundary Law

Yggdrasil World Engine remains an agnostic engine blueprint. Where Ravens Wait: Eternal Reckoning is the first single-player RPG built with YWE. The native macOS implementation belongs in a future platform-specific product/runtime repository.

## Allowed in YWE Repository

```text
game identity metadata
WRW:ER design canon
single-player RPG assumptions
macOS-first product target notes
game-layer contracts
vertical-slice design artifacts
platform boundary statements
```

## Not Allowed in YWE Repository

```text
Swift implementation
Metal renderer
SwiftUI view hierarchy
AppKit lifecycle code
GameController input implementation
macOS persistence implementation
platform-specific build tooling
platform-specific rendering assumptions
```

## Product Law

```text
YWE is not a macOS engine.
YWE is an agnostic world-engine blueprint.
WRW:ER is the first game built with YWE.
WRW:ER targets native macOS first.
```
