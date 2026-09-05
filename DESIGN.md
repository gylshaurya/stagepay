---
name: "Stagepay"
description: "A clear delivery desk for agreements, work evidence and local test-payment receipts."
colors:
  blue: "#245c92"
  blue-hover: "#164773"
  canvas: "#eef3f8"
  sheet: "#ffffff"
  ink: "#17334c"
  muted: "#526578"
  line: "#d8e2eb"
  control-line: "#a9bed0"
  soft: "#e7eff7"
  button-active: "#dce9f5"
  focus: "#4c86ba"
  status-ink: "#355574"
  good: "#206443"
  good-surface: "#e5f2ea"
  review-surface: "#e5effa"
  warn: "#805423"
  warn-surface: "#fbefd9"
  warning-ink: "#704917"
  warning-surface: "#fff5e3"
  danger: "#923e35"
  danger-line: "#d4aaa4"
  error-ink: "#843c32"
  error-surface: "#fbece9"
  evidence-surface: "#f4f7fa"
  receipt-surface: "#f3f6f9"
  proposal-surface: "#eef4fa"
typography:
  headline:
    fontFamily: "Source Sans, 'Trebuchet MS', sans-serif"
    fontSize: "1.65rem"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-.025em"
  title:
    fontFamily: "Source Sans, 'Trebuchet MS', sans-serif"
    fontSize: "1.15rem"
    fontWeight: 700
    lineHeight: 1.3
  body:
    fontFamily: "Source Sans, 'Trebuchet MS', sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Source Sans, 'Trebuchet MS', sans-serif"
    fontSize: ".9rem"
    fontWeight: 600
  status:
    fontFamily: "Source Sans, 'Trebuchet MS', sans-serif"
    fontSize: ".8rem"
    fontWeight: 600
rounded:
  compact: "4px"
  control: "6px"
  sheet: "8px"
  circle: "50%"
spacing:
  tight: "6px"
  small: "10px"
  field-gap: "14px"
  action: "16px"
  compact-section: "18px"
  section: "20px"
  column: "22px"
  sheet-inset: "24px"
components:
  button-primary:
    backgroundColor: "{colors.blue}"
    textColor: "{colors.sheet}"
    rounded: "{rounded.control}"
    padding: "9px 16px"
  button-primary-hover:
    backgroundColor: "{colors.blue-hover}"
  button-secondary:
    backgroundColor: "{colors.sheet}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "9px 16px"
  button-danger:
    backgroundColor: "{colors.sheet}"
    textColor: "{colors.danger}"
    rounded: "{rounded.control}"
    padding: "9px 16px"
  input:
    backgroundColor: "{colors.sheet}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "10px 12px"
  status:
    backgroundColor: "{colors.soft}"
    textColor: "{colors.status-ink}"
    rounded: "{rounded.compact}"
    padding: "4px 9px"
    typography: "{typography.status}"
  status-accepted:
    backgroundColor: "{colors.good-surface}"
    textColor: "{colors.good}"
  sheet:
    backgroundColor: "{colors.sheet}"
    rounded: "{rounded.sheet}"
---

# Design System: Stagepay

## Overview

**Creative North Star: "The Delivery Desk"**

Stagepay uses the clarity of a parcel tracking desk for collaborative project work. A pale blue canvas, navy identity band and white work sheets establish a calm, practical setting. Restrained blue actions and humanist typography make decisions easy to locate.

The visual system is flat, moderately dense and explicit about state. Numbered work rows, attached evidence and expandable receipts create continuity between an agreement and its outcome. Plain language and visible local-demo context keep the interface honest.

**Key Characteristics:**

- Pale blue surroundings and white work sheets with quiet borders.
- Humanist type, compact labels and readable scope text.
- Numbered delivery rows with written status and a small status dot.
- Native disclosures keep evidence and secondary actions close to their context.

This scan records `web/index.html`, `web/style.css` and `web/app.js` after the finish review. The source and its final CSS overrides take precedence over earlier direction notes. Route-specific strategy is recorded in the surface brief.

