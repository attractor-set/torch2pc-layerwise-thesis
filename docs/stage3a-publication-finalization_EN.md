# Stage 3A publication finalization

`scripts/finalize_stage3a_publication.py` synchronizes repository status with
the completed layer-wise campaign, installs metadata-aware aggregation,
creates bilingual completion records, and adds a provenance correction note
without changing primary observations.

The original `COMPOSE_RESOLVED.yaml` remains preserved. The correction records
the stale variable rather than rewriting the historical snapshot.

After running the finalizer, regenerate summaries from the raw directory,
verify row counts and hashes, and stage only publication artifacts.
