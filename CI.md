# CI

##  cloud.azure_ops Collection

GitHub Actions are used to run the Continuous Integration for redhat-cop/cloud.azure_ops collection. The workflows used for the CI can be found [here](https://github.com/redhat-cop/cloud.aws_troubleshooting/tree/main/.github/workflows). These workflows include jobs to run the sanity tests, linters and changelog check. The following table lists the python and ansible versions against which these jobs are run.

| Jobs | Description | Python Versions | Ansible Versions |
| ------ |-------| ------ | -----------|
| changelog |Checks for the presence of Changelog fragments | 3.9 | devel |
| Linters | Runs `black` and `flake8` on plugins and tests | 3.9 | devel |
| Sanity | Runs absible sanity checks | 3.8, 3.9, 3.10, 3.11 | Stable-2.12, 2.13, 2.14 (not on py 3.11), Stable-2.15+ (not on 3.8) |