## Colors

Cool blue neutrals frame the work, while restrained semantic tints explain state. Frontmatter values are normative; the names below describe their use.

### Primary

- **Delivery Blue** (`blue`): primary actions, evidence links and submitted-state text. **Deep Delivery Blue** (`blue-hover`) strengthens primary button hover.
- **Focus Blue** (`focus`): the visible keyboard outline on controls, links and disclosure summaries.

### Secondary

- **Accepted Green** (`good`, `good-surface`): accepted or closed states and accepted milestone numbering.
- **Agreement Amber** (`warn`, `warn-surface`): awaiting agreement and disputed status. The separate warning surface and ink carry explanatory notices.
- **Dispute Red** (`danger`, `danger-line`): the outlined dispute action. Error ink and surface distinguish failed action notices.

### Neutral

- **Pale Blue Canvas** (`canvas`): the page surrounding the work sheets.
- **White Sheet** (`sheet`): toolbar, project sheets and form controls.
- **Navy Ink** (`ink`): header fill and primary text. **Slate Copy** (`muted`): supporting labels, descriptions and timestamps.
- **Sheet Divider** (`line`) separates containers and rows; **Control Stroke** (`control-line`) gives form controls a firmer edge.
- **Soft Blue** (`soft`) and **Pressed Blue** (`button-active`) supply secondary control feedback. Evidence, proposal and receipt surfaces provide quiet local grouping.

**The Written State Rule.** Color accompanies readable state text; a dot alone does not explain project or milestone status.

## Typography

**Display and Body Font:** self-hosted Source Sans 3, registered in CSS under the family alias `Source Sans`, followed by Trebuchet MS and sans-serif. The three bundled faces supply normal styles at weights 400, 600 and 700. Font synthesis is disabled and faces use swap loading. There is no separate display face; browser monospace is used for hashes.

The humanist sans supports scope reading and dense labels without making the workspace feel technical. Paragraphs have a maximum measure of 72ch. Amounts in milestone rows use tabular numerals.

### Hierarchy

- **Headline:** the selected project name uses the frontmatter headline role. On mobile it reduces to 1.4rem. The empty-state headline is 2rem on desktop and 1.65rem on mobile.
- **Title:** section headings use the title role; subheadings use 1rem bold.
- **Body:** normal text uses the body role. The 1.5 line height is applied to paragraphs; other elements retain their native or component line height.
- **Label:** visible form labels use the label role. Status labels use the smaller status role. Supporting help text is usually .88rem.
- **Identity:** the brand is bold at 1.5rem with tight tracking, reducing to 1.35rem on mobile.

## Layout

A centered main region has a maximum width of 1228px including 24px side padding. The header aligns to the corresponding 1180px content width. A shallow project toolbar precedes the selected project heading. Broad work sheets and narrower supporting sheets share the same border and inset vocabulary. Typical sheet content uses a 24px inset, reducing to 18px on mobile.

The implemented project view places milestones and agreement in a grid of `minmax(0,1.8fr) minmax(300px,1fr)` with a 22px gap. Receipt history follows across the available width. This composition belongs to the milestone desk surface; it is not a requirement for every future screen.

- **Above 900px:** the toolbar uses a wrapping flex layout. The two selector labels can grow; project selection starts with a 200px minimum, role with a 160px minimum.
- **761px through 900px:** selector fields take a complete first row and the connection/create group spans a second row.
- **760px and below:** page insets become 14px, the header stacks, and the toolbar uses 12px padding. Project and Demo role remain side by side in a `1.5fr / 1fr` grid. Connection status and New project occupy their own row. Agreement precedes milestones in the single-column layout. A visible View milestones anchor leads past agreement detail. Secondary agreement tools are nested under Agreement options. Milestone summaries wrap status below the name/amount line, and action buttons share available width.

The milestone anchor has a 16px scroll margin. Scope, evidence links and transaction hashes wrap rather than widening their containers.

## Elevation & Depth

