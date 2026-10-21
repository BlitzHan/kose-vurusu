# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Static HTML/CSS/JS, no build step, published on GitHub Pages. One data file (`data/tahminler.json`) produced locally by the analysis tooling.

## Users

Yıldırım and a small group of friends who look at upcoming football matches together before kick-off, mostly on their phones. They want a quick read of who is in form and what the numbers suggest, then the option to dig into recent matches and player form to make up their own minds.

## Product Purpose

For each match the user asks about, show data-driven probable outcomes (match result, both teams to score, total goals over/under, most likely scores) derived from both teams' recent statistics and players' recent form. Success: a friend opens a match on the phone, sees within seconds which outcomes the data strongly supports, and can verify them against the last matches without leaving the page.

## Positioning

Not a betting tip sheet. It presents what the teams' and players' recent numbers imply, says plainly when the data gives no strong signal, and keeps the underlying recent-match data one tap away so the reader can judge for themselves.

## Operating Context

Matches are added on request by the owner (analysis via a local Claude skill), usually on match day. Viewers revisit the page before and after matches; results are recorded afterwards and a running record (how often picks were right) is shown.

## Capabilities and Constraints

- Per match: expected goals, 1/X/2, double chance, BTTS, 1.5/2.5/3.5 over-under probabilities, score matrix, market comparison when odds exist.
- Only high-confidence picks are presented as picks; low-confidence outcomes are shown as plain probabilities, not recommendations.
- Recent-match table per team (last 10 official matches: result, xG, shots on target, big chances, box touches, possession, XI rating) and player form (recent ratings, goals, assists, absences).
- Text is short: a headline and a few sentences, never long columns.
- Data source names must never appear on the site, in the repo, or in commit messages.
- Turkish UI.

## Brand Commitments

Name: Köşe Vuruşu. Voice: short, plain, direct Turkish. The previous newspaper look was rejected by the owner.

## Evidence on Hand

Real data for two matches (2026-10-21: Lille – Galatasaray, Real Madrid – RB Leipzig). No results recorded yet; no testimonials or usage claims.

## Product Principles

1. Lead with what the data strongly supports; say "no strong signal" when that is the truth.
2. Every pick shows its evidence (model probability, recent hit rate, market) in one line.
3. The raw recent numbers are always one tap away.
4. Short beats complete: fewer words, more numbers.
5. Not betting advice; never frame picks as a sure thing.
