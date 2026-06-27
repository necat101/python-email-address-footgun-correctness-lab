#!/usr/bin/env python3
"""
generate_cases.py – build deterministic fake email-address test cases.

All addresses use fake/example domains only. No real user emails.
No DNS, MX, SMTP, or network calls.
"""
import json
import os

CASES_FILE = "cases.json"
SEED = 42

cases = []


def add_case(case_id, category, raw_input,
             expected_local=None, expected_domain=None,
             expected_parse_ok=True,
             expected_simple_regex_ok=None,
             expected_email_utils_ok=None,
             expected_idna_ok=True,
             expected_length_ok=True,
             expected_ownership_tested=False,
             case_tags=None,
             notes=""):
    cases.append({
        "case_id": case_id,
        "category": category,
        "raw_input": raw_input,
        "expected_local": expected_local,
        "expected_domain": expected_domain,
        "expected_parse_ok": expected_parse_ok,
        "expected_simple_regex_ok": expected_simple_regex_ok,
        "expected_email_utils_ok": expected_email_utils_ok,
        "expected_idna_ok": expected_idna_ok,
        "expected_length_ok": expected_length_ok,
        "expected_ownership_tested": expected_ownership_tested,
        "case_tags": case_tags or [category],
        "notes": notes,
    })


# Normal / simple
add_case("e01_simple", "simple_ascii", "user@example.com",
         expected_local="user", expected_domain="example.com",
         expected_simple_regex_ok=True, expected_email_utils_ok=True,
         case_tags=["simple_ascii"])
add_case("e02_plus", "plus_addressing", "user+tag@example.com",
         expected_local="user+tag", expected_domain="example.com",
         expected_simple_regex_ok=True, expected_email_utils_ok=True,
         case_tags=["plus_addressing", "naive_negative"])
add_case("e03_subdomain", "simple_ascii", "user@mail.example.com",
         expected_local="user", expected_domain="mail.example.com",
         expected_simple_regex_ok=True, expected_email_utils_ok=True,
         case_tags=["simple_ascii"])
add_case("e04_long_tld", "simple_ascii", "user@example.consulting",
         expected_local="user", expected_domain="example.consulting",
         expected_simple_regex_ok=True, expected_email_utils_ok=True,
         case_tags=["simple_ascii", "naive_negative"],
         notes="long TLD – naive regex may reject")
add_case("e05_multi_dot", "simple_ascii", "sean@foo.bar.baz",
         expected_local="sean", expected_domain="foo.bar.baz",
         expected_simple_regex_ok=True, expected_email_utils_ok=True,
         case_tags=["simple_ascii", "naive_negative"],
         notes="multiple dots in domain – HN comment: rejected ~30% of the time")

# Single-label / address literal
add_case("e06_localhost", "simple_ascii", "user@localhost",
         expected_local="user", expected_domain="localhost",
         expected_simple_regex_ok=True,
         expected_email_utils_ok=True,
         case_tags=["simple_ascii", "typo_caveat", "naive_negative"],
         notes="single-label host – valid in intranet, often rejected by naive validators")
add_case("e07_addr_literal_v4", "address_literal", "user@[127.0.0.1]",
         expected_local="user", expected_domain="[127.0.0.1]",
         expected_email_utils_ok=False,
         case_tags=["address_literal"],
         notes="RFC 5321 address literal")
add_case("e08_addr_literal_v6", "address_literal", "user@[IPv6:2001:db8::1]",
         expected_local="user", expected_domain="[IPv6:2001:db8::1]",
         expected_email_utils_ok=False,
         case_tags=["address_literal"],
         notes="IPv6 address literal")

# Case
add_case("e09_upper", "simple_ascii", "USER@EXAMPLE.COM",
         expected_local="USER", expected_domain="EXAMPLE.COM",
         expected_simple_regex_ok=True, expected_email_utils_ok=True,
         case_tags=["simple_ascii"],
         notes="uppercase – domain case-insensitive, local-part messy")
