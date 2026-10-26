"""Record retained and removed original references without inventing verification."""
import csv
import json
from pathlib import Path
from build_revised_article import REFERENCES
from revision_reference_audit import entries

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/q1_artifacts/revision_20261026'
ORIGINAL=[1,2,3,5,6,7,8,9,10,12,13,17,18,19,21,22,23,24,25,27,30,32,33,34,38,None,None,None,None,None,None]


def main():
    renumber=json.loads((OUT/'manuscript_integrity.json').read_text())['reference_renumbering']
    kept={old:(i+1,REFERENCES[i]) for i,old in enumerate(ORIGINAL) if old is not None}
    rows=[]
    for old,entry in enumerate(entries(),1):
        if old in kept:
            i,(ref,link)=kept[old]
            source=link if link.startswith('http') else 'https://doi.org/'+link
            rows.append([old,entry,'retained and normalized',renumber[str(i)],ref,source,
                'Identity and bibliographic metadata checked against publisher/arXiv/institutional or registry records; not a full-text or indexing audit'])
        else:
            rows.append([old,entry,'removed from revised argument','','','','Not needed for the revised claims; not represented as fully verified'])
    for i,old in enumerate(ORIGINAL,1):
        if old is None:
            ref,url=REFERENCES[i-1]
            rows.append(['','', 'added primary source',renumber[str(i)],ref,url,'Publisher metadata or official institutional dataset/method definition; not a full-text audit'])
    with (OUT/'reference_verification.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['original_number','original_entry','disposition','revised_number','revised_entry','source_url','verification_scope']);writer.writerows(rows)
    print('41 original references accounted for; 25 retained, 16 removed, 6 sources added')


if __name__=='__main__':main()
