# Tarot Club Preliminary Planning Investigation

## Related Glossary Thread

Planned page: `Glossary_Threads/Factions/faction-tarot-club.md`

## Investigation Question

Which Tarot Club members and associated tarot cards are directly supported by local source evidence?

## Status

Preliminary planning notes. This investigation is source-backed by the local official EPUB image extraction metadata and the reviewed artwork map, not by external wiki or fandom references.

## Evidence Method

- Checked official EPUB image entries with `Tools/edit_image.py --operation list-epub-images`.
- Used the reviewed `Artwork/official-epub-image-map.md` rows as the canonical local record for visible official character-gallery labels.
- Treated official character-gallery labels in the form `Character - Card` as direct source evidence for Tarot Club card identity mapping.
- Preserved identity-state nuance where the same person appears under a later alias or role.

## Source-Backed Tarot Club Identity Map

| Person / identity | Associated tarot card | Source image row(s) | Evidence status | Notes |
| --- | --- | --- | --- | --- |
| Klein Moretti | The Fool | `11`, `99` | confirmed official artwork label | Volume 1 and Volume 8 character-gallery images are recorded as labeled `Klein Moretti - The Fool`. This should be the main convener / founder identity on the future Tarot Club page. |
| Audrey Hall | Justice | `12` | confirmed official artwork label | Volume 1 character-gallery image is recorded as labeled `Audrey Hall - Justice`. |
| Alger Wilson | The Hanged Man | `13` | confirmed official artwork label | Volume 1 character-gallery image is recorded as labeled `Alger Wilson - The Hanged Man`. |
| Derrick Berg | The Sun | `14` | confirmed official artwork label | Volume 1 character-gallery image is recorded as labeled `Derrick Berg - The Sun`. |
| Fors Wall | The Magician | `26` | confirmed official artwork label | Volume 2 character-gallery image is recorded as labeled `Fors Wall - The Magician`. |
| Emlyn White | The Moon | `27` | confirmed official artwork label | Volume 2 character-gallery image is recorded as labeled `Emlyn White - The Moon`. |
| Klein Moretti as Gehrman Sparrow | The World | `39` | confirmed official artwork label for Klein alias / state | Volume 3 character-gallery image is recorded as labeled `Klein Moretti as Gehrman Sparrow - The World`. This is Klein's later identity/card state, not a separate character page target. |
| Cattleya | The Hermit | `40` | confirmed official artwork label | Volume 3 character-gallery image is recorded as labeled `Cattleya - The Hermit`. |
| Leonard Mitchell | The Star | `66` | confirmed official artwork label | Volume 5 character-gallery image is recorded as labeled `Leonard Mitchell - The Star`. |
| Xio Derecha | Judgement | `67` | confirmed official artwork label | Volume 5 character-gallery image is recorded as labeled `Xio Derecha - Judgement`. Preserve the official spelling `Judgement` unless a later house style deliberately normalizes card names. |

## Supporting Artwork Rows

- `110`: Side-stories/end-matter artwork centered on Klein / The Fool with Tarot Club-like figures beneath him. This is useful for future faction-page header or relationship wiring, but it is not the source for individual card assignments.
- `111`: Klein / The Fool portrait holding The Fool tarot card. This reinforces Klein / The Fool identity wiring but does not add a separate club member mapping.

## Future Page Structure Notes

- The future Tarot Club faction page should include a `Tarot Club Seats / Identities` table with reader-boundary-aware rows.
- The table should allow a person to have more than one Tarot Club-facing identity over time, especially Klein as `The Fool` and Klein as `Gehrman Sparrow / The World`.
- Relationship seeds should connect the faction to each character page and should separately capture the associated tarot card.
- Character pages should track Tarot Club card identity as timeline-aware structured data, not only prose.
- `concept-tarot-cards.md` should remain the parent concept for tarot-card symbolism and pathway-card associations; the faction page should only track club membership/card identities.

## Reader-Safety Notes

This investigation uses full-EPUB official gallery evidence and is not reader-safe for early-volume browsing as a whole. The future faction page should expose individual rows only at or after the relevant in-story reveal boundary.
