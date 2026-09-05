# Captioned demo plan

These files are recording plans, not recorded videos. The target is about three minutes at 1440 x 900, with captions only. The current event rules do not give a numeric duration limit, so 180 seconds is a working target that must be checked before the final recording.

Both plans show the same job, actions and hold times. The baseline uses fuller captions. The candidate uses shorter captions so the viewer has more time to watch the action. Planned character rates help identify dense captions; they do not prove readable playback or a better demo.

## Story

The client asks for three guide documents and funds 35 DEMO across 10, 20 and 5 DEMO milestones. The freelancer submits an intentionally incomplete setup note. The client asks for the missing recovery section, which releases no payment. The freelancer then links the actual full setup guide. Acceptance credits 10 DEMO. Both people agree to clarify the remaining scope, inspect its real receipt and withdraw wallet credit. The unpaid 25 DEMO stays in escrow.

The evidence files are real Markdown documents in this repository. The initial note is explicitly incomplete demo work. This is not a customer job, and the recording must not suggest otherwise. It uses the local role switch and freely minted test tokens.

## Before recording

Start the local chain and workspace using the setup guide. Check that no action needs reconciliation. The scene creates a new labelled demo project; it does not reset or delete other agreements. Use a new dedicated recording browser context so the local Client role is selected initially. Pin evidence links to the final published commit when the package is frozen.

The scene selectors come from the current application source. They still need an actual recording run. If a selector, transaction or expectation fails, retain that failed attempt and fix the cause. Do not edit a video to imply the failed action succeeded.

The caption overlay must not cover inputs, confirmations or receipt hashes. After every action, show the actual result long enough to read it. If time is tight, shorten text or cut a separate optional explanation; do not speed up a payment confirmation to hide waiting.

## Recording in Hacky

The controller supplies `scripts/record-demo.mjs`. Use the selected plan with that permitted recording tool and save the attempt under the current job's artifact folder. Its documented interface is:

```text
node scripts/record-demo.mjs SCENE_JSON OUTPUT_DIRECTORY
```

The recorder produces WebM, WebVTT captions and actual timing metadata. Run the controller's `scripts/demo_metrics.py` on that actual metadata, using the final verified event duration and the chosen caption trial target. Do not pass planned times off as a recording.

Watch the entire result. Check exact duration, successful decode, readable captions, real receipt outcomes, secret exclusion and the actual public playback URL. `planned-metrics.json` is only a preflight. No final demo or playback pass is claimed by these files.

## Alternate focus

The same sequence can be narrated through fuller explanations (baseline.json) or shorter action captions (candidate.json). The scene includes precondition metadata, which the recorder does not enforce automatically. Check the live pending-action list, local chain, initial role and public evidence links before each take. Wallet credit can include other agreements, so the captions do not claim that an entire withdrawal came from this one job.

The shorter plan is the first recording candidate because its planned caption rates are lower while the underlying actions and time allowance remain the same. The video must still demonstrate the agreed scope change, the unpaid balance and a real receipt.
