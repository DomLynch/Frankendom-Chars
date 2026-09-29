# Inject before build/render scripts. Stage bytes before temporary files are reused.
from huggingface_hub import HfApi,CommitOperationAdd
from pathlib import Path
_DELIVERY='Domlynch/frankendom-nightborn-delivery-20260928'
_pending=[]
def _stage_upload(self,path_or_fileobj,path_in_repo,**kwargs):
 data=Path(path_or_fileobj).read_bytes() if isinstance(path_or_fileobj,(str,Path)) else path_or_fileobj
 _pending.append(CommitOperationAdd(path_in_repo=path_in_repo,path_or_fileobj=data))
HfApi.upload_file=_stage_upload
def _flush_uploads():
 if _pending:
  info=HfApi().create_commit(repo_id=_DELIVERY,repo_type='dataset',operations=list(_pending),commit_message='Persist verified Nightborn output batch')
  print('BATCH_PERSISTED',info.oid,len(_pending),flush=True);_pending.clear()
