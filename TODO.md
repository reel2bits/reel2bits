# GLOBAL

- Workers for crons
  - Some ideas about sanity checking transcodings broken, or not done totaly etc.

- Tags for tracks
- FTS Search for sounds

- Some basic statistics of files
  - Played from player, downloads (transcode, orig)

- Album
  - switch song duration stay sometimes

- Emails notifications (register, password changed, track ready)

- Slugs: BEFORE, and UNIQUE; Some things weird on that side IIRC

- Better handle transcoding and waveform generation for FLAC and OGG (audiowaveform should use the transcoded mp3 file)
  - to check, might be already done...

# Design

- Needs improvements

# Low priority:
- SQL optimization
- translations update (PR blocked because of library weirdness)


- Check for sentry in:
  - waitress (web)
  - celery (workers)

- Celery things to add in web interface:
  - log user
    - jobs failed
    - retry
  - admin interface
    - jobs failed
    - retry

# ACTIVITYPUB

PR in progress.
