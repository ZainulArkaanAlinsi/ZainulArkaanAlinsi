# Refresh the profile the moment you push anywhere

The profile workflow already runs on every push to this repo and once an hour.
To make a push to **any other repo** update the commit log within a minute,
add this workflow to that repo as `.github/workflows/ping-profile.yml`:

```yaml
name: ping-profile
on:
  push:
    branches: [main, master]
jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - run: |
          curl -sf -X POST \
            -H "Authorization: Bearer ${{ secrets.PROFILE_DISPATCH_TOKEN }}" \
            -H "Accept: application/vnd.github+json" \
            https://api.github.com/repos/ZainulArkaanAlinsi/ZainulArkaanAlinsi/dispatches \
            -d '{"event_type":"profile-refresh"}'
```

`PROFILE_DISPATCH_TOKEN` is a fine-grained personal access token with
**Contents: read and write** on the `ZainulArkaanAlinsi/ZainulArkaanAlinsi`
repository only, saved as a secret in the repo that pings.
