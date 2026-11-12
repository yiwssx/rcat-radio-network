# RRN-04 — One Live DJ handoff and automatic AutoDJ return

**Scope:** one existing LibreTime 4.5.0 + bundled Icecast 2.4.4 station on `rcatiotserver`. Private, owner-controlled acceptance only. No deployment, public radio launch, proxy/DNS/firewall edit, new DNAS, duplicate AutoDJ test or change to the Docker Engine.

## Accepted starting evidence (2026-11-12)

- The owner reported `RRN02_DEPLOY=STARTED`; the targeted radio-only snapshot showed **10/10** containers running with zero restarts, LibreTime UI and Icecast status **HTTP 200**.
- The owner supplied two screenshots: LibreTime Dashboard **ON AIR** and `My Show` scheduled, playing `Wavecont - Inspire` (Corporate Background Music), and a Chrome audio player running the existing `http://127.0.0.1:8600/main.mp3` stream. The owner explicitly confirmed that the AutoDJ test **passed**.
- This establishes one private, **operator-confirmed audible scheduled playout** through the intended Icecast mount. It does **not** establish a public launch, an independently verified recording, valid music redistribution rights, a separate LibreTime Playlist workflow, changed admin credentials, or Live DJ/fallback.

## Priority and credentials

1. **Before further user provisioning or any public access**, change the built-in LibreTime `admin` default password via the username at top right, **if not already changed**. Official LibreTime 4.x recommends avoiding default `admin` in production. Never paste credentials into GitHub, screenshots or chat.
2. Create one dedicated **DJ** account with its own password in LibreTime's user-management UI, not the built-in `admin` or the Icecast source/admin password. See the LibreTime *Managing users* documentation.
3. In **Calendar**, edit the show that will be live. Assign the DJ under **Who**, enable the **Show Source / Live Stream Input** option and choose **LibreTime authentication** for that show. The Show Source credentials are those of the assigned DJ; connection may be rejected outside the DJ's assigned on-air window. Do **not** use Master Source as a shortcut.
4. In **Settings → Streams**, enable and save **Auto Switch On** and **Auto Switch Off** for input-source handoff. If a manual switch is necessary, check the Show Source toggle in the Source Streams panel. Master Source has higher priority and should remain unused for this test.

## DJ encoder from the same Windows client (private SSH tunnel)

Leave the existing browser tunnels for local LibreTime UI `127.0.0.1:8700` and listener `127.0.0.1:8600` intact. Open a **separate Windows PowerShell session**:

```powershell
ssh -N -L 127.0.0.1:8605:127.0.0.1:8605 rcat_iot_admin@10.10.1.100
```

The SSH session is a **private local connection** only; do not open TCP 8605 in the firewall and do not modify public ingress. Use B.U.T.T. or Mixxx (free) to feed **LibreTime Liquidsoap Show Source**, not Icecast directly.

**BUTT → Settings → Main → Server → Add:**

| Field | Value |
| --- | --- |
| Name | RCAT LibreTime Show |
| Type | Icecast |
| Address / Host | `127.0.0.1` |
| Port | `8605` (SSH tunnel forwards to host-loopback `8605`, mapped to Liquidsoap internal `8002`) |
| Icecast mountpoint | `/show` |
| User | Dedicated LibreTime DJ username assigned to active show |
| Password | That DJ account password only; never the admin/Icecast-source password |

In **Audio**, select the intended microphone/mixer interface. Avoid microphone feedback: headphones for monitoring, and do not route the browser's Icecast monitor back into the encoder microphone input.

## Single meaningful acceptance test

1. Keep an **authorized audio track scheduled** within an active Show, so scheduled fallback has actual content. Use the already observed `/main.mp3` monitor: **do not re-test the existing AutoDJ setup from scratch**.
2. During that DJ's assigned on-air time, begin the microphone/live encoder stream in BUTT to `/show` on local port 8605. Confirm one live source is connected and source priority changes to **Show Source** (automatically if Auto Switch On is enabled).
3. Listen to the **same** browser stream `http://127.0.0.1:8600/main.mp3`; confirm audible **Live DJ** input, not the scheduled track.
4. Stop/disconnect BUTT **once**. With Auto Switch Off enabled, verify the **same** listener automatically returns to the already scheduled AutoDJ audio without manually restarting a container, rescheduling music or refreshing network routing.
5. Record a simple result in existing [RRN-04 #6](../issues/6): `LIVE_DJ_HANDOFF=PASS|FAIL`, `AUTO_DJ_RETURN=PASS|FAIL`. Include only nonsecret observations; reuse already accepted RRN-02/RRN-03 audio proof.

**Failure handling:** If encoder authentication fails, check the DJ's show assignment, **Who**, Show Source authentication and show time first; if connected but not on-air, check Stream Settings and Show Source switch. A Live DJ input is **not** the Icecast listener output. Do not open more ports, try admin/Master Source credentials, restart the radio project or touch unrelated RCAT services merely to bypass a failed DJ login.

## Sources

- [LibreTime 4.x — Broadcasting live](https://libretime.org/docs/user-manual/live-broadcast/)
- [LibreTime 4.x — Stream settings and source priority](https://libretime.org/docs/user-manual/settings/)
- [LibreTime 4.x — Scheduling shows](https://libretime.org/docs/user-manual/scheduling-shows/)
- [LibreTime 4.x — Managing users](https://libretime.org/docs/user-manual/users/)
