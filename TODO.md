# GLOBAL

- Workers for crons
  - Some ideas about sanity checking transcodings broken, or not done totaly etc.

- Tags for tracks
- FTS Search for sounds

- Some basic statistics of files
  - Played from player, downloads (transcode, orig)

- Slugs: BEFORE, and UNIQUE; Some things weird on that side IIRC

- Better handle transcoding and waveform generation for FLAC and OGG (audiowaveform should use the transcoded mp3 file)
  - to check, might be already done...

# Low priority:
- SQL optimization

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

- deleted sound : test / fix handle correctly, tombstone thing

- Accessing a deleted object/activity should return a Tombstone
