#!/usr/bin/env python3
"""Import the prebuilt android17-6.18 kernel for Nothing Phone (2) from tested stage images.

Copies the kernel Image, the vendor_boot DTB, dtbo.img, every vendor_dlkm module and the
module lists of one tested image set, checks them against the stage reports and writes
SHA256SUMS. Run from this directory:

    ./import-pong618.py /mnt/storage/5.15/pong618/diagnostics CLS36

The vendor_boot image is taken from the stage the boot/vendor_dlkm report names (CLS17 for CLS36).
"""
import hashlib, json, pathlib, shutil, struct, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def vendor_boot_parts(img, tmp):
    """Unpack a v4 vendor_boot with AOSP unpack_bootimg; return (dtb, ramdisk module dir)."""
    unpack = HERE.parents[2] / 'system/tools/mkbootimg/unpack_bootimg.py'
    out = tmp / 'vb'
    subprocess.run([sys.executable, unpack, '--boot_img', img, '--out', out], check=True, capture_output=True)
    root = tmp / 'ramdisk'
    root.mkdir()
    data = (out / 'vendor_ramdisk00').read_bytes()
    if data[:4] == b'\x02\x21\x4c\x18':  # legacy lz4
        data = subprocess.run(['lz4', '-dc'], input=data, check=True, capture_output=True).stdout
    subprocess.run(['cpio', '-idm', '--quiet'], input=data, cwd=root, check=True)
    mods = [p for p in (root / 'lib/modules').iterdir() if p.is_dir()]
    assert len(mods) == 1, mods
    return out / 'dtb', mods[0]


def main():
    diag, stage = pathlib.Path(sys.argv[1]), sys.argv[2]
    images = json.loads((diag / f'stage{stage}-images/report.json').read_text())['images']
    boot = pathlib.Path(images['boot_b']['file'])
    vboot = pathlib.Path(images['vendor_boot_b']['file'])
    dtbo = pathlib.Path(images['dtbo_b']['file'])
    for key, p in [('boot_b', boot), ('vendor_boot_b', vboot), ('dtbo_b', dtbo)]:
        assert sha(p) == images[key]['sha256'], key
    dlkm = diag / f'stage{stage}-images/dlkm-readback/lib/modules'
    kernel = diag / f'stage{stage}-kernel/kernel/Image'

    # The boot image of the stage must carry exactly this Image.
    raw = boot.read_bytes()
    ksize = struct.unpack_from('<I', raw, 8)[0]
    assert raw[4096:4096 + ksize] == kernel.read_bytes(), 'boot.img kernel != stage Image'

    with tempfile.TemporaryDirectory() as t:
        dtb, ramdisk = vendor_boot_parts(vboot, pathlib.Path(t))
        for d in ['modules', 'dtb']:
            shutil.rmtree(HERE / d, ignore_errors=True)
            (HERE / d).mkdir()
        shutil.copyfile(kernel, HERE / 'Image')
        shutil.copyfile(dtb, HERE / 'dtb/pong.dtb')
        shutil.copyfile(dtbo, HERE / 'dtbo.img')
        for ko in sorted(dlkm.glob('*.ko')):
            shutil.copyfile(ko, HERE / 'modules' / ko.name)
        # First-stage modules must be the same files that vendor_dlkm ships.
        vb_mods = sorted(p.name for p in ramdisk.glob('*.ko'))
        for n in vb_mods:
            assert sha(ramdisk / n) == sha(HERE / 'modules' / n), n
        (HERE / 'modules.load').write_text((dlkm / 'modules.load').read_text())
        (HERE / 'modules.load.vendor_boot').write_text((ramdisk / 'modules.load').read_text())
        (HERE / 'modules.load.recovery').write_text((ramdisk / 'modules.load.recovery').read_text())
        (HERE / 'modules.list.vendor_boot').write_text('\n'.join(vb_mods) + '\n')
        (HERE / 'modules.options').write_text((dlkm / 'modules.options').read_text())
        (HERE / 'modules.blocklist').write_text((ramdisk / 'modules.blocklist').read_text())

    files = sorted(p for p in HERE.rglob('*') if p.is_file() and '.git' not in p.parts
                   and p.name not in {'SHA256SUMS', 'README.md', 'import-pong618.py', 'Android.bp'})
    (HERE / 'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(HERE)}\n' for p in files))
    (HERE / 'source.json').write_text(json.dumps(dict(
        stage=stage, kernel=dict(file=str(kernel), sha256=sha(HERE / 'Image')),
        boot_b=images['boot_b']['sha256'], vendor_boot_b=images['vendor_boot_b']['sha256'],
        dtbo_b=images['dtbo_b']['sha256'], vendor_dlkm_b=images['vendor_dlkm_b']['sha256'],
        modules=len(list((HERE / 'modules').glob('*.ko'))), vendor_boot_modules=len(vb_mods)), indent=2) + '\n')
    print(f'imported {stage}: {len(files)} files')


if __name__ == '__main__':
    main()
