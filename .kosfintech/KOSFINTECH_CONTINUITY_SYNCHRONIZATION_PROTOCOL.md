# KOSFINTECH CONTINUITY SYNCHRONIZATION PROTOCOL

## 1. Purpose

This protocol establishes the controlled synchronization relationship between the live KOSFintech Git repository and the KOSFintech Continuity Corpus maintained in Library.

## 2. Source-of-Truth Boundary

Git is the authoritative source for the exact live repository state, including committed code, repository history, branch state, tracked files, untracked files, working-tree state, and recovery artifacts.

The Library Continuity Corpus is the authoritative continuity store for preserved project knowledge, architectural decisions, constitutional and governance boundaries, domain semantics, developmental frontiers, validation evidence, historical continuity, AI handoff information, and documented repository checkpoints.

The Library does not replace Git and shall not be treated as the live repository.

## 3. Synchronization Principle

A Git commit does not automatically synchronize the Library.

Meaningful repository changes SHALL trigger deliberate continuity synchronization when they materially affect:

- architecture;
- domain semantics;
- constitutional or governance boundaries;
- DSL development or readiness evidence;
- SMOS, CMOS, CDA, or another MOS frontier;
- implementation correspondence;
- validation evidence;
- engineering decisions;
- unresolved questions;
- continuity or handoff state;
- repository recovery or checkpoint state.

Minor implementation changes that do not materially alter continuity knowledge MAY remain Git-only until a meaningful checkpoint.

## 4. Synchronization Sequence

The controlled sequence is:

1. Implement.
2. Validate.
3. Commit or establish a repository checkpoint where appropriate.
4. Capture branch, HEAD, working-tree status, and relevant repository evidence.
5. Identify continuity-relevant changes.
6. Synchronize the relevant knowledge/artifacts into Library.
7. Record the synchronized Git HEAD and synchronization timestamp.
8. Verify the Library synchronization.
9. Continue development.

## 5. Repository State Classification

Repository artifacts SHALL be distinguished before preservation or cleanup.

### 5.1 Tracked

Files already tracked by Git.

### 5.2 Untracked Developmental

New artifacts that represent current developmental knowledge and may require Library synchronization.

### 5.3 Recovery

Backup, pre-change, corrupted-recovery, baseline, or restoration artifacts.

Recovery artifacts SHALL NOT automatically be interpreted as current implementation.

### 5.4 Temporary

Working files, temporary semantic/question files, experimental directories, generated intermediate material, or other transient artifacts.

Temporary artifacts SHALL NOT be deleted solely because they are classified as temporary. Their disposition SHALL be determined deliberately.

## 6. Required Repository Checkpoint Evidence

A continuity synchronization record SHOULD capture, at minimum:

- UTC timestamp;
- active branch;
- Git HEAD;
- working-tree status;
- relevant changed or untracked artifacts;
- validation/test evidence relevant to the frontier;
- continuity artifacts synchronized;
- unresolved items;
- recovery references where relevant.

## 7. Library Synchronization Boundary

Only continuity-relevant knowledge and verified project artifacts SHALL be synchronized into the Continuity Corpus.

The Corpus SHALL preserve the distinction between:

- current;
- developmental;
- historical;
- superseded;
- unresolved;
- not implementation ready;
- implementation not authorized.

A Library artifact SHALL NOT be treated as current merely because it exists in Library.

## 8. Staleness Rule

Every repository-derived Library snapshot SHALL be associated with the Git state from which it was captured.

If the live repository has advanced beyond that recorded state, the Library artifact SHALL be treated as a continuity snapshot rather than a claim of current repository state until re-synchronized.

## 9. Non-Substitution Rule

Library continuity evidence SHALL NOT be used as proof of live repository behavior when the relevant repository state has not been verified.

Likewise, successful implementation, tests, Git commits, or Library preservation SHALL NOT independently create constitutional, governance, institutional, ecclesiastical, legal, or external authority.

## 10. No Automatic Promotion

Synchronization SHALL NOT promote:

- developmental semantics into production semantics;
- unresolved questions into resolved decisions;
- recovery artifacts into current implementation;
- structural similarity into domain identity;
- implementation evidence into authority;
- Library preservation into production authorization.

## 11. Current Baseline

Initial verified synchronization baseline:

- UTC timestamp: 2026-09-23T16:40:11Z
- Branch: main
- HEAD: e9f183bcbf44da1b4b8ff2e3c95bfc9b8a5dfccc
- git diff --check: clean

At this baseline, the working tree contains untracked developmental, recovery, and temporary artifacts. These SHALL remain separately classified until deliberately resolved.

## 12. Governing Rule

Git records what the repository is.

Library records what KOSFintech knows, has decided, has established, has preserved, and needs for continuity.

Meaningful repository checkpoints synchronize the two deliberately; they are not assumed to synchronize automatically.

## 13. Status

PROTOCOL STATUS: ESTABLISHED — DEVELOPMENTAL

PRODUCTION APPLICATION DEPENDENCY: NONE

AUTHORITY EFFECT: NONE
