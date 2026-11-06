# Contributing to StepSheet

Thanks for your interest in StepSheet. This is a small, dependency-free project —
a single `StepSheet.html` file plus an optional browser-extension wrapper.

## Ground rules

- **No real work content in the repo.** Never commit real `.soe` documents, shop
  photos, or proprietary/confidential instructions. Use synthetic sample data for
  bug reports and demos. (`.gitignore` blocks these by default — don't override it.)
- **Keep it dependency-free.** StepSheet is intentionally one self-contained HTML file
  with no build step, no CDN, and no external libraries, so it runs offline from a
  `file://` path. Please don't add runtime dependencies or a bundler without discussion.
- **No secrets.** Don't commit API keys, tokens, or credentials of any kind.

## How to contribute

1. Open an issue describing the bug or proposed change first.
2. Fork the repo and make your change in a branch.
3. Test in current Chrome and Edge at minimum; note what you tested.
4. Open a pull request referencing the issue.

## Licensing of contributions

By submitting a contribution, you agree that your contribution is your own original
work (or that you have the right to submit it) and that it is licensed to this project
and its users under the project's [MIT License](LICENSE). Do not submit code copied from
proprietary sources, from an employer, or from incompatibly-licensed projects.

## Disclaimer

StepSheet is provided "AS IS", without warranty of any kind, as stated in the
[LICENSE](LICENSE). It is a personal project and is not affiliated with, endorsed by, or
derived from any other application or company. You are responsible for validating any
output (including PDFs and translations) before relying on it.