The system has no box shadows. White sheets, fine blue-gray borders and soft inset fills create grouping. Header contrast establishes identity; expanded disclosures expose content in the document flow. Nothing depends on hover lift or floating layers.

**The Flat Sheet Rule.** Separate information with borders, whitespace and tonal fills before adding any elevation.

Motion is limited to background feedback and disclosure direction: buttons and chevrons transition for .18s with ease-out, and action notices receive a .25s ease-out background highlight. Reduced-motion preference disables animations and transitions.

## Shapes

Sheets and the toolbar use the sheet radius; controls, notices and evidence blocks use the control radius. Status badges and receipt code blocks use the compact radius. Numbered milestone markers and status dots are circular. Sheet overflow is clipped to its edge. One-pixel strokes define containers and inputs without heavy frames.

## Components

### Buttons

Confident, compact controls with visible text. Buttons have a minimum height of 44px, semibold labels and the control radius. Primary buttons use Delivery Blue with white text and Deep Delivery Blue on hover. Secondary controls use white with navy text and a firmer control stroke, soft hover fill and pressed fill. The danger variant changes text and stroke while retaining the secondary form. Disabled buttons use .48 opacity and a not-allowed cursor. Smaller export controls preserve the minimum height.

Keyboard focus uses a 3px Focus Blue outline, with a 4px outline offset on buttons, links and form controls. The source does not assign that offset to summary elements. Primary buttons have a hover color but no distinct primary-specific pressed color; document this cascade without inventing a new state.

### Inputs / Fields

Visible semibold labels sit above native inputs and selects. White fields use a one-pixel control stroke, control radius, 10px by 12px padding and a minimum height of 44px. Textareas are at least 90px high and resize vertically. Form validation uses native required, type and pattern constraints. There is no separate custom field-error treatment; action errors appear in the live notice.

### Status Badges

Compact filled rectangles combine a six-pixel dot with an explicit written state. Default states use soft blue, submitted work uses the review tint, accepted and closed use green, and disputed or awaiting agreement use amber. They are informational, with no hover or selection behavior.

### Sheets and Evidence

Bordered white sheets use a shared rounded silhouette. Section headings and supporting descriptions stay in a clear top inset. Evidence appears in a subdued inner block with a note, work link and wrapping hash. Proposals receive a pale blue inset, while warnings and success/error notices use semantic fills.

### Navigation and Disclosures

The workspace has a skip link, project selector and Demo role selector rather than a sidebar. The mobile View milestones link is the explicit shortcut to work. Native details and summary elements reveal milestones, agreement options and receipts. A small inline chevron rotates when open. Summary controls retain a visible focus outline; the source does not define a hover fill for them.

### Delivery Rows and Receipts

Milestone rows connect a circular sequence marker, work name, DEMO amount and status. The next relevant row opens according to the selected demo role and project state; accepted rows remain initially collapsed. Delivery evidence and decisions stay inside that row. Receipt history presents recent entries first, each with a timestamp and confirmed status; expanding reveals the transaction hash, agreement fingerprint and local chain/block context. Export record creates the current project's JSON record.

While an action is pending, the app marks itself busy and shows a live receipt-wait notice. Confirmed actions refresh the workspace and display saved feedback. This is a local Anvil demo with real local transaction receipts and test tokens; these components do not establish production authentication or public deployment.

## Do's and Don'ts

### Do:

- Do use blue for primary actions and links, with navy for identity and readable text.
- Do pair status color with a written state and retain visible keyboard focus.
- Do keep long evidence URLs and hashes wrapping within their containers.
- Do retain the compact two-column project and role controls on mobile, with connection and create controls on a separate row.
- Do keep local-demo and test-token labels visible and put transaction details beside their receipts.

### Don't:

- Don't add gradients, glow, decorative metric tiles or a speculative crypto dashboard.
- Don't replace the humanist sans with display typography or invent an extra type family.
- Don't hide the route to milestones behind agreement-management disclosures on mobile.
- Don't label the demo role switch as authentication or local receipts as public testnet proof.
