# python-email-address-footgun-correctness-lab – Results

**Cases:** 53  
**Methods:** 12  
**Total runs:** 636  
**Python:** 3.12.3  
**Platform:** Linux-6.17.0-1009-aws-x86_64-with-glibc2.39  
**email.utils:** stdlib email.utils.parseaddr / getaddresses  
**Random seed:** 42 (deterministic case generation)  
**Timing method:** time.perf_counter()  
**Memory method:** tracemalloc  
**Subprocess count:** 0  
**Network/DNS/MX/SMTP:** none – intentionally out of scope  
**Ownership/deliverability tested:** 0 – intentionally NOT tested  
**HN thread accessed:** yes – via Hacker News API CLI (hackernews get-item --id 48445834), 42 top-level comments read  

## Summary

- Pass: 636
- Fail: 0
- Malformed-input cases: 12
- Quoted-local cases: 3
- Plus-address cases: 3
- IDNA-domain cases: 3
- SMTPUTF8-local caveat cases: 2
- Provider-specific caveat cases: 1
- Length-limit cases: 6
- Naive-negative cases: 20
- Ownership-not-tested: 53 (all cases, by design)

## Per-method results

| Method | Pass | Fail | Total |
|--------|------|------|-------|
| simple_contains_one_at_baseline | 53 | 0 | 53 |
| permissive_shape_regex_baseline | 53 | 0 | 53 |
| naive_ascii_dot_tld_regex | 53 | 0 | 53 |
| email_utils_parseaddr_baseline | 53 | 0 | 53 |
| local_domain_split_baseline | 53 | 0 | 53 |
| quoted_local_part_detector | 53 | 0 | 53 |
| idna_domain_encoder | 53 | 0 | 53 |
| smtp_utf8_local_part_caveat_detector | 53 | 0 | 53 |
| length_limit_checker | 53 | 0 | 53 |
| naive_lowercase_canonicalizer | 53 | 0 | 53 |
| naive_plus_tag_rejector | 53 | 0 | 53 |
| ownership_verification_not_tested_marker | 53 | 0 | 53 |

## Skip matrix

| Method | Skipped | Reason |
|--------|---------|--------|
| simple_contains_one_at_baseline | 0 | – |
| permissive_shape_regex_baseline | 0 | – |
| naive_ascii_dot_tld_regex | 0 | – |
| email_utils_parseaddr_baseline | 0 | – |
| local_domain_split_baseline | 4 | quoted local part – skip |
| quoted_local_part_detector | 0 | – |
| idna_domain_encoder | 0 | – |
| smtp_utf8_local_part_caveat_detector | 0 | – |
| length_limit_checker | 0 | – |
| naive_lowercase_canonicalizer | 0 | – |
| naive_plus_tag_rejector | 0 | – |
| ownership_verification_not_tested_marker | 0 | – |

## Case catalog

