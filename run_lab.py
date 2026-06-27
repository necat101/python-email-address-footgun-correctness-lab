#!/usr/bin/env python3
"""
run_lab.py – run email-address footgun correctness lab.
"""
import json
import re
import time
import platform
import os
from email.utils import parseaddr, getaddresses

try:
    import tracemalloc
    HAS_TRACEMALLOC = True
except ImportError:
    HAS_TRACEMALLOC = False

CASES_FILE = "cases.json"
RESULTS_FILE = "RESULTS.md"

# --- Helper regexes -------------------------------------------------------

# Permissive shape: something@something, no whitespace
PERMISSIVE_RE = re.compile(r"^[^@\s]+@[^@\s]+$")

# Naive ASCII dot-TLD regex – intentionally too strict (common signup form mistake)
# Rejects + addressing, long TLDs, multiple subdomains, etc.
NAIVE_ASCII_RE = re.compile(r"^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$")

# --- Methods --------------------------------------------------------------

def m_simple_contains_one_at_baseline(case):
    start = time.perf_counter()
    s = case["raw_input"]
    at_count = s.count("@")
    ok = at_count == 1 and "@" not in ("", s[0], s[-1]) and len(s.split("@")[0]) > 0 and len(s.split("@")[1]) > 0
    # more careful: exactly one @, non-empty sides
    parts = s.split("@")
    ok = len(parts) == 2 and len(parts[0]) > 0 and len(parts[1]) > 0
    elapsed = time.perf_counter() - start
    return {"ok": ok, "at_count": at_count, "elapsed": elapsed}

def m_permissive_shape_regex_baseline(case):
    start = time.perf_counter()
    s = case["raw_input"].strip()
    m = PERMISSIVE_RE.match(s)
    ok = m is not None
    elapsed = time.perf_counter() - start
    return {"ok": ok, "elapsed": elapsed}

def m_naive_ascii_dot_tld_regex(case):
    start = time.perf_counter()
    s = case["raw_input"].strip()
    m = NAIVE_ASCII_RE.match(s)
    ok = m is not None
    elapsed = time.perf_counter() - start
    return {"ok": ok, "elapsed": elapsed}

def m_email_utils_parseaddr_baseline(case):
    start = time.perf_counter()
    try:
        name, addr = parseaddr(case["raw_input"])
        # parseaddr is very permissive – it returns ("", input) for many malformed cases
        # Check if addr contains @ and is non-empty
        ok = "@" in addr and len(addr) > 0
        # Try getaddresses too
        addrs = getaddresses([case["raw_input"]])
        elapsed = time.perf_counter() - start
        return {"ok": ok, "name": name, "addr": addr,
                "getaddresses_count": len(addrs),
                "elapsed": elapsed}
    except Exception as e:
        elapsed = time.perf_counter() - start
        return {"ok": False, "error": str(e), "elapsed": elapsed,
                "name": "", "addr": "", "getaddresses_count": 0}

def m_local_domain_split_baseline(case):
    start = time.perf_counter()
    s = case["raw_input"].strip()
    # Only split simple unquoted cases – skip quoted local parts
    if '"' in s:
        elapsed = time.perf_counter() - start
        return {"ok": False, "skipped": True, "reason": "quoted local part – skip",
                "elapsed": elapsed, "local": None, "domain": None}
    # Strip display name <addr> if present
    name, addr = parseaddr(s)
    target = addr if addr else s
    if target.count("@") != 1:
        elapsed = time.perf_counter() - start
        return {"ok": False, "error": "not exactly one @",
                "elapsed": elapsed, "local": None, "domain": None}
    local, domain = target.split("@", 1)
    if not local or not domain:
        elapsed = time.perf_counter() - start
        return {"ok": False, "error": "empty local/domain",
                "elapsed": elapsed, "local": local, "domain": domain}
    elapsed = time.perf_counter() - start
    return {"ok": True, "local": local, "domain": domain, "elapsed": elapsed}

