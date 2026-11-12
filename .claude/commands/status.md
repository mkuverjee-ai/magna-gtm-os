Where every campaign stands, problems first.

Scope: **$ARGUMENTS** (empty = everything; a play name = that play only)

## Steps

1. **Pull every campaign, live:**
   ```
   python3 gtm.py campaigns --json
   ```
   Both Instantly and Lemlist, read-only. If one platform errors, say which and carry on with the other.

2. **For anything active or recently finished**, pull sends, replies, positive replies and bounces
   with `skills/instantly` (analytics overview per campaign) and `skills/lemlist-reporting`.

3. **Match campaigns to plays.** Each `plays/<slug>/PLAY.md` names its campaigns. A live campaign
   that no play claims is worth flagging: nobody owns its learnings.

4. **Report, in this order:**
   - **Needs attention now:** bounce protect, accounts unhealthy, suspended, bounce rate over 3%,
     a campaign that ended with leads still unsent, a positive reply nobody has answered
   - **Live:** sent, reply rate, positive replies, against the benchmarks below
   - **Paused / draft:** and why, if PLAY.md says
   - **Completed:** final numbers, and whether the learning was logged (`gtm.py intel`)
   - **Next:** the one or two things you would do

## Rules

- Reply rate is the signal. Open rate is unreliable when open tracking is off.
- Benchmarks from a few hundred B2B campaigns: median reply 0.64%, top decile 2.75%, about a quarter
  of replies positive. Event-sourced audiences run far higher; judge them separately.
- Under ~200 sends, say the sample is too small rather than quoting a rate as if it were stable.
- Be concrete: "Campaign X is in bounce protect, 4.1% bounce on 560 sent" beats "some issues".
