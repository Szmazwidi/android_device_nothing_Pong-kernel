# Nothing Phone (2), community CLG43 prebuilt

This candidate packages the complete source-built 6.18.60 community kernel and
293 signed modules, with 100 first-stage modules. It is selected together with
the matching Pong community device tree and source manifest.

Kernel SHA-256 is
`c6a70ae3ff9ce6042b9a52c6d0548759ca4df6236a9aa5e3a8e4a6b3459a103d`.
`source.json`, the public certificate and `SHA256SUMS` record the imported bank.
No private signing key is included.

The community kernel has `CONFIG_MODULE_SIG_FORCE=y` and SHA-256 signature
verification. `CONFIG_PONG_LAB_GUARDS` is disabled, so this build omits the
fixed-UFS write/mount policy and exact-payload restriction of the laboratory
handset. The LAB cohorts and their history remain on their development branches.

## Source and validation

The module source branch is `pong-a17-6.18.60-community-clg43` in
`Szmazwidi/android_kernel_nothing_sm8475-modules-6.18`. Its pinned manifest and
`docs/build-reference-6.18.60-community.json` select 209 vendor modules and
84 GKI modules from the matching kernel sources.

The full bank was built into a new output directory, checked for architecture,
coverage, dependencies, imported/exported CRCs and runtime contracts, and
signed with the final kernel certificate. Diskless QEMU checked forced
signature enforcement, valid trusted modules and rejection of unsigned,
unknown-key and damaged signatures. Separate LAB regression checks retain
immutable-payload rejection.

These are host results. Record full ROM boot, user-data compatibility,
recovery, physical peripherals and other RAM/UFS variants separately. The
previous CLG43 LAB component qualification belongs to its earlier image hashes.

## Rebuild and import

After the companion source build completes, run the importer first with
`--check-only`. Select the community reference and the exact CLG43 startup lists.

```sh
python3 import-source-build.py   --kernel /absolute/path/to/build/kernel-final   --signed /absolute/path/to/build/signed   --frozen /absolute/path/to/build/frozen   --reference /absolute/path/to/modules-source/docs/build-reference-6.18.60-community.json   --source-tools /absolute/path/to/modules-source/tools   --lists /absolute/path/to/qualified-startup-lists   --destination . --check-only
```

A validated import preserves the qualified DTB/DTBO, recovery list, options
and blocklist. The community profile is accepted only when the reference,
signed-bank metadata and kernel configuration agree. Certificate/CMS, file
integrity and final ABI checks apply to both community and LAB imports.

`modules.options` enables PCIe DRV and WLAN cold boot calibration on one cnss2
line. The device tree handles DSP, memory, fingerprint, sensor, audio, camera
and peripheral startup through native init services. The OTG/FSA experiments
are separate from this candidate.
