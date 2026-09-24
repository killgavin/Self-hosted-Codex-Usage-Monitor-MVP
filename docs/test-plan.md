# Self-hosted Codex Usage Monitor — Test Plan

- Version: 0.3
- Status: READY
- Sources: `specification.md`, `design.md`

## Rules

分類 UT / IT / E2E / SEC / MAN。狀態只能 PASS / FAIL / BLOCKED / NOT_RUN / NOT_APPLICABLE。PASS 必須有 evidence；Mock PASS 不得宣稱 Real Codex verified。

## MVP Test Cases

T-01 used25→remaining75; T-02 used0→100; T-03 used100→0; T-04 used-1→clamp100; T-05 used101→clamp0; T-06 decimal precision; T-07 unknown limitId preserved; T-08 null name; T-09 secondary null; T-10 null primary according to verified protocol; T-11 unknown field safe.

T-12 resetCredits null; T-13 availableCount2/credits null preserves 2; T-14 empty credits; T-15 credit detail mapping.

T-16 Unix timestamp→UTC ISO; T-17 no fixed Taiwan timezone.

T-18 authenticated account; T-19 unauth account; T-20 null plan no inference.

T-21 cache hit no adapter; T-22 miss adapter once/cache populated; T-23 expired refresh; T-24 no domain mutation.

Codex login gate: login lifecycle endpoints remain available while logged out; status/account/rate-limit APIs reject access until Codex login completes; logout clears the in-memory login state and returns the UI to ChatGPT Login.

T-29 Authorization/Bearer redaction; T-30 access token; T-31 refresh token; T-32 cookie; T-33 account REST no credential; T-34 rate REST no credential; T-35 sanitized errors.

T-36 Codex executable detection; T-37 missing executable controlled; T-38 real app-server start; T-39 real stop/no orphan; T-40 out-of-order correlation; T-41 notification between response; T-42 unknown notification safe; T-43 malformed JSON controlled; T-44 timeout controlled.

T-45 real initialize/initialized→READY; T-46 request before READY controlled.

T-47 real account/read; T-48 unauth real/clean environment; T-49 real device-code login start; T-50 real login completion; T-51 login cancel.

T-52 real rateLimits/read; T-53 multiple limits preserved if available.

T-54 status endpoint schema; T-55 account endpoint; T-56 rate endpoint; T-57 unknown limit preserved.

T-58 dashboard load; T-59 unauth UI no fake quota; T-60 generic cards; T-61 unknown fallback; T-62 UTC→browser local; T-63 mobile 360 no required horizontal scroll.

T-64 docker compose build; T-65 compose up/health; T-66 clean volume unauth; T-67 credential persistence restart; T-68 persistence rebuild.

T-69 Codex missing degraded; T-70 unexpected exit controlled; T-71 upstream unavailable sanitized; T-72 new top-level field safe; T-73 new rate field safe; T-74 unknown enum safe; T-75 stable REST schema; T-76 no raw protocol leakage.

## Reserved

Phase 2 T-77–T-86。Phase 3 T-87–T-98。MVP 均 NOT_APPLICABLE。

## Stage Matrix

Stage0 health smoke/T-54 subset; Stage1 T-37–44; Stage2 T-45–46; Stage3 T-18–20/T-47–48; Stage4 T-49–51/T-59; Stage5 T-01–17/T-52–53/T-72–74; Stage6 T-21–28/T-33–35/T-54–57/T-75–76; Stage7 T-58–62 plus T-63 implementation/static prerequisites; Stage8 T-29–35/T-69–71/T-76; Stage9 Docker implementation/static prerequisites for T-64–68; Stage10 all applicable T-01–76，including mandatory real-browser T-63 and real Docker T-64–68.

By explicit Human decision on 2026-09-20，T-63 real-browser execution is deferred from Stage7 to Stage10 because the current ChatGPT Work workspace cannot provide a browser that can access repository localhost. By explicit Human decision on 2026-09-20，real Docker T-64–68 execution is likewise deferred from Stage9 to Stage10 because the workspace has no usable container builder. These sequencing changes do not mark any deferred test PASS、do not permit mock/static substitution，and do not lower the Final MVP Gate.

## Reporting

Luna 必須回報 TESTS_RUN、actual VALIDATION commands、RESULT。未執行 real test 必須 NOT_RUN，不得用 mock/code inspection/build 取代。

## Regression

Bug fix 先建立 failing regression test，再修正，最後 regression + affected tests PASS。

## CI

Unit + mock integration + security + static；不得要求 CI 保存真實 ChatGPT/OpenAI credential。

## MVP Gate

Applicable automated tests PASS；真實完成 app-server startup、initialize、account/read、rateLimits/read；無已知 credential leakage；文件與實作一致。只有 Final Report `OVERALL: PASS` 才能 MVP COMPLETE。