add_case("e10_mixed_case", "simple_ascii", "UsEr@ExAmPlE.CoM",
         expected_local="UsEr", expected_domain="ExAmPlE.CoM",
         expected_simple_regex_ok=True, expected_email_utils_ok=True,
         case_tags=["simple_ascii", "naive_negative"],
         notes="case-folding caveat – naive canonicalizer lowercases all")

# Quoted local parts
add_case("e11_quoted", "quoted_local", '"user name"@example.com',
         expected_local='"user name"', expected_domain="example.com",
         expected_simple_regex_ok=False,
         expected_email_utils_ok=True,
         case_tags=["quoted_local", "naive_negative"])
add_case("e12_quoted_at", "quoted_local", '"user@something"@example.com',
         expected_local='"user@something"', expected_domain="example.com",
         expected_simple_regex_ok=False,
         expected_email_utils_ok=True,
         case_tags=["quoted_local", "naive_negative"],
         notes="HN: ^[^@]+@[^@\\s]+$ rejects this valid address")
add_case("e13_quoted_escaped", "quoted_local", r'"foo\"bar"@example.com',
         expected_local=r'"foo\"bar"', expected_domain="example.com",
         expected_simple_regex_ok=True,
         expected_email_utils_ok=True,
         case_tags=["quoted_local", "naive_negative"],
         notes="escaped quote in quoted local part")

# Display name / comments
add_case("e14_display_name", "display_name", "User Name <user@example.com>",
         expected_local="user", expected_domain="example.com",
         expected_email_utils_ok=True,
         case_tags=["display_name", "comment_syntax"])
add_case("e15_display_quoted", "display_name", '"Doe, Jane" <jane@example.com>',
         expected_local="jane", expected_domain="example.com",
         expected_email_utils_ok=True,
         case_tags=["display_name", "comment_syntax"])

# Malformed
add_case("e16_missing_at", "malformed", "userexample.com",
         expected_parse_ok=False,
         expected_simple_regex_ok=False,
         expected_email_utils_ok=False,
         case_tags=["malformed"])
add_case("e17_double_at", "malformed", "user@@example.com",
         expected_parse_ok=False,
         expected_simple_regex_ok=False,
         case_tags=["malformed"],
         notes="two unquoted @ – invalid")
add_case("e18_empty_local", "malformed", "@example.com",
         expected_parse_ok=False,
         expected_simple_regex_ok=False,
         case_tags=["malformed"])
add_case("e19_empty_domain", "malformed", "user@",
         expected_parse_ok=False,
         expected_simple_regex_ok=False,
         case_tags=["malformed"])
add_case("e20_local_dot_end", "malformed", "user.@example.com",
         expected_parse_ok=False,
         expected_simple_regex_ok=True,
         case_tags=["malformed"],
         notes="local part ending in dot")
add_case("e21_local_ddot", "malformed", "user..name@example.com",
         expected_parse_ok=False,
         expected_simple_regex_ok=True,
         case_tags=["malformed"],
         notes="consecutive dots in local part")

# Domain quirks
add_case("e22_domain_dot_end", "malformed", "user@example.com.",
         expected_parse_ok=False,
         case_tags=["malformed"],
         notes="domain ending in dot – caveat")
add_case("e23_domain_hyphen_start", "malformed", "user@-example.com",
         expected_parse_ok=False,
         case_tags=["malformed"],
         notes="domain label starting with hyphen")
add_case("e24_domain_hyphen_end", "malformed", "user@example-.com",
         expected_parse_ok=False,
         case_tags=["malformed"],
         notes="domain label ending with hyphen")
add_case("e25_domain_underscore", "malformed", "user@exam_ple.com",
         expected_parse_ok=False,
         case_tags=["malformed"],
         notes="underscore in domain – invalid per DNS")

# IDNA / Unicode
add_case("e26_idna_domain", "idna_domain", "user@münchen.example",
         expected_local="user", expected_domain="münchen.example",
         expected_idna_ok=True,
         expected_email_utils_ok=True,
         case_tags=["idna_domain", "unicode_caveat"])