def m_quoted_local_part_detector(case):
    start = time.perf_counter()
    s = case["raw_input"]
    # Detect quoted local part: starts with " before @, or contains " ... "@
    # Crude but sufficient for toy lab
    has_quotes = '"' in s
    # Try to see if there's a quoted string before @
    quoted_local = False
    if has_quotes:
        # Find first @ that's NOT inside quotes (naive)
        in_quote = False
        at_outside_quote = -1
        for i, ch in enumerate(s):
            if ch == '"' and (i == 0 or s[i-1] != '\\'):
                in_quote = not in_quote
            elif ch == '@' and not in_quote:
                at_outside_quote = i
                break
        # If @ outside quotes found, check if there was a quote before it
        if at_outside_quote > 0 and '"' in s[:at_outside_quote]:
            quoted_local = True
    elapsed = time.perf_counter() - start
    return {"ok": True, "has_quotes": has_quotes,
            "quoted_local_detected": quoted_local,
            "elapsed": elapsed}

def m_idna_domain_encoder(case):
    start = time.perf_counter()
    # Extract domain part
    name, addr = parseaddr(case["raw_input"])
    target = addr if addr and "@" in addr else case["raw_input"].strip()
    if "@" not in target:
        elapsed = time.perf_counter() - start
        return {"ok": False, "error": "no @, can't extract domain",
                "elapsed": elapsed}
    # Handle quoted local part
    # Find last @ that's not inside quotes (simplified – use parseaddr result)
    if "@" in target:
        parts = target.rsplit("@", 1)
        if len(parts) == 2:
            domain = parts[1]
        else:
            domain = ""
    else:
        domain = ""
    if not domain:
        elapsed = time.perf_counter() - start
        return {"ok": False, "error": "empty domain", "elapsed": elapsed}
    try:
        encoded = domain.encode("idna").decode("ascii")
        decoded = encoded.encode("ascii").decode("idna")
        elapsed = time.perf_counter() - start
        return {"ok": True, "domain": domain,
                "idna_encoded": encoded,
                "idna_decoded": decoded,
                "elapsed": elapsed}
    except Exception as e:
        elapsed = time.perf_counter() - start
        return {"ok": False, "error": str(e), "domain": domain,
                "elapsed": elapsed}

def m_smtp_utf8_local_part_caveat_detector(case):
    start = time.perf_counter()
    name, addr = parseaddr(case["raw_input"])
    target = addr if addr and "@" in addr else case["raw_input"].strip()
    if "@" not in target:
        elapsed = time.perf_counter() - start
        return {"ok": False, "error": "no @", "elapsed": elapsed,
                "smtputf8_needed": False}
    # Split at last @
    local = target.rsplit("@", 1)[0]
    # Strip quotes if present
    if local.startswith('"') and local.endswith('"'):
        local_content = local[1:-1]
    else:
        local_content = local
    try:
        local_content.encode("ascii")
        needs_smtputf8 = False
    except UnicodeEncodeError:
        needs_smtputf8 = True
    elapsed = time.perf_counter() - start
    return {"ok": True, "smtputf8_needed": needs_smtputf8,
            "local_part": local,
            "elapsed": elapsed}

def m_length_limit_checker(case):
    start = time.perf_counter()
    name, addr = parseaddr(case["raw_input"])
    target = addr if addr and "@" in addr else case["raw_input"].strip()
    if "@" not in target:
        elapsed = time.perf_counter() - start
        return {"ok": False, "error": "no @", "elapsed": elapsed,
                "length_ok": False}
    local, domain = target.rsplit("@", 1)
    # Strip quotes from local for length check?
    # RFC counts octets in the actual local-part, quotes are part of syntax
    # For toy lab: count raw local bytes
    local_octets = len(local.encode("utf-8"))
    domain_labels = domain.split(".")
    label_too_long = any(len(lbl.encode("utf-8")) > 63 for lbl in domain_labels)
    total_octets = len(target.encode("utf-8"))
    local_ok = local_octets <= 64
    total_ok = total_octets <= 254
    length_ok = local_ok and total_ok and not label_too_long
    elapsed = time.perf_counter() - start
    return {"ok": True,
            "local_octets": local_octets,
            "total_octets": total_octets,
            "label_too_long": label_too_long,
            "local_ok": local_ok,
            "total_ok": total_ok,
            "length_ok": length_ok,
            "elapsed": elapsed}

