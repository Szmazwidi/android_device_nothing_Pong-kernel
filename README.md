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
