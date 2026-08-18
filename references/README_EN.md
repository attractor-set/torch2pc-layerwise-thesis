# References

[Русская версия](README.md)

This public directory is the canonical bibliography surface for dissertation
`v1.0.0`. It contains bibliographic metadata and source traceability, not
redistributed article PDFs.

Local PDFs may be stored in `references/pdfs/`, which is ignored by Git.

For the `v1.0.0` release, the bibliography must pass a complete dissertation
build with no undefined citations. A machine build does not replace substantive
verification against primary sources. Any later bibliography change requires:

- checking each changed BibTeX record against the primary source or publisher
  record;
- ensuring that the source is substantively used by the dissertation or is
  explicitly associated with a later follow-up artifact;
- preserving the correct link from the source to a claim, method, dataset, or
  limitation;
- removing accidental duplicates without rewriting historical bibliographic
  provenance without separate justification;
- rerunning `make thesis-check` and the final document build.