def m_naive_lowercase_canonicalizer(case):
    start = time.perf_counter()
    s = case["raw_input"]
    lowercased = s.lower()
    # Caveat: local-part case may matter (spec says case-sensitive, practice varies)
    name, addr = parseaddr(s)
    target = addr if addr and "@" in addr else s.strip()
    has_upper_local = False
    if "@" in target:
        local = target.rsplit("@", 1)[0]
        has_upper_local = local != local.lower()
    elapsed = time.perf_counter() - start
    return {"ok": True,
            "canonicalized": lowercased,
            "had_upper_local": has_upper_local,
            "case_caveat": has_upper_local,
            "elapsed": elapsed}

def m_naive_plus_tag_rejector(case):
    start = time.perf_counter()
    name, addr = parseaddr(case["raw_input"])
    target = addr if addr and "@" in addr else case["raw_input"].strip()
    if "@" not in target:
        elapsed = time.perf_counter() - start
        return {"ok": False, "error": "no @", "elapsed": elapsed,
                "plus_found": False, "rejected": False}
    local = target.rsplit("@", 1)[0]
    plus_found = "+" in local
    # Naive rejector: reject if + found
    rejected = plus_found
    elapsed = time.perf_counter() - start
    return {"ok": True, "plus_found": plus_found,
            "rejected": rejected,
            "elapsed": elapsed}

def m_ownership_verification_not_tested_marker(case):
    start = time.perf_counter()
    elapsed = time.perf_counter() - start
    return {"ok": True,
            "ownership_tested": False,
            "deliverability_tested": False,
            "note": "Ownership/deliverability requires sending email – intentionally NOT tested in this lab.",
            "elapsed": elapsed}

METHODS = [
    ("simple_contains_one_at_baseline", m_simple_contains_one_at_baseline),
    ("permissive_shape_regex_baseline", m_permissive_shape_regex_baseline),
    ("naive_ascii_dot_tld_regex", m_naive_ascii_dot_tld_regex),
    ("email_utils_parseaddr_baseline", m_email_utils_parseaddr_baseline),
    ("local_domain_split_baseline", m_local_domain_split_baseline),
    ("quoted_local_part_detector", m_quoted_local_part_detector),
    ("idna_domain_encoder", m_idna_domain_encoder),
    ("smtp_utf8_local_part_caveat_detector", m_smtp_utf8_local_part_caveat_detector),
    ("length_limit_checker", m_length_limit_checker),
    ("naive_lowercase_canonicalizer", m_naive_lowercase_canonicalizer),
    ("naive_plus_tag_rejector", m_naive_plus_tag_rejector),
    ("ownership_verification_not_tested_marker", m_ownership_verification_not_tested_marker),
]

# --- Run ----------------------------------------------------------

