# UX Design

## Purpose
To plan out details related to the UI and eventual website for the system. This will be edited as I improve/refine ideas. Also documents relevant chatGPT conversations for later review.

## Design Discussions

<details>
<summary>Initial ChatGPT Conversation</summary>

```text
Me:
Would it possibly be a good idea to make a really simple, lightweight MVP UI for a form for making categories and then for page input? 
Just so I could make my life a bit easier as well as I make new pages etc and I need to manually add/edit something like a page or category myself? 
Plus it'll help me iterate on UI stuff a bit in parallel with my underlying framework changes?

ChatGPT:
Yes — but keep it tiny and local-first.

I’d build it as an internal maintainer tool, not “the product UI” yet.

Best MVP:

/tools/ui/
  category builder
  page builder
  relationship seed helper
  YAML preview
  write-to-file button

Core goals:

Make page creation faster.
Reduce YAML syntax mistakes.
Help you discover better schemas.
Let you test UI concepts without slowing the compiler work.

I’d avoid fancy web-app architecture for now. A simple local app is enough:

Streamlit / Flask / FastAPI + basic HTML
or even
Tauri/Electron later if needed

My vote: Streamlit for the first version. It is fast, form-friendly, Python-native, and perfect for internal tools.

The MVP should probably do:

Select category: Character / Faction / Item / Knowledge Source / Custom
↓
Load template schema
↓
Fill fields
↓
Preview generated Markdown/YAML
↓
Validate
↓
Write file

The killer feature: round-trip awareness.

Meaning it should eventually open an existing page, parse the YAML/data block, let you edit fields, then write it back safely.

But don’t start there. Start with “new page generator.”

So yes: good idea. Just keep it as a helper, not a second giant project yet.
```

</details>

<details>
<summary>Pandas Discussion</summary>

```
ChatGPT:
Yep — looking at obsidian_qa_export.py, your current approach is correct.

You’re already doing the “compiler-native” version: parse YAML into typed Python dataclasses like Relationship, AvailabilityEntry, DataProjection, DataReference, FirstAppearanceBeat, BoundedGraphSpec, and CanonicalNote.

Then you render Markdown tables/graphs manually from those objects, like render_first_appearance_beats() building a Markdown table line-by-line.

So pandas would not replace this. Your exporter is doing structured document generation, not dashboard analysis.

Where pandas might help later is after this parsing step, for dashboard-style summaries:

all relationships → dataframe → filter/sort/count/display in Streamlit
all pages → dataframe → missing fields dashboard
all availability rows → dataframe → boundary QA table

So:

Current exporter:
dataclasses + plain Python = good

Future dashboard:
dataclasses → pandas tables → Streamlit = useful

I would not shove pandas into this script yet. It would probably make the compiler noisier, not cleaner.

Me:
hmm ok. but long term would I want to use pandas more to replace how I'm building the actual tables when it eventually is gonna go into like json or SQLite like you said? or again no?

ChatGPT:
Again mostly no.

Long term, I’d keep this separation:

Dataclasses / domain objects
= canonical in-memory model

SQLite / JSON
= durable generated data output

Pandas
= analysis/report/dashboard convenience

For generated JSON or SQLite, you probably want explicit serializers, not pandas:

CanonicalNote -> dict -> JSON
Relationship -> row -> SQLite table
AvailabilityEntry -> row -> SQLite table

Pandas is useful when you want to look across many rows:

count by type
filter relationships
find missing fields
sort timeline entries
dashboard tables
CSV exports
ad hoc analysis

But for your actual compiler/export pipeline, explicit Python objects are better because they preserve meaning.

So the long-term architecture would be:

Markdown/YAML
   ↓
Parser
   ↓
Domain model/dataclasses
   ↓
Serializers:
   - Markdown renderer
   - Mermaid renderer
   - JSON exporter
   - SQLite exporter
   - QA report renderer
   ↓
Optional dashboard:
   - pandas views
   - Streamlit tables

Pandas is a consumer/view layer, not the core model.
```

</details>

## Biggest Takeaways

- Taxonomy in code
- Relationship type filtering
- Source-priority model
- Maintainer vs user contexts
- QA refresh on save
- Dropdowns/checkboxes to reduce schema mistakes

## Pre-Requirements