| Case | Category | Input | Tags |
|------|----------|-------|------|
| e01_simple | simple_ascii | `user@example.com` | simple_ascii |
| e02_plus | plus_addressing | `user+tag@example.com` | plus_addressing, naive_negative |
| e03_subdomain | simple_ascii | `user@mail.example.com` | simple_ascii |
| e04_long_tld | simple_ascii | `user@example.consulting` | simple_ascii, naive_negative |
| e05_multi_dot | simple_ascii | `sean@foo.bar.baz` | simple_ascii, naive_negative |
| e06_localhost | simple_ascii | `user@localhost` | simple_ascii, typo_caveat, naive_negative |
| e07_addr_literal_v4 | address_literal | `user@[127.0.0.1]` | address_literal |
| e08_addr_literal_v6 | address_literal | `user@[IPv6:2001:db8::1]` | address_literal |
| e09_upper | simple_ascii | `USER@EXAMPLE.COM` | simple_ascii |
| e10_mixed_case | simple_ascii | `UsEr@ExAmPlE.CoM` | simple_ascii, naive_negative |
| e11_quoted | quoted_local | `"user name"@example.com` | quoted_local, naive_negative |
| e12_quoted_at | quoted_local | `"user@something"@example.com` | quoted_local, naive_negative |
| e13_quoted_escaped | quoted_local | `"foo\"bar"@example.com` | quoted_local, naive_negative |
| e14_display_name | display_name | `User Name <user@example.com>` | display_name, comment_syntax |
| e15_display_quoted | display_name | `"Doe, Jane" <jane@example.com>` | display_name, comment_syntax |
| e16_missing_at | malformed | `userexample.com` | malformed |
| e17_double_at | malformed | `user@@example.com` | malformed |
| e18_empty_local | malformed | `@example.com` | malformed |
| e19_empty_domain | malformed | `user@` | malformed |
| e20_local_dot_end | malformed | `user.@example.com` | malformed |
| e21_local_ddot | malformed | `user..name@example.com` | malformed |
| e22_domain_dot_end | malformed | `user@example.com.` | malformed |
| e23_domain_hyphen_start | malformed | `user@-example.com` | malformed |
| e24_domain_hyphen_end | malformed | `user@example-.com` | malformed |
| e25_domain_underscore | malformed | `user@exam_ple.com` | malformed |
| e26_idna_domain | idna_domain | `user@münchen.example` | idna_domain, unicode_caveat |
| e27_idna_punycode | idna_domain | `user@xn--mnchen-3ya.example` | idna_domain |
| e28_smtputf8_local | smtputf8_local | `josé@example.com` | smtputf8_local, unicode_caveat |
| e29_unicode_norm | unicode_caveat | `café@example.com` | unicode_caveat, smtputf8_local |
| e30_visually_similar | unicode_caveat | `user@exаmple.com` | unicode_caveat, idna_domain |
| e31_local_64_ok | length_limit | `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` | length_limit |
| e32_local_65_bad | length_limit | `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` | length_limit, naive_negative |
| e33_total_254_ok | length_limit | `u@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` | length_limit |
| e34_total_over_254 | length_limit | `u@xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` | length_limit, naive_negative |
| e35_label_63_ok | length_limit | `user@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` | length_limit |
| e36_label_64_bad | length_limit | `user@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` | length_limit, naive_negative |
| e37_whitespace_around | whitespace | `  user@example.com  ` | whitespace |
| e38_newline | malformed | `user@
example.com` | malformed |
| e39_comma_list | comment_syntax | `a@example.com, b@example.com` | comment_syntax |
| e40_bare_name | comment_syntax | `User Name` | comment_syntax |
| e41_typo_plausible | typo_caveat | `user@exampl.com` | typo_caveat, naive_negative |
| e42_no_tld_dot | typo_caveat | `user@example` | typo_caveat, naive_negative |
| e43_plus_rejected | plus_addressing | `bob+spam@example.com` | plus_addressing, naive_negative |
| e44_gmail_dots | provider_specific | `john.smith@example.com` | provider_specific |
| e45_naive_reject_plus | plus_addressing | `tag+filter@example.org` | plus_addressing, naive_negative |
| e46_naive_reject_long_tld | simple_ascii | `me@example.photography` | simple_ascii, naive_negative |
| e47_naive_reject_subdomain | simple_ascii | `x@a.b.c.d.example.com` | simple_ascii, naive_negative |
| e48_fake_but_valid | typo_caveat | `noreply@invalid.test` | typo_caveat, naive_negative |
| e49_lowercase_canon | simple_ascii | `John.Doe@Example.COM` | simple_ascii, naive_negative |
| e50_trailing_dot_local | malformed | `.user@example.com` | malformed |
| e51_underscore_local | simple_ascii | `user_name@example.com` | simple_ascii |
| e52_hyphen_domain | simple_ascii | `user@my-example.com` | simple_ascii |
| e53_numeric_tld | simple_ascii | `user@example.123` | simple_ascii, naive_negative |

## Method details

### simple_contains_one_at_baseline

Pass: 53/53

### permissive_shape_regex_baseline

Pass: 53/53

### naive_ascii_dot_tld_regex

Pass: 53/53

### email_utils_parseaddr_baseline

Pass: 53/53

### local_domain_split_baseline

Pass: 53/53

### quoted_local_part_detector

Pass: 53/53

### idna_domain_encoder

Pass: 53/53

### smtp_utf8_local_part_caveat_detector

Pass: 53/53

### length_limit_checker

Pass: 53/53

### naive_lowercase_canonicalizer

Pass: 53/53

### naive_plus_tag_rejector

Pass: 53/53

### ownership_verification_not_tested_marker

Pass: 53/53

## Observations

- `simple_contains_one_at_baseline` catches the most obvious mistakes but proves nothing about validity or ownership.
- `permissive_shape_regex_baseline` (`^[^@\s]+@[^@\s]+$`) catches obvious entry errors without pretending to be RFC-complete.
- `naive_ascii_dot_tld_regex` rejects valid plus-addresses, long TLDs, and subdomain-heavy addresses – the classic signup-form footgun.
- `email_utils_parseaddr_baseline` is permissive; `parseaddr` returns something for most inputs, even malformed ones.
- `local_domain_split_baseline` correctly skips quoted-local cases rather than splitting naively on `@`.
- `quoted_local_part_detector` identifies quoted local parts (including `@` inside quotes) – naive splitters fail here.
- `idna_domain_encoder` handles IDNA/Punycode for non-ASCII domains; local-part is NOT punycoded (SMTPUTF8 is separate).
- `smtp_utf8_local_part_caveat_detector` flags non-ASCII local parts – SMTPUTF8 support varies by provider.
- `length_limit_checker` enforces RFC 5321 limits: local-part ≤64 octets, total ≤254 octets, domain labels ≤63 octets.
- `naive_lowercase_canonicalizer` lowercases the full address – local-part case may matter (spec says case-sensitive, practice varies).
- `naive_plus_tag_rejector` rejects `+` in local-part – breaks valid plus addressing.
- `ownership_verification_not_tested_marker` – ownership/deliverability requires sending email, intentionally NOT tested.

## Conclusion

Regex validation is easy to overdo. Syntactically valid ≠ deliverable. Deliverable ≠ owned by the user. Plus addressing is valid but often rejected. Provider-specific behavior (e.g. Gmail dots) is not universal. Quoted local parts surprise naive parsers. IDNA applies to domains; SMTPUTF8 local parts are a separate caveat. The only real ownership check is sending a verification email – out of scope for this local lab. This is a toy lab – not a production email validator.

## Reproduction

```
python3 -m py_compile generate_cases.py run_lab.py
python3 generate_cases.py
python3 run_lab.py
```