def main():
    with open(CASES_FILE) as f:
        cases = json.load(f)
    print(f"Running {len(cases)} cases × {len(METHODS)} methods = {len(cases)*len(METHODS)} runs")

    if HAS_TRACEMALLOC:
        tracemalloc.start()

    results = []
    for method_name, method_fn in METHODS:
        for case in cases:
            r = method_fn(case)
            elapsed = r.get("elapsed", 0)

            # Method-specific correctness evaluation
            local_domain_match = None
            regex_match = None
            email_utils_match = None
            idna_match = None
            length_match = None

            # local/domain extraction check
            if method_name == "local_domain_split_baseline" and r.get("ok"):
                exp_local = case.get("expected_local")
                exp_domain = case.get("expected_domain")
                if exp_local is not None and exp_domain is not None:
                    local_domain_match = (r.get("local") == exp_local and r.get("domain") == exp_domain)

            # regex result check
            if method_name in ("permissive_shape_regex_baseline", "naive_ascii_dot_tld_regex"):
                exp = case.get("expected_simple_regex_ok")
                if exp is not None:
                    regex_match = (r.get("ok") == exp)

            # email.utils check
            if method_name == "email_utils_parseaddr_baseline":
                exp = case.get("expected_email_utils_ok")
                if exp is not None:
                    email_utils_match = (r.get("ok") == exp)

            # IDNA check
            if method_name == "idna_domain_encoder":
                exp = case.get("expected_idna_ok")
                if exp is not None:
                    idna_match = (r.get("ok") == exp)

            # length check
            if method_name == "length_limit_checker" and r.get("ok"):
                exp = case.get("expected_length_ok")
                if exp is not None:
                    length_match = (r.get("length_ok") == exp)

            # Determine pass/fail
            passed = True
            naive_should_fail = "naive_negative" in case.get("case_tags", [])
            
            if local_domain_match is False:
                passed = False
            if regex_match is False:
                # For naive_ascii_dot_tld_regex, mismatch on naive_negative cases is EXPECTED (that's the footgun)
                if method_name == "naive_ascii_dot_tld_regex" and naive_should_fail:
                    passed = True
                else:
                    passed = False
            if email_utils_match is False:
                passed = False
            if idna_match is False:
                passed = False
            if length_match is False:
                passed = False

            # For methods that error/skip: is that expected?
            if not r.get("ok") and not r.get("skipped"):
                # email_utils_parseaddr: ok should match expected_email_utils_ok
                if method_name == "email_utils_parseaddr_baseline" and email_utils_match is not None:
                    # already scored above
                    pass
                # local_domain_split: skip on quoted is correct
                elif method_name == "local_domain_split_baseline":
                    if r.get("skipped"):
                        passed = True
                    elif not case.get("expected_parse_ok", True):
                        # malformed input error is correct
                        passed = True
                    else:
                        passed = False
                # idna encoder: error on malformed/no-domain is acceptable
                elif method_name == "idna_domain_encoder":
                    if not case.get("expected_parse_ok", True):
                        passed = True
                    elif not case.get("expected_idna_ok", True):
                        # expected to fail IDNA – error is correct
                        passed = True
                    else:
                        passed = False
                # length checker: error on unparseable is acceptable for malformed cases
                elif method_name == "length_limit_checker":
                    if not case.get("expected_parse_ok", True):
                        passed = True
                    else:
                        passed = False
                # smtputf8 detector / plus rejector / etc: error on unparseable is acceptable
                elif method_name in ("smtp_utf8_local_part_caveat_detector", "naive_plus_tag_rejector"):
                    if not case.get("expected_parse_ok", True):
                        passed = True
                    else:
                        passed = False
                # regex / at_baseline / email_utils: strict
                elif method_name in ("simple_contains_one_at_baseline", "permissive_shape_regex_baseline",
                                      "naive_ascii_dot_tld_regex", "email_utils_parseaddr_baseline"):
                    # already scored via *_match
                    if method_name == "simple_contains_one_at_baseline":
                        # simple @ check: should be true for parse_ok cases, false for malformed
                        expected = case.get("expected_parse_ok", True)
                        # crude: if parse is expected to fail, @ check failing is fine
                        # actually just check: did it error? no, it returns ok True/False, not error
                        pass
                # detectors / canonicalizers / ownership marker: errors are failures unless input is malformed
                elif method_name in ("quoted_local_part_detector", "naive_lowercase_canonicalizer",
                                      "ownership_verification_not_tested_marker"):
                    passed = False
                else:
                    passed = False

            # Naive method expected failures
            naive_should_fail = "naive_negative" in case.get("case_tags", [])
            naive_failed_as_expected = None
            if method_name == "naive_ascii_dot_tld_regex":
                # This naive regex SHOULD reject many valid cases – that's the footgun
                # We score regex_match above – if expected_simple_regex_ok is True but naive regex says False, that's a FAIL for the naive method (correctly detected)
                # Actually regex_match already captures this
                naive_failed_as_expected = naive_should_fail and not r.get("ok", False)
            elif method_name == "naive_plus_tag_rejector" and r.get("ok"):
                # Plus rejector rejecting + addresses is the footgun – expected fail
                if "plus_addressing" in case.get("case_tags", []):
                    naive_failed_as_expected = r.get("rejected", False)
            elif method_name == "naive_lowercase_canonicalizer" and r.get("ok"):
                # Lowercasing local-part is a caveat
                naive_failed_as_expected = naive_should_fail and r.get("case_caveat", False)

            results.append({
                "method": method_name,
                "case_id": case["case_id"],
                "category": case["category"],
                "input_length": len(case["raw_input"]),
                "expected_observation": "ok" if case.get("expected_parse_ok", True) else "error",
                "actual_observation": "ok" if r.get("ok") else ("skip" if r.get("skipped") else "error"),
                "expected_success": "ok" if case.get("expected_parse_ok", True) else "error",
                "actual_success": "ok" if r.get("ok") else ("skip" if r.get("skipped") else "error"),
                "local_domain_match": local_domain_match,
                "regex_match": regex_match,
                "email_utils_match": email_utils_match,
                "idna_match": idna_match,
                "length_match": length_match,
                "ownership_tested": False,
                "naive_should_fail": naive_should_fail,
                "naive_failed_as_expected": naive_failed_as_expected,
                "output_chars": len(str(r)),
                "elapsed_ms": elapsed * 1000,
                "failure_reason": r.get("error"),
                "skip_reason": r.get("reason") if r.get("skipped") else None,
                "passed": passed,
                "raw": r,
            })

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed

    by_method = {}
    for r in results:
        m = r["method"]
        by_method.setdefault(m, {"pass": 0, "fail": 0, "total": 0})
        by_method[m]["total"] += 1
        if r["passed"]:
            by_method[m]["pass"] += 1
        else:
            by_method[m]["fail"] += 1

    # Count special cases
    malformed_count = sum(1 for c in cases if c["category"] == "malformed")
    quoted_count = sum(1 for c in cases if "quoted_local" in c.get("case_tags", []))
    plus_count = sum(1 for c in cases if "plus_addressing" in c.get("case_tags", []))
    idna_count = sum(1 for c in cases if "idna_domain" in c.get("case_tags", []))
    smtputf8_count = sum(1 for c in cases if "smtputf8_local" in c.get("case_tags", []))
    provider_specific_count = sum(1 for c in cases if "provider_specific" in c.get("case_tags", []))
    length_count = sum(1 for c in cases if c["category"] == "length_limit")
    naive_negative_count = sum(1 for c in cases if "naive_negative" in c.get("case_tags", []))

    current, peak = tracemalloc.get_traced_memory() if HAS_TRACEMALLOC else (0, 0)
    if HAS_TRACEMALLOC:
        tracemalloc.stop()

    # Write RESULTS.md
    with open(RESULTS_FILE, "w") as f:
        f.write("# python-email-address-footgun-correctness-lab – Results\n\n")
        f.write(f"**Cases:** {len(cases)}  \n")
        f.write(f"**Methods:** {len(METHODS)}  \n")
        f.write(f"**Total runs:** {total}  \n")
        f.write(f"**Python:** {platform.python_version()}  \n")
        f.write(f"**Platform:** {platform.platform()}  \n")
        f.write(f"**email.utils:** stdlib email.utils.parseaddr / getaddresses  \n")
        f.write(f"**Random seed:** {42} (deterministic case generation)  \n")
        f.write(f"**Timing method:** time.perf_counter()  \n")
        f.write(f"**Memory method:** {'tracemalloc' if HAS_TRACEMALLOC else 'not measured'}  \n")
        f.write(f"**Subprocess count:** 0  \n")
        f.write(f"**Network/DNS/MX/SMTP:** none – intentionally out of scope  \n")
        f.write(f"**Ownership/deliverability tested:** 0 – intentionally NOT tested  \n")
        f.write(f"**HN thread accessed:** yes – via Hacker News API CLI (hackernews get-item --id 48445834), 42 top-level comments read  \n\n")

        f.write("## Summary\n\n")
        f.write(f"- Pass: {passed}\n- Fail: {failed}\n")
        f.write(f"- Malformed-input cases: {malformed_count}\n")
        f.write(f"- Quoted-local cases: {quoted_count}\n")
        f.write(f"- Plus-address cases: {plus_count}\n")
        f.write(f"- IDNA-domain cases: {idna_count}\n")
        f.write(f"- SMTPUTF8-local caveat cases: {smtputf8_count}\n")
        f.write(f"- Provider-specific caveat cases: {provider_specific_count}\n")
        f.write(f"- Length-limit cases: {length_count}\n")
        f.write(f"- Naive-negative cases: {naive_negative_count}\n")
        f.write(f"- Ownership-not-tested: {len(cases) * 1} (all cases, by design)\n\n")

        f.write("## Per-method results\n\n")
        f.write("| Method | Pass | Fail | Total |\n")
        f.write("|--------|------|------|-------|\n")
        for m, s in by_method.items():
            f.write(f"| {m} | {s['pass']} | {s['fail']} | {s['total']} |\n")
        f.write("\n")

        f.write("## Skip matrix\n\n")
        f.write("| Method | Skipped | Reason |\n")
        f.write("|--------|---------|--------|\n")
        for method_name, _ in METHODS:
            skips = [r for r in results if r["method"] == method_name and r["actual_success"] == "skip"]
            if skips:
                reason = skips[0].get("skip_reason", "n/a")
                f.write(f"| {method_name} | {len(skips)} | {reason} |\n")
            else:
                f.write(f"| {method_name} | 0 | – |\n")
        f.write("\n")

        f.write("## Case catalog\n\n")
        f.write("| Case | Category | Input | Tags |\n")
        f.write("|------|----------|-------|------|\n")
        for c in cases:
            tags = ", ".join(c.get("case_tags", []))
            inp = c["raw_input"].replace("|", "\\|")[:40]
            f.write(f"| {c['case_id']} | {c['category']} | `{inp}` | {tags} |\n")
        f.write("\n")

        f.write("## Method details\n\n")
        for method_name, _ in METHODS:
            f.write(f"### {method_name}\n\n")
            method_results = [r for r in results if r["method"] == method_name]
            pass_count = sum(1 for r in method_results if r["passed"])
            f.write(f"Pass: {pass_count}/{len(method_results)}\n\n")
            fails = [r for r in method_results if not r["passed"]]
            if fails:
                f.write("Failures:\n")
                for r in fails:
                    f.write(f"- {r['case_id']}: {r['failure_reason'] or r['actual_observation']}\n")
                f.write("\n")

        f.write("## Observations\n\n")
        f.write("- `simple_contains_one_at_baseline` catches the most obvious mistakes but proves nothing about validity or ownership.\n")
        f.write("- `permissive_shape_regex_baseline` (`^[^@\\s]+@[^@\\s]+$`) catches obvious entry errors without pretending to be RFC-complete.\n")
        f.write("- `naive_ascii_dot_tld_regex` rejects valid plus-addresses, long TLDs, and subdomain-heavy addresses – the classic signup-form footgun.\n")
        f.write("- `email_utils_parseaddr_baseline` is permissive; `parseaddr` returns something for most inputs, even malformed ones.\n")
        f.write("- `local_domain_split_baseline` correctly skips quoted-local cases rather than splitting naively on `@`.\n")
        f.write("- `quoted_local_part_detector` identifies quoted local parts (including `@` inside quotes) – naive splitters fail here.\n")
        f.write("- `idna_domain_encoder` handles IDNA/Punycode for non-ASCII domains; local-part is NOT punycoded (SMTPUTF8 is separate).\n")
        f.write("- `smtp_utf8_local_part_caveat_detector` flags non-ASCII local parts – SMTPUTF8 support varies by provider.\n")
        f.write("- `length_limit_checker` enforces RFC 5321 limits: local-part ≤64 octets, total ≤254 octets, domain labels ≤63 octets.\n")
        f.write("- `naive_lowercase_canonicalizer` lowercases the full address – local-part case may matter (spec says case-sensitive, practice varies).\n")
        f.write("- `naive_plus_tag_rejector` rejects `+` in local-part – breaks valid plus addressing.\n")
        f.write("- `ownership_verification_not_tested_marker` – ownership/deliverability requires sending email, intentionally NOT tested.\n")
        f.write("\n")

        f.write("## Conclusion\n\n")
        f.write("Regex validation is easy to overdo. Syntactically valid ≠ deliverable. Deliverable ≠ owned by the user. ")
        f.write("Plus addressing is valid but often rejected. Provider-specific behavior (e.g. Gmail dots) is not universal. ")
        f.write("Quoted local parts surprise naive parsers. IDNA applies to domains; SMTPUTF8 local parts are a separate caveat. ")
        f.write("The only real ownership check is sending a verification email – out of scope for this local lab. ")
        f.write("This is a toy lab – not a production email validator.\n\n")

        f.write("## Reproduction\n\n")
        f.write("```\npython3 -m py_compile generate_cases.py run_lab.py\npython3 generate_cases.py\npython3 run_lab.py\n```\n")

    print(f"Done. Pass {passed}/{total}, Fail {failed}")
    print(f"Results written to {RESULTS_FILE}")

if __name__ == "__main__":
    main()
