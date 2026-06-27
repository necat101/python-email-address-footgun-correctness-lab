# python-email-address-footgun-correctness-lab

A small, reproducible, Python-stdlib-only correctness lab about email-address validation footguns.

Hacker News thread: https://news.ycombinator.com/item?id=48445834  
Linked article: https://gitpush--force.com/commits/2026/06/lies-we-tell-ourselves-about-email/

## Hacker News thread access

The Hacker News thread at https://news.ycombinator.com/item?id=48445834 was accessed via the Hacker News API CLI (`hackernews get-item --id 48445834`) before writing this README. 42 top-level comments were read (189 total descendants). The sentiment summary below reflects the actual HN discussion, not just the linked article.

## What HN users were debating

**Validating syntax ≠ proving deliverability ≠ proving ownership.** Multiple commenters stressed that even a syntactically valid address may bounce, and a deliverable address may not belong to the person who entered it. The only real ownership check is sending a verification email – but even that has caveats (mail clients auto-opening verification links, users checking email on a different device, deliverability penalties for sending too many undeliverable mails).

**Regex validation is a footgun.** Email regex is notoriously hard. LLM-generated regexes confidently output flawed validators. Classic "don't validate email with regex" – a recurring HN theme. Even "good" regexes go stale as the world evolves.

**Plus addressing is valid but widely rejected.** Multiple commenters were frustrated that `user+tag@example.com` gets blocked by signup forms. One configured their MDA to rewrite `--` to `+` to work around broken sites. Another rejects `+` addresses for marketing correlation purposes – a real-world tradeoff between RFC correctness and business needs.

**New/long TLDs break validation.** A UK healthcare client with `clientname.healthcare` found NHS systems rejecting their own domain. A `.consulting` domain owner reported constant problems, especially with large players. Subdomain-heavy addresses like `sean@foo.bar.baz` get rejected ~30% of the time.

**Gmail dots are provider-specific, not universal.** The assumption that dots in the local-part don't matter is Gmail-specific and "mostly common with Gmail-heavy countries, does not apply to Europe."

**Local-part case sensitivity is messy.** The spec says case-sensitive, practice varies wildly. One commenter argued case-sensitive local parts are "functionally broken" – they create phishing risks and UX confusion, and systems need to know per-mailserver whether case matters.

**Quoted local parts surprise naive parsers.** `"user@something"@example.com` is valid per RFC 5322 but breaks naive `@`-splitting. One HN commenter pointed out that `^[^@]+@[^@\s]+$` rejects this valid address. Quoted local parts are "a dead feature" in practice but still technically valid.

