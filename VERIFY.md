# VERIFY.md

Fresh-clone verification transcript.

```
$ git clone https://github.com/necat101/python-email-address-footgun-correctness-lab.git
$ cd python-email-address-footgun-correctness-lab

$ python3 -m py_compile generate_cases.py run_lab.py
py_compile: OK

$ python3 generate_cases.py
Generated 53 cases
Wrote cases.json

$ python3 run_lab.py
Running 53 cases × 12 methods = 636 runs
Done. Pass 636/636, Fail 0
Results written to RESULTS.md
```

Verified commit: 76c5506d9220744765aef48710c67aee013aa9be

This commit (76c5506) contains the lab code, cases, and RESULTS.md. It was fresh-clone verified with 636/636 pass.

Current HEAD only adds this VERIFY.md file on top of 76c5506 – code and results are unchanged. I locally re-ran HEAD with identical 636/636 pass results, but that run is NOT captured in the transcript above.

Python: 3.12.3  
Platform: Linux-6.17.0-1009-aws-x86_64-with-glibc2.39

Case count: 53  
Method count: 12  
Total runs: 636  
Pass: 636  
Fail: 0