add_case("e27_idna_punycode", "idna_domain", "user@xn--mnchen-3ya.example",
         expected_local="user", expected_domain="xn--mnchen-3ya.example",
         expected_idna_ok=True,
         expected_email_utils_ok=True,
         case_tags=["idna_domain"])
add_case("e28_smtputf8_local", "smtputf8_local", "josé@example.com",
         expected_local="josé", expected_domain="example.com",
         expected_email_utils_ok=True,
         case_tags=["smtputf8_local", "unicode_caveat"],
         notes="non-ASCII local part – SMTPUTF8 caveat")
add_case("e29_unicode_norm", "unicode_caveat", "café@example.com",
         expected_local="café", expected_domain="example.com",
         case_tags=["unicode_caveat", "smtputf8_local"],
         notes="Unicode normalization caveat – é as U+00E9 vs e + U+0301")
add_case("e30_visually_similar", "unicode_caveat", "user@exаmple.com",
         expected_local="user", expected_domain="exаmple.com",
         case_tags=["unicode_caveat", "idna_domain"],
         notes="Cyrillic а (U+0430) looks like Latin a – homograph caveat")

# Length limits
# RFC 5321: local-part max 64 octets, total max 254
add_case("e31_local_64_ok", "length_limit", "a"*64 + "@example.com",
         expected_local="a"*64, expected_domain="example.com",
         expected_length_ok=True,
         case_tags=["length_limit"])
add_case("e32_local_65_bad", "length_limit", "a"*65 + "@example.com",
         expected_local="a"*65, expected_domain="example.com",
         expected_length_ok=False,
         case_tags=["length_limit", "naive_negative"],
         notes="local-part 65 octets – over RFC 5321 limit")
add_case("e33_total_254_ok", "length_limit",
         "u@" + "a"*60 + "." + "b"*60 + "." + "c"*60 + "." + "d"*62 + ".com",
         expected_length_ok=True,
         case_tags=["length_limit"],
         notes="total ~250 bytes, under 254 limit")
add_case("e34_total_over_254", "length_limit",
         "u@" + "x"*250 + ".com",
         expected_length_ok=False,
         expected_idna_ok=False,
         case_tags=["length_limit", "naive_negative"])
add_case("e35_label_63_ok", "length_limit",
         "user@" + "a"*63 + ".com",
         expected_domain="a"*63 + ".com",
         expected_length_ok=True,
         case_tags=["length_limit"])
add_case("e36_label_64_bad", "length_limit",
         "user@" + "a"*64 + ".com",
         expected_length_ok=False,
         expected_idna_ok=False,
         case_tags=["length_limit", "naive_negative"],
         notes="domain label 64 octets – over 63 limit")

# Whitespace / control
add_case("e37_whitespace_around", "whitespace", "  user@example.com  ",
         expected_local="user", expected_domain="example.com",
         expected_simple_regex_ok=True,
         case_tags=["whitespace"],
         notes="whitespace around – should trim")
add_case("e38_newline", "malformed", "user@\nexample.com",
         expected_parse_ok=False,
         expected_simple_regex_ok=False,
         case_tags=["malformed"],
         notes="newline/control char – invalid")

# List / parsing caveats
add_case("e39_comma_list", "comment_syntax", "a@example.com, b@example.com",
         expected_local="a", expected_domain="example.com",
         expected_email_utils_ok=False,
         expected_parse_ok=False,
         case_tags=["comment_syntax"],
         notes="comma-separated list – parseaddr/getaddresses caveat")
add_case("e40_bare_name", "comment_syntax", "User Name",
         expected_parse_ok=False,
         case_tags=["comment_syntax"],
         notes="bare name, no @ – parseaddr may accept oddly")

# Typo / fake caveats
add_case("e41_typo_plausible", "typo_caveat", "user@exampl.com",
         expected_local="user", expected_domain="exampl.com",
         expected_simple_regex_ok=True,
         expected_email_utils_ok=True,
         case_tags=["typo_caveat", "naive_negative"],
         notes="typo-looking but syntactically valid – can't detect without sending mail")
