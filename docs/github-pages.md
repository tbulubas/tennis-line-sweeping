# Publishing the Game on GitHub Pages

The game [web/sweeping-game.html](../web/sweeping-game.html) is a single,
self-contained HTML file: it needs no build step, no Python and no solver.
GitHub Pages serves it straight from the repository at

**https://tbulubas.github.io/tennis-line-sweeping/web/sweeping-game.html**

This is the address the game exception in [LICENSE](../LICENSE) refers to.

## Prerequisites

- The repository `tbulubas/tennis-line-sweeping` exists on GitHub and the
  branch `main` is pushed.
- The repository is **public**. On a free GitHub plan, Pages works for public
  repositories only.

## Turn Pages on (once)

1. Open the repository on GitHub, then *Settings → Pages* (in the left
   column under *Code and automation*).
2. Under *Build and deployment*, set *Source* to **Deploy from a branch**.
3. Under *Branch*, choose **main** and the folder **/ (root)**, then *Save*.
4. Wait a minute or two. The tab *Actions* shows a run named *pages build and
   deployment*; when it is green, *Settings → Pages* shows
   "Your site is live at https://tbulubas.github.io/tennis-line-sweeping/".
5. Open the game address above and play one round, also on a phone.

## Show the link on the repository page

On the repository's main page, click the gear next to *About* and paste the
game address into *Website*. It then appears at the top of the repository,
next to the description.

## What GitHub Pages serves

- Every file of the branch under the same path:
  `web/sweeping-game.html` becomes `…/tennis-line-sweeping/web/sweeping-game.html`.
- The site's start page `https://tbulubas.github.io/tennis-line-sweeping/` is
  the README, which Pages renders with Jekyll; its *Play online* link leads to
  the game.
- The game loads only its fonts from Google Fonts; everything else is inside
  the HTML file.
- The shared board of best times only works where the page runs as a
  claude.ai artifact. On GitHub Pages it is hidden; the rest of the game is
  the same.

## Updates

Every push to `main` publishes the site again within a few minutes. The
browser may keep the old page for a short while; reload it to see the new
version.

## When the name changes

The address contains the repository name. If the repository is renamed, or
the game file moves, update the address in all three places:

- [LICENSE](../LICENSE), exception 2,
- [README.md](../README.md), *Play online* and *License*,
- the footer of [web/sweeping-game.html](../web/sweeping-game.html).

## Turn Pages off

*Settings → Pages → Unpublish site* (or set *Source* to *None*). The game
address then stops working; the repository itself is unchanged.

---

© 2026 Taras Bulubas. All rights reserved. See [LICENSE](../LICENSE).
