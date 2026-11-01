#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Verify and import a complete source-built cohort into Pong-kernel, without a phone.

Use --check-only first. The target's qualified DTB/DTBO and startup lists are
preserved. A host import is never labelled hardware-tested and never flashes.
"""
import argparse,hashlib,json,pathlib,re,shutil,struct,subprocess,tempfile

def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def run(argv):
 try:return subprocess.check_output(list(map(str,argv)),stderr=subprocess.STDOUT)
 except subprocess.CalledProcessError as e:raise RuntimeError('Command failed: '+str(argv[0])+'\n'+e.output.decode(errors='replace')[:5000])from e
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['kernel','signed','frozen','reference','source-tools','destination']:p.add_argument('--'+n,type=pathlib.Path,required=True)
 p.add_argument('--check-only',action='store_true');a=p.parse_args()
 for n in ['kernel','signed','frozen','reference','source_tools','destination']:setattr(a,n,getattr(a,n).resolve())
 bank=json.loads((a.signed/'manifest.json').read_text());frozen=json.loads((a.frozen/'manifest.json').read_text());ref=json.loads(a.reference.read_text())
 expected=set(ref['vendor'])|set(ref['gki']);assert all(re.fullmatch(r'[A-Za-z0-9_.-]+\.ko',n)for n in expected);assert len(expected)==262 and set(bank['modules'])==set(frozen['modules'])==expected
 assert bank['final_ABI_verified']and bank['signature_force_config_verified']
 assert bank['final_kernel_sha256']==sha(a.kernel/'Image');image=(a.kernel/'Image').read_bytes();assert image[56:60]==b'ARMd'
 config=(a.kernel/'kernel_aarch64_dot_config').read_text();assert 'CONFIG_MODULE_SIG_FORCE=y'in config and'CONFIG_MODULE_SIG_SHA256=y'in config
 cert=a.signed/'signing-certificate.pem';der=run(['openssl','x509','-in',cert,'-outform','DER']);assert hashlib.sha256(der).hexdigest()==bank['certificate_sha256']and der in image
 target=a.destination;assert (target/'dtb/pong.dtb').is_file()and(target/'dtbo.img').is_file()
 vb=set((target/'modules.list.vendor_boot').read_text().split());assert len(vb)==94 and vb<=expected
 for name in ['modules.load','modules.load.vendor_boot','modules.load.recovery']:
  for l in(target/name).read_text().splitlines():
   l=l.strip()
   if l and not l.startswith('#'):assert l.split()[0].removesuffix('.ko')+'.ko'in expected,(name,l)
 meta={n:sha(target/n)for n in ['dtb/pong.dtb','dtbo.img','modules.load','modules.load.vendor_boot','modules.load.recovery','modules.list.vendor_boot','modules.options','modules.blocklist']}
 with tempfile.TemporaryDirectory(prefix='pong-source-import-')as tmp:
  tmp=pathlib.Path(tmp);k=tmp/'kernel';v=tmp/'vendor';k.mkdir();v.mkdir();magic=b'~Module signature appended~\n'
  for name in ['Image','kernel_aarch64_dot_config','kernel_aarch64_Module.symvers','Module.symvers']:
   if(a.kernel/name).is_file():(k/name).symlink_to(a.kernel/name)
  for name,row in sorted(bank['modules'].items()):
   f=a.signed/name;assert sha(f)==row['sha256'];data=f.read_bytes();assert data.endswith(magic)
   n=struct.unpack('>I',data[-len(magic)-4:-len(magic)])[0];end=len(data)-len(magic)-12-n;assert end>0
   body=data[:end];signature=data[end:end+n];assert hashlib.sha256(body).hexdigest()==frozen['modules'][name]['payload_sha256']and len(body)==frozen['modules'][name]['payload_bytes']
   assert struct.pack('<Q',len(body))+hashlib.sha256(body).digest()in image, 'Final kernel lacks frozen payload entry: '+name
   (tmp/'body').write_bytes(body);(tmp/'signature').write_bytes(signature)
   run(['openssl','cms','-verify','-binary','-inform','DER','-in',tmp/'signature','-content',tmp/'body','-nointern','-certfile',cert,'-CAfile',cert,'-purpose','any','-out','/dev/null'])
   ((k if name in ref['gki']else v)/name).symlink_to(f)
  run(['python3',a.source_tools/'verify_build.py','--kernel',k,'--modules',v,'--reference',a.reference,'--report',tmp/'ABI.json'])
  checked=json.loads((tmp/'ABI.json').read_text());assert checked['selected_modules']==262
 result=dict(schema='pong-source-prebuilt-v1',status='SOURCE_BANK_CERTIFICATE_CMS_AND_FINAL_ABI_VERIFIED',kernel=dict(sha256=bank['final_kernel_sha256']),certificate_sha256=bank['certificate_sha256'],modules=262,vendor_boot_modules=94,signature_force=True,hardware_tested=False,phone_operations=0,preserved_files=meta,signed_manifest_sha256=sha(a.signed/'manifest.json'),frozen_manifest_sha256=sha(a.frozen/'manifest.json'))
 if a.check_only:print(json.dumps(result));return
 # All validation precedes the first overwrite. Retain the Git/LFS history of
 # this prebuilt checkout and refuse to mix someone else's pending edits.
 assert not run(['git','-C',target,'status','--porcelain']).strip(),'Target has uncommitted changes'
 tracked={x for x in run(['git','-C',target,'ls-files','modules/*.ko']).decode().splitlines()};assert tracked=={'modules/'+n for n in expected}
 for name in sorted(expected):shutil.copyfile(a.signed/name,target/'modules'/name)
 shutil.copyfile(a.kernel/'Image',target/'Image');shutil.copyfile(cert,target/'signing-certificate.pem')
 (target/'source.json').write_text(json.dumps(result,indent=2)+'\n')
 assert all(sha(target/n)==h for n,h in meta.items())
 # Cover the actual build inputs and metadata. Source/documentation scripts
 # are reviewed as Git source and do not belong to the binary artifact bank.
 files=[target/'Image',target/'dtb/pong.dtb',target/'dtbo.img',target/'source.json',target/'signing-certificate.pem']+[target/'modules'/n for n in sorted(expected)]+[target/n for n in meta if not n.startswith('dtb/')and n!='dtbo.img']
 files=sorted(set(files),key=lambda q:str(q.relative_to(target)))
 (target/'SHA256SUMS').write_text(''.join(sha(f)+'  '+str(f.relative_to(target))+'\n'for f in files))
 subprocess.run(['sha256sum','-c','SHA256SUMS'],cwd=target,check=True,stdout=subprocess.DEVNULL)
 print(json.dumps(dict(status='SOURCE_BANK_IMPORTED_WITH_QUALIFIED_DTB_AND_LISTS_PRESERVED',files=len(files),hardware_tested=False,phone_operations=0)))
if __name__=='__main__':main()