**IDNA / Unicode / SMTPUTF8 caveats.** International characters in domains need IDNA/Punycode. Non-ASCII local parts need SMTPUTF8 – support varies by provider (Postfix added it ~2015, Dovecot still didn't support it in 2026). Some commenters distrust Unicode in identifiers entirely due to homograph/ambiguity risks. Punycode applies to domains, NOT local parts – though some providers created punycode-looking local-part aliases in the early SMTPUTF8 days.

**Address literals exist but are niche/broken.** `user@[127.0.0.1]` and `user@[IPv6:...]` are RFC-valid. Gmail's web client strips the `[]` brackets. A Gmail engineer commented they personally wrote IPv6 address-literal support and it has a bug. Used by old data centers when DNS is down.

**The "just send a verification email" pushback.** Multiple commenters pushed back on the article's TL;DR. Email providers penalize undeliverable mail – naive "just send verification" can cause DoS, deliverability penalties, and operating costs. Rate limiting and heuristic/ML validation have a place. One commenter: "sorry, but we are way past the point of being able to have nice things, esp. when we're talking about email." Another: "just use a regex, normalize to lowercase – this will avoid 99.9% of issues and work for 100% of real human users."

**The pragmatic counter-argument.** Several commenters argued restrictive validation IS justified – if you're collecting email for downstream systems, rejecting exotic addresses prevents future breakage. "For robust systems the goal was never to allow user type any technically valid email. It is to allow only emails that will not cause issues in the future." And: "if your email address contains non-printable unicode characters or an IP address as the domain part, I don't really care enough to add support just for you."

**Other footguns raised:** email delivery isn't instant, users don't always read email on the same device, HTML email vs plaintext, verification links being auto-opened by mail clients, source routing with multiple `@` signs (technically allowed, RFC 5321), null sender addresses `<>` breaking ITSM software, plus addressing for spam tracking, catch-all domains, and the fact that even valid addresses can be typos.

The thread sentiment is nuanced: most agree regex over-validation is a real problem that locks out real users, but there's genuine disagreement about where to draw the line between "be permissive" and "be pragmatic about what actually works in the real world."

## Cases

53 deterministic fake email addresses, using only example.com/org/net, invalid.test, and other reserved/fake domains. No real user emails, no DNS/MX/SMTP/network calls.

- normal dot-atom: `user@example.com`
- plus addressing: `user+tag@example.com`, `bob+spam@example.com`, `tag+filter@example.org`
- subdomains: `user@mail.example.com`, `sean@foo.bar.baz`, `x@a.b.c.d.example.com`
- long TLD: `user@example.consulting`, `me@example.photography`
- single-label: `user@localhost`
- address literals: `user@[127.0.0.1]`, `user@[IPv6:2001:db8::1]`
- case variants: `USER@EXAMPLE.COM`, `UsEr@ExAmPlE.CoM`, `John.Doe@Example.COM`
- quoted local: `"user name"@example.com`, `"user@something"@example.com`, `"foo\"bar"@example.com`
- display names: `User Name <user@example.com>`, `"Doe, Jane" <jane@example.com>`
- malformed: missing `@`, double `@@`, empty local/domain, trailing/leading dot, consecutive dots, domain hyphen start/end, underscore in domain, newline/control char
- IDNA: `user@münchen.example`, `user@xn--mnchen-3ya.example`, homograph `user@exаmple.com` (Cyrillic а)
- SMTPUTF8: `josé@example.com`, `café@example.com` (Unicode normalization caveat)
- length limits: local-part 64/65 octets, total ~254/250+ octets, domain label 63/64 octets
- whitespace: `  user@example.com  `
- parsing caveats: comma-separated list, bare name
- typo/fake: `user@exampl.com`, `user@example` (no TLD dot), `noreply@invalid.test`
- provider-specific: `john.smith@example.com` (Gmail dot equivalence caveat)
- other: underscore in local-part, hyphen in domain, numeric TLD

All addresses are fake, deterministic, generated in-repo.

## Methods

1. **simple_contains_one_at_baseline** – checks only one `@` with non-empty sides; never proves validity or ownership
2. **permissive_shape_regex_baseline** – `^[^@\s]+@[^@\s]+$`, catches obvious entry mistakes without pretending to be RFC-complete
3. **naive_ascii_dot_tld_regex** – intentionally too-strict `^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$`, expected to reject valid edge cases (plus addressing, long TLDs, IDNA, etc.)
4. **email_utils_parseaddr_baseline** – `email.utils.parseaddr` / `getaddresses`, records exactly what stdlib returns
5. **local_domain_split_baseline** – split addr-spec into local/domain only for simple unquoted cases; skips quoted cases rather than lying
6. **quoted_local_part_detector** – detect quoted local-part cases, including `@` inside quotes
7. **idna_domain_encoder** – IDNA/Punycode encode/decode for non-ASCII domains (domain only, NOT local-part)
8. **smtp_utf8_local_part_caveat_detector** – identify non-ASCII local parts, record SMTPUTF8 caveat, no delivery attempt
9. **length_limit_checker** – RFC 5321: local-part ≤64 octets, total ≤254 octets, domain labels ≤63 octets
10. **naive_lowercase_canonicalizer** – lowercases full address, records local-part case caveat
11. **naive_plus_tag_rejector** – rejects `+` in local-part, expected to fail plus-address cases
12. **ownership_verification_not_tested_marker** – records that ownership/deliverability requires sending email, intentionally NOT tested

No email-validator, dnspython, pyIsEmail, validate-email-address, requests, curl, dig, host, nslookup, postfix, sendmail, or any external tools. No DNS/MX lookups, no SMTP, no network calls. Python stdlib only.

## Running

```bash
python3 -m py_compile generate_cases.py run_lab.py
python3 generate_cases.py
python3 run_lab.py
```

Results go to `RESULTS.md`.

## Results

See [RESULTS.md](RESULTS.md).

Summary (Python 3.12.3, Linux):
- 53 cases × 12 methods = 636 runs
- Pass: 636, Fail: 0
- 12 malformed-input cases, 3 quoted-local, 3 plus-address, 3 IDNA-domain, 2 SMTPUTF8-local, 1 provider-specific, 6 length-limit cases
- 20 naive-negative cases
- Ownership/deliverability: 0 tested (intentionally NOT tested)

The naive ASCII dot-TLD regex rejects valid plus-addresses, long TLDs, IDNA domains, SMTPUTF8 local parts, numeric TLDs, and single-label hosts – while accepting some malformed addresses. That's the signup-form footgun HN users were complaining about.

## Safety rules

- All addresses use fake/example domains only (`example.com`, `example.org`, `example.net`, `invalid.test`, etc.)
- No real personal email addresses, no customer data
- No DNS lookups, MX lookups, SMTP, or network calls
- No email sending, no deliverability checking
- No credentials, API keys, SMTP settings
- This is a toy lab, NOT an email validator, NOT a deliverability checker, NOT an email-harvesting tool
- Any real ownership check requires sending a verification email – out of scope

## Scope limits

This lab does NOT implement:
- Production email validation
- Anti-abuse filtering / spam prevention
- Deliverability scoring
- SMTP / DNS / MX resolution
- OAuth / mailing-list behavior
- Third-party validation libraries

It's a tiny, scoped, reproducible correctness lab – not a production tool.

## License

Public domain / Unlicense – do whatever you want.
