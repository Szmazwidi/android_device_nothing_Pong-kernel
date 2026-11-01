# Nothing Phone (2) — prebuilt android17-6.18 kernel

Prebuilt kernel, DTB, DTBO and vendor modules for `device/nothing/Pong` with
`TARGET_PONG_KERNEL := 6.18` (the default on its `pong-6.18` branch).

The files are the tested development image set named in `source.json` (currently CLS38:
kernel from the Kleaf build of
[android_kernel_nothing_sm8475-6.18](https://github.com/Szmazwidi/android_kernel_nothing_sm8475-6.18)
and modules from
[android_kernel_nothing_sm8475-modules-6.18](https://github.com/Szmazwidi/android_kernel_nothing_sm8475-modules-6.18),
branch `pong-a17-6.18.59`). `SHA256SUMS` lists every file.

**This is the development kernel of one phone.** It keeps the laboratory guards of that
kernel: block writes are allowed only to the userdata/metadata ranges of the development
phone's UFS, and only the listed exact module payloads load. The supplied modules
are signed. The historical CLS38 Image does not itself default to signature
forcing (`module.sig_enforce=N`); the payload hash gate is a separate check.
The newer source configuration enables signature forcing and SHA-256 for fresh
builds, which require their own frozen module set/key and separate qualification.
This repository retains the previously tested Image until that replacement is
qualified. Do not flash a build with it on another device; see `README.pong.md`
of the kernel repository.

| File | Contents |
|---|---|
| `Image` | kernel (same bytes as in the stage boot image) |
| `dtb/pong.dtb` | DTB from the stage vendor_boot |
| `dtbo.img` | DTBO of the stage |
| `modules/*.ko` | all vendor_dlkm modules (the vendor_boot ones are the same files) |
| `modules.load` | vendor_dlkm load list (first stage set; the rest loads from `init.pong618.rc`) |
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

It checks all 262 payloads, the final embedded public certificate, every CMS
signature and final kernel ABI/runtime contracts before overwriting anything.
The existing qualified DTB, DTBO and module startup lists are preserved. Private
signing keys are never copied. SHA256SUMS covers the imported binary bank,
public certificate and provenance. Source scripts are tracked separately in Git.
The resulting source.json records a host-verified import, with hardware_tested
false; importing artifacts does not qualify another phone or change a bootloader.
The physical guard geometry still requires review for the target Phone (2) SKU.
