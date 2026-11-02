# Nothing Phone (2) — prebuilt android17-6.18 kernel

Prebuilt kernel, DTB, DTBO and vendor modules for `device/nothing/Pong` with
`TARGET_PONG_KERNEL := 6.18` (the default on its `pong-6.18` branch).

The current bank in `source.json` is the CLG277 cohort (2 Nov 2026): the QRTR256
6.18.60 bank plus 15 platform ports — Qualcomm DCVS (memlat/bwmon/L3/DDR-LLCC
fast path, PMU), the Gunyah apps watchdog, the msm_rng hwrng, QTI thermal
cooling/sensors over QMI, CPU hotplug and hotplug-based thermal-pause, DDR cooling
and BCL. 277 modules (193 vendor + 84 GKI), 100 of them first-stage; the kernel
is the LAB profile (`CONFIG_PONG_LAB_GUARDS=y`, kernel commit 58b289d57). These
are byte-identical to the images running on the development phone (stage 1412).
Watchdog behaviour across long suspend and thermal mitigation under real heat
are not yet qualified. The earlier QRTR256 bank passed all 262 module
ABI/signature checks and positive/negative admission tests in a diskless VM.
On the development phone it booted the native November 1 Android 17 ROM with
SELinux enforcing, forced signatures, root and full RAM. Native startup exposes
41 sensors and five internal cameras. A normal-UID Camera2 test delivered four
transient YUV frames from each public front/main camera. An Internet ping bound
to rmnet_data2 passed, and Wi-Fi reconnected after that cellular-only test.
The importer records `hardware_tested: false` because importing files performs
no phone operation; the separate runtime result covers only this development
phone. Overnight WLAN MHI wake stability remains open. See the module source
repository's `docs/build-evidence/native-qrtr256-20261102.json` for exact inputs
and limits. Earlier cohort evidence remains in Git history.

**This is the development kernel of one phone.** It retains laboratory guards
whose block-write ranges and RAM geometry are specific to that phone; another
Phone (2) may have a different layout. Do not flash this prebuilt on another
phone without reviewing and adapting those guards. The 262 supplied modules
are signed, signature enforcement is enabled, and the exact-payload gate is a
separate check. See `README.pong.md` in the kernel source repository; the guards
are compiled only with `CONFIG_PONG_LAB_GUARDS` (default off).

| File | Contents |
|---|---|
| `Image` | kernel (same bytes as in the stage boot image) |
| `dtb/pong.dtb` | DTB from the stage vendor_boot |
| `dtbo.img` | DTBO of the stage |
| `modules/*.ko` | all vendor_dlkm modules (the vendor_boot ones are the same files) |
| `modules.load` | vendor_dlkm load list (first stage set plus the CLG ports loaded by `vendor.modprobe`; the rest loads from `init.pong618.rc`) |
| `modules.list.vendor_boot`, `modules.load.vendor_boot`, `modules.load.recovery` | vendor_boot set and lists |
| `modules.options`, `modules.blocklist` | module options; vendor_boot blocklist |

Update from another tested stage:

```sh
./import-pong618.py /mnt/storage/5.15/pong618/diagnostics CLS38
```


## Import your complete source build

After the companion modules repository's two-pass build, final signatures and
module-admission VM test, use the portable importer instead of a maintainer's
numbered stage directories:

```sh
# Set these to your own completed build and module source checkout.
PONG_KERNEL_BUILD=/absolute/path/to/source-build
PONG_MODULE_SOURCE=/absolute/path/to/modules-source
python3 ./import-source-build.py \
  --kernel "$PONG_KERNEL_BUILD/kernel-final" \
  --signed "$PONG_KERNEL_BUILD/signed" --frozen "$PONG_KERNEL_BUILD/frozen" \
  --reference "$PONG_MODULE_SOURCE/docs/build-reference-6.18.60.json" \
  --source-tools "$PONG_MODULE_SOURCE/tools" --destination . --check-only
# Repeat without --check-only to update this clean prebuilt checkout.
```

For an explicit-count reference such as `docs/build-reference-6.18.60-CLG277.json`
add `--lists DIR` with the qualified `modules.load`, `modules.load.vendor_boot` and
`modules.list.vendor_boot`; the first-stage list must match the reference's
`first_stage_list` and its SHA-256. The DCVS/PMU modules must stay first-stage:
loaded later from vendor.modprobe they fail the perfmon capability check.

It checks all 262 payloads, the final embedded public certificate, every CMS
signature and final kernel ABI/runtime contracts before overwriting anything.
The existing qualified DTB, DTBO and module startup lists are preserved. Private
signing keys are never copied. SHA256SUMS covers the imported binary bank,
public certificate and provenance. Source scripts are tracked separately in Git.
The resulting source.json records a host-verified import, with hardware_tested
false; importing artifacts does not qualify another phone or change a bootloader.
The physical guard geometry still requires review for the target Phone (2) SKU.