- Taxonomy allowlist/dictionary in code
- Sort relationships into types for later filtering
- Better conversion of taxonomy to human readable labels for things like relationship nodes etc
- Define user vs maintainer login states for site to determine what of the below will get exposed between the two layers
- Build in priority for source as in novel vs anime/movie etc so we can do things like adaptation deviation based on source priority etc. like LoTM the novel is priority 1 and donghua priority 2. Allows for adaptation deviations to be flagged on donghua not novel as novel is original source of truth that donghua adapted. Same idea would flow into eventual law enforcement/lawyer type of usage of the platform for dna vs video vs audio vs photo vs documented vs first hand witness accounts etc
- Source Priority Examples:
  - Primary source
  - Adaptation
  - Secondary source
  - Witness account
  - Derived analysis
  - Unverified claim

## Desired Features

- Make sure taxonomy is defined in code somewhere rather than in project_rules first
- Have it so UX has generate QA buttons with additional options etc
- Have UX have view/edit forms for categories/pages
- Schema viewer to view YAML/data block for a page etc
- Dynamically build TOC/navigation etc
- Hub pages for categories themselves as well as hub pages for categories with pages within that category. Likely list all of them broken out by sections of first letter (ie. A-E, F-J, etc)
- View simplified knowledgebase filemap w/o gitignored/non-prod folders
- Template editor (goes along with category section above probably)
- Relationship seed helper
- Use dropdowns, radio buttons, checkboxes etc wherever we can to reduce user error
- Flag appropriate fields as required
- Validation before saving
- Save file to write/discard changes buttons
- Turn current_state into real dashboard
- Plan for eventual future login workflow (possibly use SSO with my MS tenant or at least make it possible to use it later if we have to use local for now) to allow for user vs maintainer site
- Have search bar w/ name matchine algorithm of some kind
- Either be able to filter search by categories or have search results return category:page if no filter is set
- Have UX have mermaid viewer/exporter
- Have timeline play button/autoplay for over time playback
- Be able to center the graph on a particular node and build out from there however many layersyou want
- Be able to filter types of nodes that show up and types of relationships etc
- Have QA generator, likely improved version of it, run whenever category/page/YAML data is changed and refresh only associated info on site when detected
- Expose all of the QA specific files only when in maintainer context. Do not show to regular users (requires login state from earlier)

## Long-Term Vision

- Website and standalone desktop app for various OS's
- Support syncing between desktop platform app and website for project maintainers
- Create custom file format for saving/exporting entire project from like web to open in desktop app for more advanced features
- Custom file format should encode in a "projectUsageMode" value that determines what type of project it is to open matching project type (author/worldbuilding, legal, medical etc.)
- Eventual website generator determined by usage mode w/ templates (ie. fandom wiki style site for author/worldbuilding, legal focussed site for legal/compliance/LE, medical focussed site for medical etc)
- Website and desktop app should support themes/layouts depending on project type so buttons/prompts etc are most useful to the people using the platform in that industry
- Desktop app should allow for better integration with other desktop apps. Similar to ChatGPT web vs Codex
- AI chatbot using AI OS concept
  - Website version should know how to reason/use KB and should have checkbox opt-in for pulling external data/info from web both for search seeding as well as answer synthesis. Should explicitly tell web users that source searching is not available due to copyright issues OR figure out a legal way to allow users to upload source files to possibly user-specific saved profile tied to their login
  - Desktop app should allow upgraded features such as source searching via saved local source files that get added to application once and then get re-used going forward. Should have same opt-in for external/pre-trained data as website version
- Be able to link to discord to add discord chatbot to a given server. Chatbot should be powered by same AI system from above

## Planned Phases

### Phase 1: MVP Maintainer UI

- Taxonomy allowlist in code
- Category/page creation form
- YAML/data-block preview
- Relationship seed helper
- Required-field validation
- Save/discard buttons
- Run QA generator after save

### Phase 2: Dashboard/Navigation

- Current State dashboard
- Simplified file map
- Search by page/category
- Generated TOC/navigation
- Schema viewer
- Mermaid viewer/exporter

### Phase 3: Graph/Time Controls

- Center graph on node
- Expand N layers
- Filter node types
- Filter relationship types
- Timeline playback
- Adaptation/source-priority comparisons

### Phase 4: User/Maintainer Split

- Login state
- Maintainer-only QA files
- Reader-safe public views
- SSO-ready auth design