add_case("e42_no_tld_dot", "typo_caveat", "user@example",
         expected_local="user", expected_domain="example",
         expected_simple_regex_ok=True,
         expected_email_utils_ok=True,
         case_tags=["typo_caveat", "naive_negative"],
         notes="no TLD dot – valid for intranet, often a typo")
add_case("e43_plus_rejected", "plus_addressing", "bob+spam@example.com",
         expected_local="bob+spam", expected_domain="example.com",
         expected_simple_regex_ok=True,
         expected_email_utils_ok=True,
         case_tags=["plus_addressing", "naive_negative"],
         notes="plus addressing – naive_plus_tag_rejector should fail")
add_case("e44_gmail_dots", "provider_specific", "john.smith@example.com",
         expected_local="john.smith", expected_domain="example.com",
         expected_simple_regex_ok=True,
         expected_email_utils_ok=True,
         case_tags=["provider_specific"],
         notes="Gmail dot equivalence is provider-specific, NOT universal")

# Naive regex trap cases
add_case("e45_naive_reject_plus", "plus_addressing", "tag+filter@example.org",
         expected_local="tag+filter", expected_domain="example.org",
         case_tags=["plus_addressing", "naive_negative"],
         notes="naive_ascii_dot_tld_regex rejects +")
add_case("e46_naive_reject_long_tld", "simple_ascii", "me@example.photography",
         expected_local="me", expected_domain="example.photography",
         case_tags=["simple_ascii", "naive_negative"],
         notes="naive regex rejects long TLD")
add_case("e47_naive_reject_subdomain", "simple_ascii", "x@a.b.c.d.example.com",
         expected_local="x", expected_domain="a.b.c.d.example.com",
         case_tags=["simple_ascii", "naive_negative"],
         notes="naive regex rejects subdomain-heavy")
add_case("e48_fake_but_valid", "typo_caveat", "noreply@invalid.test",
         expected_local="noreply", expected_domain="invalid.test",
         expected_simple_regex_ok=True,
         expected_email_utils_ok=True,
         case_tags=["typo_caveat", "naive_negative"],
         notes="syntactically valid, undeliverable – regex can't catch this")
add_case("e49_lowercase_canon", "simple_ascii", "John.Doe@Example.COM",
         expected_local="John.Doe", expected_domain="Example.COM",
         expected_simple_regex_ok=True,
         expected_email_utils_ok=True,
         case_tags=["simple_ascii", "naive_negative"],
         notes="naive_lowercase_canonicalizer caveat – local-part case may matter")

# More edge cases
add_case("e50_trailing_dot_local", "malformed", ".user@example.com",
         expected_parse_ok=False,
         case_tags=["malformed"],
         notes="local part starting with dot")
add_case("e51_underscore_local", "simple_ascii", "user_name@example.com",
         expected_local="user_name", expected_domain="example.com",
         expected_simple_regex_ok=True,
         expected_email_utils_ok=True,
         case_tags=["simple_ascii"],
         notes="underscore in local-part – valid")
add_case("e52_hyphen_domain", "simple_ascii", "user@my-example.com",
         expected_local="user", expected_domain="my-example.com",
         expected_simple_regex_ok=True,
         expected_email_utils_ok=True,
         case_tags=["simple_ascii"])
add_case("e53_numeric_tld", "simple_ascii", "user@example.123",
         expected_local="user", expected_domain="example.123",
         expected_simple_regex_ok=True,
         expected_email_utils_ok=True,
         case_tags=["simple_ascii", "naive_negative"],
         notes="numeric TLD – naive regex may reject")


print(f"Generated {len(cases)} cases")
os.makedirs("cases_out", exist_ok=True)
with open(CASES_FILE, "w") as f:
    json.dump(cases, f, indent=2)
print(f"Wrote {CASES_FILE}")
